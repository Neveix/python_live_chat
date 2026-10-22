import asyncio
from datetime import datetime
from enum import IntEnum, StrEnum
import time
import traceback
from typing import Literal

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ValidationError
import websockets

from src.utils.message_logger import MessageLogger

from ... import metrics

from ...chat_service.core.exceptions import RepoError, RoomNotFoundError
from ...chat_service.core.models import Message, RoomJoinResult, UserMessage
from ..dependencies import get_chat_service, get_message_logger
from ...chat_service.core.interfaces import ChatService


router = APIRouter(prefix="")


class IngoingMessage(BaseModel):
    text: str


class OutgoingMessage(BaseModel):
    kind: Literal["message"] = "message"
    type: str  # "user" или "system"
    sender: str | None = None
    text: str
    timestamp: datetime


def make_outgoing_message_from_message(msg: Message) -> OutgoingMessage:
    sender = None
    if isinstance(msg, UserMessage):
        sender = msg.sender

    return OutgoingMessage(
        type=msg.type,
        sender=sender,
        text=msg.text,
        timestamp=msg.timestamp,
    )


class HistoryBatch(BaseModel):
    kind: Literal["history"] = "history"
    messages: list[OutgoingMessage]


class ErrorType(StrEnum):
    JoinRoomError = "JoinRoomError"
    IngoingMessageError = "IngoingMessageError"


class ErrorMessage(BaseModel):
    kind: Literal["error"] = "error"
    error_type: ErrorType
    detail: str


class WSCloseCode(IntEnum):
    ALREADY_IN_ROOM = 4000
    ROOM_NOT_FOUND = 4001
    INTERNAL_SERVER_ERROR = 1011


async def _join_room(
    chat_service: ChatService,
    room_id: int,
    username: str,
    websocket: WebSocket,
):
    try:
        join_result = await chat_service.join_room.use(room_id, username)

    except RoomNotFoundError:
        await websocket.send_text(
            ErrorMessage(
                error_type=ErrorType.JoinRoomError,
                detail="Room not found",
            ).model_dump_json()
        )
        await websocket.close(code=WSCloseCode.ROOM_NOT_FOUND)
        return

    except RepoError:
        await websocket.send_text(
            ErrorMessage(
                error_type=ErrorType.JoinRoomError,
                detail="Internal error",
            ).model_dump_json()
        )
        await websocket.close(code=WSCloseCode.INTERNAL_SERVER_ERROR)
        return

    if not join_result.success:
        detail = join_result.detail or "The user is already in the room"
        await websocket.send_text(
            ErrorMessage(
                error_type=ErrorType.JoinRoomError,
                detail=detail,
            ).model_dump_json()
        )
        await websocket.close(code=WSCloseCode.ALREADY_IN_ROOM)
        return

    return join_result


async def _send_history(websocket: WebSocket, join_result: RoomJoinResult):
    await websocket.send_text(
        HistoryBatch(
            messages=[
                make_outgoing_message_from_message(msg)
                for msg in join_result.recent_messages or []
            ]
        ).model_dump_json()
    )


async def _send_new_messages_task(
    websocket: WebSocket,
    chat_service: ChatService,
    room_id: int,
    username: str,
):
    message_generator = chat_service.listen_new_messages.use(
        room_id=room_id, username=username
    )

    async def send_messages():
        timeout = 2.0
        async for msg in message_generator:
            start = time.monotonic()
            try:
                await asyncio.wait_for(
                    websocket.send_text(
                        make_outgoing_message_from_message(msg).model_dump_json()
                    ),
                    timeout = timeout,
                )
                metrics.MSG_SENT.inc()
            except asyncio.TimeoutError:
                print(f"message sending aborted after {timeout} seconds of waiting")
            finally:
                metrics.SEND_LATENCY.observe(time.monotonic() - start)

    return asyncio.create_task(send_messages())


async def _receive_new_messages(
    websocket: WebSocket,
    chat_service: ChatService,
    room_id: int,
    username: str,
    send_task: asyncio.Task[None],
    message_logger: MessageLogger,
):
    try:
        while True:
            message_data = await websocket.receive_text()
            recv_monotonic_ns = time.monotonic_ns()
            metrics.MSG_RECEIVED.inc()
            try:
                message = IngoingMessage.model_validate_json(message_data)

            except ValidationError as e:
                await websocket.send_text(
                    ErrorMessage(
                        error_type=ErrorType.IngoingMessageError,
                        detail=f"Validation Error: {e!s}",
                    ).model_dump_json()
                )
                continue

            message_logger.srv_recv(message.text, recv_monotonic_ns)

            try:
                await chat_service.send_message.use(
                    room_id=room_id, username=username, text=message.text
                )

            except RepoError as e:
                await websocket.send_text(
                    ErrorMessage(
                        error_type=ErrorType.IngoingMessageError,
                        detail=f"Internal Server Error",
                    ).model_dump_json()
                )
                continue

    except WebSocketDisconnect:
        pass

    except Exception:
        raise

    finally:
        send_task.cancel()


async def _leave_room(
    chat_service: ChatService,
    room_id: int,
    username: str,
):
    success = await chat_service.leave_room.use(room_id, username)
    if success == False:
        print("Error leaving room")


@router.websocket("/ws/messages/{room_id}/{username}")
async def messages_websocket(
    websocket: WebSocket,
    room_id: int,
    username: str,
    chat_service: ChatService = Depends(get_chat_service),
    message_logger: MessageLogger = Depends(get_message_logger),
):
    await websocket.accept()

    join_result = await _join_room(chat_service, room_id, username, websocket)
    if join_result is None:
        return

    metrics.ACTIVE_WS.inc()

    try:
        await _send_history(websocket, join_result)

        send_task = await _send_new_messages_task(websocket, chat_service, room_id, username)

        await _receive_new_messages(
            websocket, chat_service, room_id, username, send_task, message_logger,
        )

    except:
        tb = traceback.format_exc()
        print(f"in messages_websocket unknown exception caught, traceback:\n{tb}")

    finally:
        await _leave_room(chat_service, room_id, username)

        if websocket.state == websockets.State.OPEN:
            # await websocket.close()
            ...

        metrics.ACTIVE_WS.dec()


