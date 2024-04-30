import asyncio
import datetime
import queue
import re
from queue import Queue
from typing import Dict

import websockets
from compolvo.models import AgentSoftware, Agent
from sanic.log import logger
from tortoise import BaseDBAsyncClient
from websockets import ConnectionClosedError, ConnectionClosedOK

con: BaseDBAsyncClient

# Queue for messages pending to be sent to respective agents
websocket_message_queue: Dict[str, Queue[str]] = dict()
# Queue for handling messages sent by agents (as that might require expensive database calls)
# Format: (agent_id: str, message: str)
websocket_handler_queue: Queue[(str, str)] = Queue()


async def handle_websocket_msg(agent_id: str, message: str) -> str | None:
    logger.debug("Handling websocket message for %s: %s", agent_id, message)
    status_pattern = r"(?P<status_key>[\w\d_-]+)=(?P<status_value>[\w\d\    ._-]+)"
    software_status_pattern = r"software status (?P<software_id>[\w\d-]{36}) (?P<status>[\w\d_\.=;-]+)"
    software_status_match = re.match(software_status_pattern, message)
    if software_status_match is not None:
        software_id = software_status_match.group("software_id")
        status = software_status_match.group("status")
        stati = status.split(";")
        status_data = {}
        for status_entry in stati:
            match = re.match(status_pattern, status_entry)
            if match is not None:
                status_data[match.group("status_key")] = match.group("status_value")
        software = await AgentSoftware.get_or_none(id=software_id)
        was_uninstalling = software.uninstalling
        if set(status_data.keys()).issubset(
                {"corrupt", "installed_version", "installing", "uninstalling"}):
            for key, value in status_data.items():
                if value in ["true", "false"]:
                    value = value == "true"
                elif value in ["null", "None"]:
                    value = None
                setattr(software, key, value)
            await software.save()
        if software.installed_version is None and software.uninstalling == False and was_uninstalling and not software.installing and not software.corrupt:
            await software.delete()
    return None


async def websocket_handler(ws: websockets.WebSocketServerProtocol):
    login_msg = await ws.recv()
    match = re.match(r"^login agent (?P<id>[\w-]{36})$", login_msg)
    if match is None:
        return await ws.close(4000, "Invalid login message.")
    agent_id = match.group("id")
    agent = await Agent.get_or_none(id=agent_id)
    if agent is None:
        return await ws.close(4004, "Agent not found.")
    if agent.connected:
        return await ws.close(4003, "Agent is already connected.")
    agent.last_connection_start = datetime.datetime.now()
    agent.connected = True
    agent.connection_interrupted = False
    agent.connection_from_ip_address = str(ws.remote_address)
    await agent.save()
    await ws.send("login successful")
    logger.debug("Agent logged in successfully: %s", agent_id)

    async def message_emitter(queue: Queue):
        if queue is not None:
            while not queue.empty():
                msg = queue.get()
                await ws.send(msg)

    async def message_consumer():
        try:
            async with asyncio.timeout(1):
                msg = await ws.recv()
                websocket_handler_queue.put((agent_id, msg))
        except TimeoutError:
            pass

    try:
        while True:
            queue = websocket_message_queue.get(agent_id)
            if ws.closed:
                if ws.close_code != 1000:
                    raise ConnectionClosedError(ws.close_rcvd, ws.close_sent)
                raise ConnectionClosedOK(ws.close_rcvd, ws.close_sent)
            await asyncio.gather(message_emitter(queue), message_consumer())
    except ConnectionClosedOK:
        logger.debug("Connection to agent %s closed ok", agent_id)
    except ConnectionClosedError:
        logger.warning("Connection to agent %s closed unexpectedly", agent_id)
        agent.connection_interrupted = True
    finally:
        agent.last_connection_end = datetime.datetime.now()
        agent.connected = False
        await agent.save()


async def run_websocket_server(app):
    logger.info("Preparing agents' connected attributes...")
    agents = await Agent.filter(connected=True).all()
    for agent in agents:
        agent.connected = False
        await agent.save()
    async with websockets.serve(websocket_handler, "0.0.0.0", 8001):
        logger.info("Started websocket server")
        await asyncio.Future()


async def run_websocket_handler_queue_worker():
    logger.info("Running worker handling websocket message queue...")
    while True:
        try:
            agent_id, msg = websocket_handler_queue.get(block=False)
            await handle_websocket_msg(agent_id, msg)
        except queue.Empty:
            await asyncio.sleep(1)


def queue_websocket_msg(agent_id: str, message: str):
    assert type(
        agent_id) == str, "agent id isn't of type str. Don't search further why messages don't get delivered"
    global websocket_message_queue
    queue = websocket_message_queue.get(agent_id)
    if queue is None:
        queue = Queue()
    queue.put(message)
    websocket_message_queue[agent_id] = queue
    logger.debug(f"Queued message for {agent_id}: {message}")
