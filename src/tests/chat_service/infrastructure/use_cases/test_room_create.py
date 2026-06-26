import pytest
from unittest.mock import AsyncMock
from chat_service.core.exceptions import RepoElementAlreadyExists, RepoError
from chat_service.core.models import Room
from chat_service.infrastructure.use_cases.room_create import RoomCreateUseCaseImpl


class TestRoomCreateUseCase:
    @pytest.mark.asyncio
    async def test_create_room_success(
        self,
        mock_rooms_repo: AsyncMock,
        mock_messages_repo: AsyncMock,
        sample_room: Room,
    ) -> None:
        mock_rooms_repo.create.return_value = sample_room
        mock_messages_repo.add.return_value = AsyncMock()

        use_case = RoomCreateUseCaseImpl(
            rooms_repo=mock_rooms_repo,
            messages_repo=mock_messages_repo,
        )

        result = await use_case.use(room_name="test_room", username="test_user")

        assert result == sample_room
        mock_rooms_repo.create.assert_awaited_once_with("test_room", "test_user")
        mock_messages_repo.add.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_create_room_duplicate_name(
        self,
        mock_rooms_repo: AsyncMock,
        mock_messages_repo: AsyncMock,
    ) -> None:
        mock_rooms_repo.create.side_effect = RepoElementAlreadyExists("Room 'test_room' already exists")

        use_case = RoomCreateUseCaseImpl(
            rooms_repo=mock_rooms_repo,
            messages_repo=mock_messages_repo,
        )

        with pytest.raises(RepoElementAlreadyExists):
            await use_case.use(room_name="test_room", username="test_user")

        mock_rooms_repo.create.assert_awaited_once_with("test_room", "test_user")
        mock_messages_repo.add.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_create_room_repo_error(
        self,
        mock_rooms_repo: AsyncMock,
        mock_messages_repo: AsyncMock,
    ) -> None:
        mock_rooms_repo.create.side_effect = RepoError()

        use_case = RoomCreateUseCaseImpl(
            rooms_repo=mock_rooms_repo,
            messages_repo=mock_messages_repo,
        )

        with pytest.raises(RepoError):
            await use_case.use(room_name="test_room", username="test_user")

        mock_rooms_repo.create.assert_awaited_once_with("test_room", "test_user")
        mock_messages_repo.add.assert_not_awaited()