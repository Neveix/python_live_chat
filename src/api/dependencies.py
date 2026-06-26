from fastapi import Depends
from redis.asyncio import Redis

from ..chat_service.factory.default import ChatServiceFactory
from ..chat_service.core.interfaces import ChatService

_pubsub_redis: Redis | None = None
_redis: Redis | None = None
_chat_service: ChatService | None = None


async def get_redis():
    global _redis
    if _redis:
        yield _redis
        return
    
    redis = Redis.from_url(
        "redis://localhost:6379",
        socket_timeout=5,
        socket_connect_timeout=5
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
        redis = Depends(get_redis),
        pubsub_redis = Depends(get_pubsub_redis),
    ) -> ChatService:
    global _chat_service
    if _chat_service:
        return _chat_service
    
    _chat_service = ChatServiceFactory(redis, pubsub_redis).create()
    return _chat_service