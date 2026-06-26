import pytest
from unittest.mock import AsyncMock
from chat_service.core.models import Room
from chat_service.core.exceptions import RepoError
from chat_service.infrastructure.use_cases.rooms_get import RoomsGetUseCaseImpl


class TestRoomsGetUseCase:
    @pytest.mark.asyncio
    async def test_get_rooms_success(self, mock_rooms_repo: AsyncMock) -> None:
        expected_rooms: list[Room] = [
            Room(id=1, name="room1", creator="user1"),
            Room(id=2, name="room2", creator="user2"),
        ]
        mock_rooms_repo.get_all.return_value = expected_rooms
        use_case = RoomsGetUseCaseImpl(repo=mock_rooms_repo)
        result: list[Room] = await use_case.use()
        assert result == expected_rooms
        mock_rooms_repo.get_all.assert_awaited_once_with()

    @pytest.mark.asyncio
    async def test_get_rooms_empty(self, mock_rooms_repo: AsyncMock) -> None:
        mock_rooms_repo.get_all.return_value = []
        use_case = RoomsGetUseCaseImpl(repo=mock_rooms_repo)
        result: list[Room] = await use_case.use()
        assert result == []
        mock_rooms_repo.get_all.assert_awaited_once_with()

    @pytest.mark.asyncio
    async def test_get_rooms_repo_error(self, mock_rooms_repo: AsyncMock) -> None:
        mock_rooms_repo.get_all.side_effect = RepoError()
        use_case = RoomsGetUseCaseImpl(repo=mock_rooms_repo)
        with pytest.raises(RepoError):
            await use_case.use()
        mock_rooms_repo.get_all.assert_awaited_once_with()