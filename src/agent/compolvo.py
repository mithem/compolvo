import asyncio
import logging
import os
import re
import sys
from logging import Logger
from typing import Dict, Any, Optional

import click
import requests
import websockets
import yaml
from ansible import context
from ansible.executor.playbook_executor import PlaybookExecutor
from ansible.inventory.manager import InventoryManager
from ansible.module_utils.common.collections import ImmutableDict
from ansible.parsing.dataloader import DataLoader
from ansible.vars.manager import VariableManager

config: "Config"
logger: Logger
config_filename: str


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


def handle_websocket_command(command: str) -> str | None:
    install_pattern = r"^install (?P<system_name>.+) (?P<software_id>[\w\d_-]{36}) v(?P<version>.+)$"
    install_match = re.match(install_pattern, command)

    uninstall_pattern = r"^uninstall (?P<system_name>.+) (?P<software_id>[\w\d_-]{36})$"

    if install_match:
        system_name = install_match.group("system_name")
        software_id = install_match.group("software_id")
        version = install_match.group("version")
        return run_playbook(system_name, software_id, version)
    else:
        uninstall_match = re.match(uninstall_pattern, command)
        if uninstall_match:
            system_name = uninstall_match.group("system_name")
            software_id = uninstall_match.group("software_id")
            return run_playbook(system_name, software_id, "uninstall")
        else:
            logger.error("Got websocket message that can't be interpreted: %s", command)
    return None


def run_playbook(system_name: str, software_id: str, playbook_name: str):
    playbook_url = f"http{'s' if config.compolvo.secure else ''}://{config.compolvo.host}/ansible/playbooks/{system_name}/{playbook_name}.yml"
    response = requests.get(playbook_url)
    if not response.ok:
        logger.error("Error fetching playbook from %s: %s", playbook_url, response.text)
        return None
    with open(system_name + ".yml", "w") as f:
        f.write(response.text)
    context.CLIARGS = ImmutableDict(
        connection='smart',
        become=None,
        become_method=None,
        become_user=None,
        check=False,
        diff=False,
        verbosity=0,
        syntax=None,
        start_at_task=None
    )
    loader = DataLoader()
    inventory = InventoryManager(loader=loader)
    inventory.add_host("localhost")
    var_manager = VariableManager(loader=loader, inventory=inventory)
    var_manager.set_host_variable("localhost", "ansible_python_interpreter",
                                  "./venv/bin/python3")
    playbook_executor = PlaybookExecutor(
        inventory=inventory,
        variable_manager=var_manager,
        playbooks=[f"{system_name}.yml"],
        loader=loader,
        passwords={}
    )
    data = playbook_executor.run()
    os.remove(system_name + ".yml")
    installed_version = playbook_name if playbook_name != 'uninstall' else None
    if data == 0:
        return f"software status {software_id} installed_version={installed_version};corrupt=false;installing=false;uninstalling=false"
    return f"software status {software_id} installed_version={installed_version};corrupt=true;installing=false;uninstalling=false"


async def run_websocket(retries: Optional[int] = 5):
    uri = f"ws{'s' if config.compolvo.secure else ''}://{config.compolvo.host}/api/agent/ws"
    logger.debug("logging in to WebSocket at %s", uri)
    retry = False
    try:
        async with websockets.connect(uri) as ws:
            login_msg = f"login agent {config.agent.id}"
            await ws.send(login_msg)
            response = await ws.recv()
            if response == "login successful":
                logger.info("Logged in successfully.")
            else:
                logger.info("Error logger in: %s", response)
            try:
                while True:
                    data = await ws.recv()
                    logger.debug("received %s", data)
                    data = handle_websocket_command(data)
                    if data is not None:
                        logger.debug("Sending %s", data)
                        await ws.send(data)
            except KeyboardInterrupt:
                return
            except Exception as e:
                logger.error(e)
                retry = True
    except Exception as e:
        logger.error(e)
        retry = True
    if retry and (retries is None or retries > 0):
        await asyncio.sleep(1)
        return await run_websocket(None if retries is None else retries - 1)



@click.command("init")
@click.option("--compolvo-host", default="localhost:8080", help="hostname where Compolvo is hosted")
@click.option("--agent-id", "--id", prompt="What's your agent's ID?",
              help="ID of the agent to connect as")
@click.option("--overwrite", "-f", is_flag=True, default=False,
              help="Overwrite existing config file")
@click.option("--insecure", is_flag=True, default=False, help="Insecure websocket connection")
def init(compolvo_host: str, agent_id: str, overwrite: bool, insecure: bool):
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
    agent_endpoint = f"http{'s' if config.compolvo.secure else ''}://{config.compolvo.host}/api/agent/name?id={agent_id}"
    response = requests.get(agent_endpoint)
    if not response.ok:
        logger.error("Error getting current agent status: %s", response.text)
        return
    name = response.json().get("name")
    error = False
    if name is None:
        new_name = click.prompt("Enter new name", type=click.STRING, default="")
        if new_name != "":
            response = requests.patch(agent_endpoint, json={"id": agent_id, "name": new_name})
            if not response.ok:
                logger.error("Error updating agent's name: %s.", response.text)
                error = True
            name = response.json().get("name")
    logger.info(f"Initialized {'successfully' if not error else 'with errors'} as agent '{name}'.")


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
