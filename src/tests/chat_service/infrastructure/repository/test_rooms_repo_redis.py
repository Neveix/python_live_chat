import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from redis.asyncio import Redis

from chat_service.core.models import Room
from chat_service.core.exceptions import RepoError, RepoElementAlreadyExists
from chat_service.infrastructure.repository.rooms_repo_redis import RoomsRepoRedis


@pytest.mark.asyncio
class TestRoomsRepoRedis:
    """Test class for RoomsRepoRedis. Uses mock_redis fixture."""

    async def test_get_all_success(self, mock_redis: AsyncMock) -> None:
        mock_redis.smembers.return_value = {b"1", b"2"}
        mock_redis.hgetall.side_effect = [
            {b"name": b"room1", b"creator": b"user1"},
            {b"name": b"room2", b"creator": b"user2"},
        ]
        repo = RoomsRepoRedis(mock_redis)
        rooms = await repo.get_all()
        assert len(rooms) == 2
        assert rooms[0].name == "room1"
        assert rooms[0].creator == "user1"
        assert rooms[1].name == "room2"
        assert rooms[1].creator == "user2"
        mock_redis.smembers.assert_awaited_once_with("rooms:all")
        assert mock_redis.hgetall.await_count == 2

    async def test_get_all_empty(self, mock_redis: AsyncMock) -> None:
        mock_redis.smembers.return_value = set()
        repo = RoomsRepoRedis(mock_redis)
        rooms = await repo.get_all()
        assert rooms == []
        mock_redis.smembers.assert_awaited_once_with("rooms:all")

    async def test_get_by_id_found(self, mock_redis: AsyncMock) -> None:
        mock_redis.hgetall.return_value = {b"name": b"room1", b"creator": b"user1"}
        repo = RoomsRepoRedis(mock_redis)
        room = await repo.get_by_id(1)
        assert room is not None
        assert room.id == 1
        assert room.name == "room1"
        assert room.creator == "user1"
        mock_redis.hgetall.assert_awaited_once_with("room:1")

    async def test_get_by_id_not_found(self, mock_redis: AsyncMock) -> None:
        mock_redis.hgetall.return_value = {}
        repo = RoomsRepoRedis(mock_redis)
        room = await repo.get_by_id(999)
        assert room is None
        mock_redis.hgetall.assert_awaited_once_with("room:999")

    async def test_get_by_name_found(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.side_effect = [b"1", None]
        mock_redis.hgetall.return_value = {b"name": b"room1", b"creator": b"user1"}
        repo = RoomsRepoRedis(mock_redis)
        room = await repo.get_by_name("room1")
        assert room is not None
        assert room.id == 1
        assert room.name == "room1"
        assert room.creator == "user1"
        mock_redis.get.assert_awaited_with("room:name:room1")
        mock_redis.hgetall.assert_awaited_once_with("room:1")

    async def test_get_by_name_not_found(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = None
        repo = RoomsRepoRedis(mock_redis)
        room = await repo.get_by_name("nonexistent")
        assert room is None
        mock_redis.get.assert_awaited_once_with("room:name:nonexistent")

    async def test_create_success(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = None
        mock_redis.incr.return_value = 1
        mock_redis.hset = AsyncMock()
        mock_redis.set = AsyncMock()
        mock_redis.sadd = AsyncMock()
        repo = RoomsRepoRedis(mock_redis)
        room = await repo.create("new_room", "creator_user")
        assert room.id == 1
        assert room.name == "new_room"
        assert room.creator == "creator_user"
        mock_redis.get.assert_awaited_once_with("room:name:new_room")
        mock_redis.incr.assert_awaited_once_with("rooms:next_id")
        mock_redis.hset.assert_awaited_once_with("room:1", mapping={"name": "new_room", "creator": "creator_user"})
        mock_redis.set.assert_awaited_once_with("room:name:new_room", 1)
        mock_redis.sadd.assert_awaited_once_with("rooms:all", "1")

    async def test_create_duplicate_name(self, mock_redis: AsyncMock) -> None:
        mock_redis.get.return_value = b"1"
        repo = RoomsRepoRedis(mock_redis)
        with pytest.raises(RepoElementAlreadyExists, match="Room 'dup_room' already exists"):
            await repo.create("dup_room", "user")
        mock_redis.get.assert_awaited_once_with("room:name:dup_room")

    async def test_delete_success(self, mock_redis: AsyncMock) -> None:
        mock_redis.hgetall.return_value = {b"name": b"room1", b"creator": b"user1"}
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.srem = AsyncMock(return_value=1)
        repo = RoomsRepoRedis(mock_redis)
        result = await repo.delete(1)
        assert result is True
        mock_redis.hgetall.assert_awaited_once_with("room:1")
        mock_redis.delete.assert_any_await("room:1")
        mock_redis.delete.assert_any_await("room:name:room1")
        mock_redis.srem.assert_awaited_once_with("rooms:all", "1")

    async def test_delete_not_found(self, mock_redis: AsyncMock) -> None:
        mock_redis.hgetall.return_value = {}
        repo = RoomsRepoRedis(mock_redis)
        result = await repo.delete(999)
        assert result is False
        mock_redis.hgetall.assert_awaited_once_with("room:999")

    async def test_repo_error(self, mock_redis: AsyncMock) -> None:
        mock_redis.smembers.side_effect = Exception("Redis connection error")
        repo = RoomsRepoRedis(mock_redis)
        with pytest.raises(RepoError):
            await repo.get_all()
        mock_redis.smembers.assert_awaited_once_with("rooms:all")