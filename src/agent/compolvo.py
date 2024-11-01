import asyncio
import enum
import json
import logging
import os
import platform
import queue
import sys
from logging import Logger
from threading import Thread
from typing import Dict, Any, Optional

import click
import distro
import requests
import websockets
import yaml
from websockets.exceptions import ConnectionClosedError

config: "Config"
logger: Logger
config_filename: str
message_queue = queue.Queue()


class ConfigAgent:
    id: str

    def __init__(self, data: Dict[str, str]):
        self.id = data['id']

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.id
        }


class ConfigCompolvo:
    host: str
    secure: bool

    def __init__(self, data: Dict[str, str | bool]):
        self.host = data['host']
        self.secure = data["secure"]

    def to_dict(self) -> Dict[str, str | bool]:
        return {
            "host": self.host,
            "secure": self.secure
        }


class Config:
    agent: ConfigAgent
    compolvo: ConfigCompolvo
    config_file: str

    def __init__(self, data: Dict[str, Dict[str, str]], config_file: str):
        self.agent = ConfigAgent(data["agent"])
        self.compolvo = ConfigCompolvo(data["compolvo"])
        self.config_file = config_file

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent": self.agent.to_dict(),
            "compolvo": self.compolvo.to_dict()
        }


def load_config(config_file: str):
    with open(config_file) as f:
        config = yaml.safe_load(f)
    return Config(config, config_file)


def save_config(config: Config, config_file: str):
    with open(config_file, "w") as f:
        yaml.safe_dump(config.to_dict(), f)


def install_software(event: Dict) -> str | None:
    system_name, software_id, version = extract_command_data_from_event(event)
    return run_playbook(system_name, software_id, version)


def extract_command_data_from_event(event: Dict):
    msg = event["message"]
    system_name = msg["service"]
    software_id = msg["software"]
    version = msg.get("version")
    return system_name, software_id, version


def uninstall_software(event: Dict) -> str | None:
    system_name, software_id, _ = extract_command_data_from_event(event)
    return run_playbook(system_name, software_id, "uninstall")


def handle_websocket_command(command: str) -> str | None:
    data = json.loads(command)
    event = data.get("event")
    if data.get("success") == True:
        logger.debug("Received positive confirmation: %s", data)
        return
    if event is None:
        logger.warning("Received websocket message that can't be interpreted: %s", data)
        return
    if event.get("type") == "software-status-update":
        return
    recipient = event.get("recipient", {})
    assert recipient.get(
        "subscriber_type") == "agent", f"Received event for {recipient}: {event} (expected for agent)."
    recipient_id = recipient.get("id")
    assert recipient_id is None or recipient_id == config.agent.id, f"Received event for different agent: {event}"
    type = event["type"]
    msg: str | None = None
    match type:
        case "install-software":
            msg = install_software(event)
        case "uninstall-software":
            msg = uninstall_software(event)
        case other:
            logger.error("Received unsupported event of type '%s': %s", other, event)
    if msg is not None:
        logger.debug("Queueing message: %s", msg)
        message_queue.put(msg)
    return None


def generate_software_status(software_id: str, installed_version: str | None, corrupt=False,
                             installing=False, uninstalling=False):
    return json.dumps({
        "event": {
            "type": "software-status-update",
            "recipient": {
                "subscriber_type": "server",
                "id": None
            },
            "message": {
                "software_id": software_id,
                "status": {
                    "installed_version": installed_version,
                    "corrupt": corrupt,
                    "installing": installing,
                    "uninstalling": uninstalling
                }
            }
        }
    })


def run_playbook(system_name: str, software_id: str, playbook_name: str):
    playbook_url = f"http{'s' if config.compolvo.secure else ''}://{config.compolvo.host}/ansible/playbooks/{system_name}/{playbook_name}.yml"
    response = requests.get(playbook_url)
    if not response.ok:
        logger.error("Error fetching playbook from %s: %s", playbook_url, response.text)
        return generate_software_status(software_id, None, True, False, False)
    path = system_name + ".yml"
    with open(path, "w") as f:
        f.write(response.text)
    return_code = os.system(f"ansible-playbook '{path}'")
    os.remove(path)
    installed_version = playbook_name if playbook_name != 'uninstall' else None
    if return_code == 0:
        return generate_software_status(software_id, installed_version, False, False, False)
    return generate_software_status(software_id, installed_version, True, False, False)


async def subscribe(ws: websockets.WebSocketClientProtocol, event_type: str):
    subscription_data = {
        "intent": "subscribe",
        "subscriber_type": "agent",
        "event_type": event_type,
        "id": config.agent.id
    }
    await ws.send(json.dumps(subscription_data))
    response = await ws.recv()
    res = json.loads(response)
    if not res.get("success", False):
        raise Exception("Received unsuccessful message from server: " + response)


async def run_websocket(retries: Optional[int] = 5):
    uri = f"ws{'s' if config.compolvo.secure else ''}://{config.compolvo.host}/api/notify"
    logger.debug("logging in to WebSocket at %s", uri)
    while retries is None or retries > 0:
        try:
            async with websockets.connect(uri) as ws:
                login_data = {
                    "event": {
                        "type": "agent-login",
                        "recipient": {
                            "subscriber_type": "server",
                            "id": None
                        },
                        "message": {
                            "agent_id": config.agent.id
                        }
                    }
                }
                await ws.send(json.dumps(login_data))
                response = await ws.recv()
                res = json.loads(response)
                if res.get("success", False):
                    logger.info("Logged in successfully.")
                else:
                    logger.info("Error logging in: %s", response)
                _ = await ws.recv()
                await subscribe(ws, "install-software")
                await subscribe(ws, "uninstall-software")
                logger.info("Subscribed to relevant notification topics.")
                try:
                    while True:
                        data: str | bytes | None = None
                        if ws.closed:
                            raise ConnectionClosedError(ws.close_rcvd, ws.close_sent)
                        try:
                            async with asyncio.timeout(1):
                                data = await ws.recv()
                                logger.debug("received %s", data)
                        except asyncio.TimeoutError:
                            pass
                        try:
                            if data is not None:
                                Thread(target=handle_websocket_command, args=(data,)).start()
                            while message_queue.unfinished_tasks > 0:
                                msg = message_queue.get()
                                logger.debug("Sending %s", msg)
                                await ws.send(msg)
                                message_queue.task_done()
                        except (AssertionError, ConnectionClosedError) as e:
                            handle_error_for_user(e)
                            message_queue.put(data)
                except KeyboardInterrupt:
                    return
                except Exception as e:
                    handle_error_for_user(e)
        except Exception as e:
            handle_error_for_user(e)
            if retries is not None:
                retries = retries - 1
        await asyncio.sleep(1)


def handle_error_for_user(err: Exception):
    logger.error("Error occured: %s: %s", err.__class__.__name__, err)
    if logger.level == logging.DEBUG:
        logger.exception(err)

class OperatingSystem(enum.StrEnum):
    debian = "debian"
    macos = "macOS"
    windows = "windows"
    manjaro = "manjaro"


class UnsupportedOperatingSystem(Exception):
    pass


def detect_operating_system(id: str = None) -> OperatingSystem:
    dist = distro.id() if id is None else id
    match dist:
        case "debian":
            return OperatingSystem.debian
        case "darwin" | "macOS":
            return OperatingSystem.macos
        case "windows":
            return OperatingSystem.windows
        case "manjaro":
            return OperatingSystem.manjaro
        case "":  # distro seemingly can't detect windows in my VM
            if platform.system() == "Windows":
                return OperatingSystem.windows

    raise UnsupportedOperatingSystem(
        f"Unsupported operating system detected ({dist}). Please add a agent with a supported one.")


@click.command("init")
@click.option("--compolvo-host", default="localhost:8080", help="hostname where Compolvo is hosted")
@click.option("--agent-id", "--id", prompt="What's your agent's ID?",
              help="ID of the agent to connect as")
@click.option("--overwrite", "-f", is_flag=True, default=False,
              help="Overwrite existing config file")
@click.option("--insecure", is_flag=True, default=False, help="Insecure websocket connection")
def init(compolvo_host: str, agent_id: str, overwrite: bool, insecure: bool):
    try:
        operating_system = detect_operating_system()
        logger.info("Initializing compolvo...")
        config = Config({
            "agent": {
                "id": agent_id
            },
            "compolvo": {
                "host": compolvo_host,
                "secure": not insecure
            }
        }, config_filename)
        if not overwrite and os.path.isfile(config.config_file):
            overwrite = click.confirm("Overwrite existing config?", default=True)
            if not overwrite:
                return
        logger.info(f"Writing config into {config_filename}")
        save_config(config, config_filename)
        api_base = f"http{'s' if config.compolvo.secure else ''}://{config.compolvo.host}"
        agent_endpoint = f"{api_base}/api/agent/name?id={agent_id}"
        response = requests.get(agent_endpoint)
        if not response.ok:
            logger.error("Error getting current agent status: %s", response.text)
            exit(1)
        json = response.json()
        name = json.get("name")
        existing_os = detect_operating_system(json.get("operating_system"))
        if existing_os != operating_system:
            logger.warning(
                "Agent configured previously on different operating system (was %s, now %s)",
                existing_os, operating_system)
        error = False
        payload = {"id": agent_id, "operating_system": operating_system.value}
        if name is None:
            new_name = click.prompt("Enter new name", type=click.STRING, default="")
            if new_name != "":
                payload["name"] = new_name
        response = requests.patch(f"{api_base}/api/agent/init?id={agent_id}", json=payload)
        if not response.ok:
            logger.error("Error initializing agent: %s.", response.text)
            error = True
        try:
            name = response.json().get("name")
        except requests.JSONDecodeError:
            logger.error("Received unexpected response from server: %s", response.text)
            return
        logger.info(
            f"Initialized {'successfully' if not error else 'with errors'} as agent '{name}'.")
    except UnsupportedOperatingSystem as e:
        logger.error(e)


@click.command("run")
@click.option("--infinite-retries", "-r", is_flag=True, default=False,
              help="Infinite retries when connection fails (default 5)")
def run(infinite_retries: bool):
    args = {}
    if infinite_retries:
        args["retries"] = None
    asyncio.run(run_websocket(**args))


@click.group()
@click.option("--config-file", "-c", default="config.yml", help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose mode")
def cli(config_file: str, verbose: bool):
    global config
    global logger
    global config_filename
    config_filename = config_file

    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=log_level)
    logger = logging.getLogger("agent")
    logger.setLevel(log_level)
    try:
        config = load_config(config_file)
        logger.debug("Using config: %s", config.to_dict())
    except FileNotFoundError:
        if "init" not in sys.argv:
            logger.error(
                f"Config file {config_file} not found. Please run 'compolvo init --help' for more information.")


commands = [init, run]
for command in commands:
    cli.add_command(command)

if __name__ == "__main__":
    cli()
