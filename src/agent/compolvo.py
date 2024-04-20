import asyncio
import logging
import os
import sys
from logging import Logger
from typing import Dict, Any

import click
import requests
import websockets
import yaml

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


async def run_websocket():
    uri = f"ws{'s' if config.compolvo.secure else ''}://{config.compolvo.host}/api/agent/ws"
    logger.debug("logging in to WebSocket at %s", uri)
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
                logger.info("received %s", data)
                await ws.send(data)
        except Exception as e:
            logger.exception(e)


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
def run():
    asyncio.run(run_websocket())


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
