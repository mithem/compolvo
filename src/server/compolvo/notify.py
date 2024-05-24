import asyncio
import datetime
import enum
import json
import uuid
from queue import Queue
from typing import Callable, Dict, List, Coroutine
from uuid import UUID

import websockets
from compolvo.models import Agent, AgentSoftware
from sanic.log import logger
from websockets import ConnectionClosed, ConnectionClosedOK, ConnectionClosedError


class EventType(enum.StrEnum):
    RELOAD = "reload"
    INSTALL_SOFTWARE = "install-software"
    UNINSTALL_SOFTWARE = "uninstall-software"
    AGENT_SOFTWARE_STATUS_UPDATE = "software-status-update"
    AGENT_LOGIN = "agent-login"
    WS_DISCONNECT = "ws-disconnect"


class SubscriberType(enum.StrEnum):
    USER = "user"
    AGENT = "agent"
    SERVER = "server"


class Subscriber:
    type: SubscriberType
    event_type: EventType
    id: str | None

    def __init__(self, type: SubscriberType, event_type: EventType, id: str | None = None) -> None:
        self.type = type
        self.event_type = event_type
        self.id = id

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "event_type": self.event_type.value,
            "id": self.id
        }

    def __repr__(self):
        return str(self.to_dict())

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __hash__(self):
        return hash((self.type, self.event_type, self.id))


class Recipient:
    subscriber_type: SubscriberType
    id: str | None

    def __init__(self, subscriber_type: SubscriberType, id: str | None = None) -> None:
        self.subscriber_type = subscriber_type
        self.id = id

    def to_dict(self):
        return {
            "subscriber_type": self.subscriber_type,
            "id": self.id
        }

    def __repr__(self):
        return str(self.to_dict())


class Event:
    type: EventType
    recipient: Recipient | None
    message: Dict
    ephemeral: bool

    def __init__(self, type: EventType, recipient: Recipient | None, message: Dict,
                 ephemeral: bool = True):
        self.type = type
        self.recipient = recipient
        self.message = message
        self.ephemeral = ephemeral

    def __repr__(self):
        return str(self.to_dict())

    def __hash__(self):
        return hash((self.type, self.recipient, self.message, self.ephemeral))

    def to_dict(self):
        return {
            "type": self.type.value,
            "recipient": self.recipient.to_dict() if self.recipient is not None else None,
            "message": self.message,
            "ephemeral": self.ephemeral
        }


class Subscription:
    subscriber: Subscriber
    id: UUID

    def __init__(self, subscriber: Subscriber, id: UUID):
        self.subscriber = subscriber
        self.id = id

    def __repr__(self):
        return str(self.to_dict())

    def __hash__(self):
        return hash((self.subscriber, self.id))

    def __eq__(self, other):
        return hash(self) == hash(other)

    def to_dict(self):
        return {
            "subscriber": self.subscriber.to_dict(),
            "id": str(self.id)
        }


EventHandler = Callable[[Event], Coroutine[None, None, bool | None]]
SubscriptionCallback = Callable[[Subscription], Coroutine[None, None, None]]

_connection_handlers: Dict[Subscription, EventHandler] = {}
_event_queue: Queue[Event] = Queue()


def get_subscribers_for_event(event: Event) -> List[Subscriber]:
    subscribers = set(map(lambda sub: sub.subscriber, _connection_handlers.keys()))

    def subscriber_is_included(subscriber: Subscriber) -> bool:
        if subscriber.event_type != event.type or (
                event.recipient is not None and subscriber.type != event.recipient.subscriber_type):
            return False
        return event.recipient is None or subscriber.id == event.recipient.id or event.recipient.id is None or subscriber.id is None

    return list(filter(subscriber_is_included, subscribers))


def queue(event: Event):
    _event_queue.put(event)


async def _notify(event: Event) -> bool:
    subscribers = get_subscribers_for_event(event)
    if len(subscribers) == 0:
        logger.debug("No subscribers, unsuccessful delivery.")
        return False
    success = True
    # collect items first as dict might change during iteration
    # that isn't fatal however, as newly unregistered handlers need to deal with potentially being invoked after that
    connection_handlers = set(_connection_handlers.items())
    for subscription, handler in connection_handlers:
        if subscription.subscriber in subscribers:
            result = await handler(event)
            if result == False:  # A None return value is not a failure
                success = False
    return success


def subscribe(type: SubscriberType, event_type: EventType, handler: EventHandler,
              id: str | None = None) -> Subscription:
    # TODO: Checks that ensure users can only subscribe to the right events
    # (e.g. reload & login events only for users with restricted id)
    subscriber = Subscriber(type, event_type, id)
    subscription = Subscription(subscriber, uuid.uuid4())
    _connection_handlers[subscription] = handler
    return subscription


def unsubscribe(subscription_id: UUID):
    subscriptions = list(filter(lambda sub: sub.id == subscription_id, _connection_handlers.keys()))
    for subscription in subscriptions:
        _connection_handlers.pop(subscription)


async def handle_incoming_message(msg: str, event_handler: EventHandler,
                                  subscription_callback: SubscriptionCallback) -> str:
    try:
        raw_data = json.loads(msg)
        intent = str(raw_data.get("intent")).lower()
        if intent == "subscribe":
            return await handle_incoming_subscribe_intent(raw_data, event_handler,
                                                          subscription_callback)
        elif intent == "unsubscribe":
            return await handle_incoming_unsubscribe_intent(raw_data)
        event_data = raw_data.get("event")
        if event_data is not None:
            res = await handle_incoming_event(event_data, event_handler)
            return res if res is not None else json.dumps({"success": True})
        return json.dumps({"success": False, "error": "Instructions unclear."})
    except Exception as e:
        logger.exception(e)
        return json.dumps({"success": False, "error": str(e)})


async def handle_incoming_subscribe_intent(data: dict, event_handler: EventHandler,
                                           subscription_callback: SubscriptionCallback) -> str:
    assert isinstance(data, dict)
    sub_type = SubscriberType(str(data.get("subscriber_type")).lower())
    event_type = EventType(str(data.get("event_type")).lower())
    id = data.get("id")
    sub = subscribe(sub_type, event_type, event_handler, id)
    await subscription_callback(sub)
    return json.dumps({"success": True, "subscription": sub.to_dict()})


async def handle_incoming_unsubscribe_intent(data: dict):
    try:
        unsubscribe(UUID(data["sub_id"]))
        res = {"success": True}
    except KeyError as e:
        print(e)
        res = {"success": False, "error": "Expected 'subscription_id' parameter."}
    return json.dumps(res)


async def handle_incoming_event(data: dict, event_handler: EventHandler):
    type = EventType(data["type"])
    rec = data.get("recipient")
    if rec is not None:
        rec = Recipient(rec["subscriber_type"], rec.get("id"))
    message = data["message"]
    ephemeral = data.get("ephemeral", True)
    event = Event(type, rec, message, ephemeral)
    try:
        await event_handler(event)
    except Exception as e:
        logger.exception(e)
        return json.dumps({"success": False, "error": str(e)})
    queue(event)
    return json.dumps({"success": True, "event": event.to_dict()})


async def handle_agent_login_event(event: Event,
                                   ws: websockets.WebSocketServerProtocol) -> Agent | None:
    close_code: int | None = None
    agent_id = event.message["agent_id"]
    agent: Agent | None = await Agent.get_or_none(id=agent_id)
    if agent is None:
        error = f"Agent '{agent_id}' not found"
        close_code = 4004
    elif agent.connected:
        error = "Agent is already connected."
        close_code = 4003
    else:
        agent.last_connection_start = datetime.datetime.now()
        agent.connected = True
        agent.connection_interrupted = False
        agent.connection_from_ip_address = ws.request_headers.get(
            "x-forwarded-for", ws.remote_address[0] if isinstance(ws.remote_address, tuple)
                                                       and len(ws.remote_address) > 0
            else str(ws.remote_address))
        await agent.save()
        await ws.send(json.dumps({"success": True}))
        return agent
    if close_code is not None:
        await ws.close(close_code, error)


async def handle_agent_software_status_update_event(event: Event, agent: Agent | None):
    assert agent, "You need to log in first."
    software_id = event.message["software_id"]
    status: Dict = event.message["status"]
    assert isinstance(status, dict)
    software = await AgentSoftware.get_or_none(id=software_id)
    if software is None:
        raise ValueError(f"Software '{software_id}' not found.")
    assert (await software.agent).id == agent.id, "This software isn't installed on this agent."
    was_uninstalling = software.uninstalling
    valid_fields = {"corrupt", "installed_version", "installing", "uninstalling"}
    if set(status.keys()).issubset(valid_fields):
        for key, value in status.items():
            setattr(software, key, value)
        await software.save()
        # Perform delete check after update as not all fields required for the check need to be sent in the event
        if software.installed_version is None and software.uninstalling == False and was_uninstalling and not software.installing and not software.corrupt:
            recipient = Recipient(SubscriberType.SERVER)
            event = Event(EventType.AGENT_SOFTWARE_STATUS_UPDATE, recipient,
                          {"software_id": software_id})
            event = await get_user_reload_event(event)
            if event is not None:
                queue(event)
            await software.delete()
    else:
        fields_str = ", ".join(map(lambda field: "'" + field + "'", valid_fields))
        raise ValueError(f"You can only alter the status of the fields {fields_str}")


async def handle_agent_disconnect(agent: Agent, error: ConnectionClosed):
    agent.connected = False
    agent.last_connection_end = datetime.datetime.now()
    if isinstance(error, ConnectionClosedError):
        agent.connection_interrupted = True
    await agent.save()
    recipient = Recipient(SubscriberType.SERVER)
    event = Event(EventType.WS_DISCONNECT, recipient, {"agent_id": str(agent.id)})
    await _notify(event)


async def websocket_handler(ws: websockets.WebSocketServerProtocol):
    async def event_handler(event: Event):
        nonlocal agent
        match event.type:
            case EventType.AGENT_LOGIN:
                agent = await handle_agent_login_event(event, ws)
            case EventType.AGENT_SOFTWARE_STATUS_UPDATE:
                await handle_agent_software_status_update_event(event, agent)
        await ws.send(json.dumps({"event": event.to_dict()}))

    async def subscription_callback(subscription: Subscription):
        nonlocal subs
        subs.append(subscription.id)

    subs: List[UUID] = []
    agent: Agent | None = None
    try:
        while True:
            if ws.closed:
                if ws.close_code != 1000:
                    raise ConnectionClosedError(ws.close_rcvd, ws.close_sent)
                raise ConnectionClosedOK(ws.close_rcvd, ws.close_sent)
            msg = await ws.recv()
            res = await handle_incoming_message(msg, event_handler, subscription_callback)
            await ws.send(res)
    except (ConnectionClosedOK, ConnectionClosedError) as error:
        # Unsubscribe to prevent memory leak
        for id in subs:
            unsubscribe(id)
        if agent is not None:
            await handle_agent_disconnect(agent, error)


async def process_queue():
    logger.debug("Processing queue: %s unfinished", _event_queue.unfinished_tasks)
    failed_notifications = []
    while not _event_queue.empty():
        event = _event_queue.get(block=False)
        try:
            success = await _notify(event)
        except ConnectionClosed:
            success = False
        if not success and not event.ephemeral:
            failed_notifications.append(event)
        _event_queue.task_done()
    for event in failed_notifications:
        _event_queue.put(event)


async def run_websocket_server():
    agents = await Agent.filter(connected=True).all()
    for agent in agents:
        agent.connected = False
        await agent.save()
    async with websockets.serve(websocket_handler, "0.0.0.0", 8001):
        logger.info("Started event server")
        await asyncio.Future()


async def run_queue_worker():
    logger.info("Running notify queue worker")
    while True:
        await process_queue()
        await asyncio.sleep(1)


async def get_user_reload_event(event: Event):
    agent_id: str | UUID | None = None
    match event.type:
        case EventType.AGENT_LOGIN | EventType.WS_DISCONNECT:
            agent_id = event.message["agent_id"]
        case EventType.AGENT_SOFTWARE_STATUS_UPDATE:
            software_id = event.message["software_id"]
            software = await AgentSoftware.get_or_none(id=software_id)
            agent_id = (await software.agent).id if software is not None else None
    if agent_id is None:
        return
    agent: Agent | None = await Agent.get_or_none(id=agent_id)
    if agent is None:
        return
    user_id = str((await agent.user).id)
    recipient = Recipient(SubscriberType.USER, user_id)
    return Event(EventType.RELOAD, recipient, {"path": "/home/agent/software"})


async def run_event_worker():
    async def handler(event: Event):
        event = await get_user_reload_event(event)
        if event is not None:
            await _notify(event)

    logger.info("Running event worker")
    subscribe(SubscriberType.SERVER, EventType.AGENT_LOGIN, handler)
    subscribe(SubscriberType.SERVER, EventType.WS_DISCONNECT, handler)
    subscribe(SubscriberType.SERVER, EventType.AGENT_SOFTWARE_STATUS_UPDATE, handler)
