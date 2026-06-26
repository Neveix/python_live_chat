import asyncio
from datetime import datetime
from typing import AsyncGenerator, AsyncIterator
from unittest.mock import AsyncMock, Mock

import pytest
from pytest import FixtureRequest

from chat_service.core.models import Room, UserMessage, SystemMessage, Message
from chat_service.core.interfaces import RoomRepo, MessageRepo, PresenceRepo, MessageListener


@pytest.fixture(scope="function")
def sample_room() -> Room:
    return Room(id=1, name="test_room", creator="test_user")


@pytest.fixture(scope="function")
def sample_user_message() -> UserMessage:
    return UserMessage(text="hello", sender="test_user", timestamp=datetime.now(), id=1)


@pytest.fixture(scope="function")
def sample_system_message() -> SystemMessage:
    return SystemMessage(text="system message", timestamp=datetime.now(), id=2)


@pytest.fixture(scope="function")
def mock_redis() -> AsyncMock:
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.incr = AsyncMock(return_value=1)
    mock.hset = AsyncMock(return_value=True)
    mock.hgetall = AsyncMock(return_value={b"name": b"test_room", b"creator": b"test_user"})
    mock.lpush = AsyncMock(return_value=1)
    mock.lrange = AsyncMock(return_value=[])
    mock.ltrim = AsyncMock(return_value=True)
    mock.publish = AsyncMock(return_value=1)
    mock.pubsub = AsyncMock()
    mock.smembers = AsyncMock(return_value=set())
    mock.sadd = AsyncMock(return_value=1)
    mock.srem = AsyncMock(return_value=1)
    mock.delete = AsyncMock(return_value=1)
    return mock


@pytest.fixture(scope="function")
def mock_rooms_repo() -> AsyncMock:
    mock = AsyncMock(spec=RoomRepo)
    mock.get_all = AsyncMock(return_value=[])
    mock.get_by_id = AsyncMock(return_value=None)
    mock.get_by_name = AsyncMock(return_value=None)
    mock.create = AsyncMock(return_value=Room(id=1, name="test_room", creator="test_user"))
    mock.delete = AsyncMock(return_value=True)
    return mock


@pytest.fixture(scope="function")
def mock_messages_repo() -> AsyncMock:
    mock = AsyncMock(spec=MessageRepo)
    mock.add = AsyncMock(return_value=UserMessage(text="hello", sender="test_user", timestamp=datetime.now(), id=1))
    mock.get_recent = AsyncMock(return_value=[])
    mock.listen_new = AsyncMock()
    return mock


@pytest.fixture(scope="function")
def mock_presence_repo() -> AsyncMock:
    mock = AsyncMock(spec=PresenceRepo)
    mock.add = AsyncMock(return_value=True)
    mock.remove = AsyncMock(return_value=True)
    mock.get_all = AsyncMock(return_value=[])
    return mock


@pytest.fixture(scope="function")
def mock_message_listener() -> AsyncMock:
    mock = AsyncMock(spec=MessageListener)
    mock.listen = Mock()
    mock.break_listen = AsyncMock(return_value=True)
    return mock


@pytest.fixture(scope="function")
def message_generator(sample_user_message: UserMessage, sample_system_message: SystemMessage) -> AsyncGenerator[Message, None]:
    async def gen() -> AsyncGenerator[Message]:
        yield sample_user_message
        yield sample_system_message
    return gen()