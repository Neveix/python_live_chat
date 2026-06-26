import pytest
import json
from unittest.mock import AsyncMock, MagicMock, Mock
from typing import AsyncGenerator

from chat_service.core.models import Message, UserMessage, SystemMessage
from chat_service.core.exceptions import RepoError
from chat_service.infrastructure.repository.message_repo_redis import \
    MessagesRepoRedis, RedisMessageSubscription


class TestMessagesRepoRedis:

    @pytest.mark.asyncio
    async def test_add_success(self, mock_redis: AsyncMock) -> None:
        mock_redis.incr = AsyncMock(return_value=1)
        mock_redis.lpush = AsyncMock()
        mock_redis.ltrim = AsyncMock()
        mock_redis.publish = AsyncMock()

        repo = MessagesRepoRedis(redis=mock_redis, pubsub_redis=mock_redis)
        message = UserMessage(text="hello", sender="test_user")

        result = await repo.add(room_id=1, message=message)

        assert result.id == 1
        assert result.text == "hello"
        assert result.sender == "test_user"
        mock_redis.incr.assert_awaited_once_with("message_id:1")
        mock_redis.lpush.assert_awaited_once()
        mock_redis.ltrim.assert_awaited_once_with("history:1", 0, 99)
        mock_redis.publish.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_add_repo_error(self, mock_redis: AsyncMock) -> None:
        mock_redis.incr = AsyncMock(side_effect=Exception("Redis error"))

        repo = MessagesRepoRedis(redis=mock_redis, pubsub_redis=mock_redis)
        message = UserMessage(text="hello", sender="test_user")

        with pytest.raises(RepoError):
            await repo.add(room_id=1, message=message)

    @pytest.mark.asyncio
    async def test_get_recent_success(self, mock_redis: AsyncMock) -> None:
        message1 = UserMessage(text="first", sender="user1", id=1)
        message2 = UserMessage(text="second", sender="user2", id=2)
        messages_json = [
            json.dumps(message1.serialize()),
            json.dumps(message2.serialize()),
        ]
        mock_redis.lrange = AsyncMock(return_value=messages_json)

        repo = MessagesRepoRedis(redis=mock_redis, pubsub_redis=mock_redis)
        result = await repo.get_recent(room_id=1, limit=50)

        assert len(result) == 2
        
        assert isinstance(result[1], UserMessage)
        assert result[1].text == "first"
        assert result[1].sender == "user1"
        
        assert isinstance(result[0], UserMessage)
        assert result[0].text == "second"
        assert result[0].sender == "user2"
        mock_redis.lrange.assert_awaited_once_with("history:1", 0, 49)

    @pytest.mark.asyncio
    async def test_get_recent_empty(self, mock_redis: AsyncMock) -> None:
        mock_redis.lrange = AsyncMock(return_value=[])

        repo = MessagesRepoRedis(redis=mock_redis, pubsub_redis=mock_redis)
        result = await repo.get_recent(room_id=1, limit=50)

        assert result == []
        mock_redis.lrange.assert_awaited_once_with("history:1", 0, 49)

    @pytest.mark.asyncio
    async def test_get_recent_repo_error(self, mock_redis: AsyncMock) -> None:
        mock_redis.lrange = AsyncMock(side_effect=Exception("Redis error"))

        repo = MessagesRepoRedis(redis=mock_redis, pubsub_redis=mock_redis)

        with pytest.raises(RepoError):
            await repo.get_recent(room_id=1, limit=50)

    @pytest.mark.asyncio
    async def test_listen_new_success(self, mock_redis: AsyncMock) -> None:
        pubsub_mock = AsyncMock()
        pubsub_mock.subscribe = AsyncMock()
        async def listen() -> AsyncGenerator:
            yield {"type": "message", "data": json.dumps({"type": "user", "text": "hello", "sender": "user1", "timestamp": "2023-01-01T00:00:00", "id": 1})}
            yield {"type": "message", "data": json.dumps({"type": "system", "text": "system msg", "timestamp": "2023-01-01T00:00:01", "id": 2})}
            
        
        pubsub_mock.listen = Mock(return_value=listen())
        mock_redis.pubsub = MagicMock(return_value=pubsub_mock)

        repo = MessagesRepoRedis(redis=mock_redis, pubsub_redis=mock_redis)
        gen, subscription = await repo.listen_new(room_id=1)

        assert isinstance(subscription, RedisMessageSubscription)
        assert subscription.channel == "room:1"
        assert subscription.pubsub == pubsub_mock

        messages: list[Message] = []
        async for msg in gen:
            messages.append(msg)

        assert len(messages) == 2
        assert isinstance(messages[0], UserMessage)
        assert messages[0].text == "hello"
        assert isinstance(messages[1], SystemMessage)
        assert messages[1].text == "system msg"

        pubsub_mock.subscribe.assert_awaited_once_with("room:1")

    @pytest.mark.asyncio
    async def test_listen_new_repo_error(self, mock_redis: AsyncMock) -> None:
        mock_redis.pubsub = MagicMock(side_effect=Exception("Redis error"))

        repo = MessagesRepoRedis(redis=mock_redis, pubsub_redis=mock_redis)

        with pytest.raises(RepoError):
            await repo.listen_new(room_id=1)