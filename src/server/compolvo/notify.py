import asyncio
import enum
import json
from typing import Callable, Dict, List, Coroutine

import websockets
from sanic.log import logger
from websockets.frames import CloseCode


class EventType(enum.StrEnum):
    RELOAD = "reload"


class SubscriberType(enum.StrEnum):
    USER = "user"


class Subscriber:
    type: SubscriberType
    event_type: EventType
    id: str | None

    def __init__(self, type: SubscriberType, event_type: EventType, id: str | None = None) -> None:
        self.type = type
        self.event_type = event_type
        self.id = id

    def __hash__(self) -> int:
        return hash((self.type, self.event_type, self.id))

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "event_type": self.event_type.value,
            "id": self.id
        }


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


class Event:
    type: EventType
    recipient: Recipient | None
    message: str
    ephemeral: bool

    def __init__(self, type: EventType, recipient: Recipient | None, message: str,
                 ephemeral: bool = True):
        self.type = type
        self.recipient = recipient
        self.message = message
        self.ephemeral = ephemeral

    def to_dict(self):
        return {
            "type": self.type.value,
            "recipient": self.recipient.to_dict(),
            "message": self.message,
            "ephemeral": self.ephemeral
        }


EventHandler = Callable[[Event], Coroutine[None, None, None]]
_connection_handlers: Dict[Subscriber, EventHandler] = {}


def get_subscribers_for_event(event: Event) -> List[Subscriber]:
    subscribers = set(_connection_handlers.keys())

    def subscriber_is_included(subscriber: Subscriber) -> bool:
        if subscriber.event_type != event.type or subscriber.type != event.recipient.subscriber_type:
            return False
        return subscriber.id == event.recipient.id or event.recipient.id is None

    return list(filter(subscriber_is_included, subscribers))


async def notify(event: Event):
    subscribers = get_subscribers_for_event(event)
    for subscriber in subscribers:
        handler = _connection_handlers.get(subscriber)
        if handler is None:
            return
        await handler(event)


def subscribe(type: SubscriberType, event_type: EventType, handler: EventHandler,
              id: str | None = None):
    subscriber = Subscriber(type, event_type, id)
    _connection_handlers[subscriber] = handler


async def websocket_handler(ws: websockets.WebSocketServerProtocol):
    async def emit_event(event: Event):
        await ws.send(json.dumps(
            {
                "event": event.to_dict()
            }
        ))

    try:
        msg = await ws.recv()
        data = json.loads(msg)
        assert isinstance(data, dict)
        intent = str(data.get("intent")).lower()
        assert intent == "subscribe"
        sub_type = SubscriberType(str(data.get("subscriber_type")).lower())
        event_type = EventType(str(data.get("event_type")).lower())
        id = data.get("id")
        subscribe(sub_type, event_type, emit_event, id)
        await ws.send(json.dumps({"success": True}))
    except (json.JSONDecodeError, AssertionError):
        return await ws.close(CloseCode.INVALID_DATA, "Invalid JSON received.")
    except Exception as e:
        return await ws.close(CloseCode.INTERNAL_ERROR, str(e))
    while True:
        await ws.recv()


async def run_websocket_server():
    async with websockets.serve(websocket_handler, "0.0.0.0", 8002):
        logger.info("Started event server")
        await asyncio.Future()
