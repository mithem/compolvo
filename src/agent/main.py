import asyncio
import logging
from typing import Dict

import argparse
import websockets
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent")


class ConfigAgent:
    id: str

    def __init__(self, data: Dict[str, str]):
        self.id = data['id']


class ConfigCompolvo:
    host: str

    def __init__(self, data: Dict[str, str]):
        self.host = data['host']


class Config:
    agent: ConfigAgent
    compolvo: ConfigCompolvo

    def __init__(self, data: Dict[str, Dict[str, str]]):
        self.agent = ConfigAgent(data["agent"])
        self.compolvo = ConfigCompolvo(data["compolvo"])


def load_config(config: Dict):
    return Config(config)


async def run_websocket(config: Config):
    uri = config.compolvo.host + "/api/agent/ws"
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
                await ws.send(data)
        except Exception as e:
            logger.exception(e)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", "-c", type=str, help="Path to config file", required=True)
    args = parser.parse_args()
    with open(args.config) as f:
        config = yaml.safe_load(f)
    config = load_config(config)
    logger.debug("Using config: %s", config)
    asyncio.run(run_websocket(config))


if __name__ == "__main__":
    main()
