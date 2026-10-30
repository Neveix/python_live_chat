import os
from pathlib import Path

from fastapi import Depends
from redis.asyncio import Redis

from src.utils.message_logger import (
    MessageLogger,
    MessageLoggerBypass,
    MessageLoggerImpl,
)

from ..chat_service.core.interfaces import ChatService
from ..chat_service.factory.default import ChatServiceFactory

message_logger_path = os.environ.get("MESSAGE_LOGGER_PATH")
if message_logger_path:
    print(f"using {message_logger_path=}")
else:
    print("not using message_logger.")

_pubsub_redis: Redis | None = None
_redis: Redis | None = None
_chat_service: ChatService | None = None
_message_logger: MessageLogger | None = None


async def get_redis():
    global _redis
    if _redis:
        yield _redis
        return

    redis = Redis.from_url(
        "redis://localhost:6379", socket_timeout=5, socket_connect_timeout=5
    )
    _redis = redis
    # await redis.flushdb()
    try:
        yield redis
    finally:
        await redis.close()


async def get_pubsub_redis():
    global _pubsub_redis

    if _pubsub_redis:
        yield _pubsub_redis
        return

    redis = Redis.from_url(
        "redis://localhost:6379",
        socket_timeout=None,
        socket_connect_timeout=5,
        health_check_interval=30,
        socket_keepalive=True,
    )
    _pubsub_redis = redis
    try:
        yield redis
    finally:
        await redis.close()


async def get_chat_service(
    redis=Depends(get_redis),
    pubsub_redis=Depends(get_pubsub_redis),
) -> ChatService:
    global _chat_service
    if _chat_service:
        return _chat_service

    _chat_service = ChatServiceFactory(redis, pubsub_redis).create()
    return _chat_service


async def get_message_logger() -> MessageLogger:
    global _message_logger
    if _message_logger:
        return _message_logger

    if message_logger_path is None:
        return MessageLoggerBypass()

    _message_logger = MessageLoggerImpl(Path(message_logger_path))
    return _message_logger
