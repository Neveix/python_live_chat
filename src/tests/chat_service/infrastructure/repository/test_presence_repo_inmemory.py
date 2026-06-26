import pytest
from chat_service.infrastructure.repository.presence_repo_inmemory import PresenceRepoInMemory


class TestPresenceRepoInMemory:
    """Test class for PresenceRepoInMemory. Uses the real implementation directly."""

    @pytest.fixture
    def repo(self) -> PresenceRepoInMemory:
        return PresenceRepoInMemory()

    @pytest.mark.asyncio
    async def test_add_new_user(self, repo: PresenceRepoInMemory) -> None:
        result = await repo.add(1, "user1")
        assert result is True
        users = await repo.get_all(1)
        assert users == ["user1"]

    @pytest.mark.asyncio
    async def test_add_duplicate_user(self, repo: PresenceRepoInMemory) -> None:
        await repo.add(1, "user1")
        result = await repo.add(1, "user1")
        assert result is False
        users = await repo.get_all(1)
        assert users == ["user1"]

    @pytest.mark.asyncio
    async def test_remove_existing_user(self, repo: PresenceRepoInMemory) -> None:
        await repo.add(1, "user1")
        result = await repo.remove(1, "user1")
        assert result is True
        users = await repo.get_all(1)
        assert users == []

    @pytest.mark.asyncio
    async def test_remove_nonexistent_user(self, repo: PresenceRepoInMemory) -> None:
        result = await repo.remove(1, "nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_get_all_multiple_users(self, repo: PresenceRepoInMemory) -> None:
        await repo.add(1, "user1")
        await repo.add(1, "user2")
        await repo.add(1, "user3")
        users = await repo.get_all(1)
        assert sorted(users) == ["user1", "user2", "user3"]

    @pytest.mark.asyncio
    async def test_get_all_empty_room(self, repo: PresenceRepoInMemory) -> None:
        users = await repo.get_all(1)
        assert users == []

    @pytest.mark.asyncio
    async def test_get_all_different_rooms(self, repo: PresenceRepoInMemory) -> None:
        await repo.add(1, "user1")
        await repo.add(1, "user2")
        await repo.add(2, "user3")
        users_room1 = await repo.get_all(1)
        users_room2 = await repo.get_all(2)
        assert sorted(users_room1) == ["user1", "user2"]
        assert users_room2 == ["user3"]