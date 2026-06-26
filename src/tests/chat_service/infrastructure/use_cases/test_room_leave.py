import pytest
from unittest.mock import AsyncMock
from chat_service.core.exceptions import RepoError, RoomNotFoundError
from chat_service.core.models import SystemMessage, Room
from chat_service.infrastructure.use_cases.room_leave import RoomLeaveUseCaseImpl


class TestRoomLeaveUseCase:
    @pytest.fixture
    def mock_room_repo(self) -> AsyncMock:
        return AsyncMock()
    
    @pytest.fixture
    def mock_message_repo(self) -> AsyncMock:
        return AsyncMock()
    
    @pytest.fixture
    def mock_presence_repo(self) -> AsyncMock:
        return AsyncMock()
    
    @pytest.fixture
    def mock_message_listener(self) -> AsyncMock:
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_room_repo, mock_message_repo, mock_presence_repo, mock_message_listener) -> RoomLeaveUseCaseImpl:
        return RoomLeaveUseCaseImpl(
            room_repo=mock_room_repo,
            message_repo=mock_message_repo,
            presence_repo=mock_presence_repo,
            message_listener=mock_message_listener,
        )

    @pytest.mark.asyncio
    async def test_leave_room_success(self, mock_room_repo, mock_message_repo, mock_presence_repo, mock_message_listener, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test Creator")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_presence_repo.remove.return_value = True
        mock_message_repo.add.return_value = SystemMessage(text="test_user left", id=1)
        mock_message_listener.break_listen.return_value = True

        # Act
        result = await use_case.use(room_id=1, username="test_user")

        # Assert
        assert result is True
        
        mock_room_repo.get_by_id.assert_awaited_once_with(1)
        mock_presence_repo.remove.assert_awaited_once_with(1, "test_user")
        
        actual_call = mock_message_repo.add.await_args_list[0]
        assert actual_call.args[0] == 1
        assert actual_call.args[1].text == "test_user left"
        
        mock_message_listener.break_listen.assert_awaited_once_with(1, "test_user")

    @pytest.mark.asyncio
    async def test_leave_room_not_found(self, mock_room_repo, mock_message_repo, mock_presence_repo, mock_message_listener, use_case) -> None:
        # Arrange
        mock_room_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(RoomNotFoundError):
            await use_case.use(room_id=999, username="test_user")
        
        mock_room_repo.get_by_id.assert_awaited_once_with(999)
        mock_presence_repo.remove.assert_not_awaited()
        mock_message_repo.add.assert_not_awaited()
        mock_message_listener.break_listen.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_leave_room_user_not_in_room(self, mock_room_repo, mock_message_repo, mock_presence_repo, mock_message_listener, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test Creator")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_presence_repo.remove.return_value = False

        # Act
        result = await use_case.use(room_id=1, username="test_user")

        # Assert
        assert result is False
        
        mock_room_repo.get_by_id.assert_awaited_once_with(1)
        mock_presence_repo.remove.assert_awaited_once_with(1, "test_user")
        mock_message_repo.add.assert_not_awaited()
        mock_message_listener.break_listen.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_leave_room_repo_error_on_message_add(self, mock_room_repo, mock_message_repo, mock_presence_repo, mock_message_listener, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test Creator")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_presence_repo.remove.return_value = True
        mock_message_repo.add.side_effect = RepoError("Database error")

        # Act & Assert
        with pytest.raises(RepoError):
            await use_case.use(room_id=1, username="test_user")

        mock_room_repo.get_by_id.assert_awaited_once_with(1)
        mock_presence_repo.remove.assert_awaited_once_with(1, "test_user")
        
        actual_call = mock_message_repo.add.await_args_list[0]
        assert actual_call.args[0] == 1
        assert actual_call.args[1].text == "test_user left"
        
        mock_message_listener.break_listen.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_leave_room_repo_error_on_break_listen(self, mock_room_repo, mock_message_repo, mock_presence_repo, mock_message_listener, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test Creator")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_presence_repo.remove.return_value = True
        mock_message_repo.add.return_value = SystemMessage(text="test_user left", id=1)
        mock_message_listener.break_listen.side_effect = RepoError("Listener error")

        # Act & Assert
        with pytest.raises(RepoError):
            await use_case.use(room_id=1, username="test_user")

        mock_room_repo.get_by_id.assert_awaited_once_with(1)
        mock_presence_repo.remove.assert_awaited_once_with(1, "test_user")
        
        actual_call = mock_message_repo.add.await_args_list[0]
        assert actual_call.args[0] == 1
        assert actual_call.args[1].text == "test_user left"
        
        mock_message_listener.break_listen.assert_awaited_once_with(1, "test_user")

    @pytest.mark.asyncio
    async def test_leave_room_multiple_users_leave_sequentially(self, mock_room_repo, mock_message_repo, mock_presence_repo, mock_message_listener, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test Creator")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_presence_repo.remove.return_value = True
        mock_message_repo.add.return_value = SystemMessage(text="user left", id=1)
        mock_message_listener.break_listen.return_value = True

        # Act - First user leaves
        result1 = await use_case.use(room_id=1, username="user1")
        assert result1 is True
        
        # Act - Second user leaves
        result2 = await use_case.use(room_id=1, username="user2")
        assert result2 is True

        # Assert
        assert mock_room_repo.get_by_id.await_count == 2
        assert mock_presence_repo.remove.await_count == 2
        mock_presence_repo.remove.assert_any_call(1, "user1")
        mock_presence_repo.remove.assert_any_call(1, "user2")
        
        assert mock_message_repo.add.await_count == 2
        assert mock_message_listener.break_listen.await_count == 2
        mock_message_listener.break_listen.assert_any_call(1, "user1")
        mock_message_listener.break_listen.assert_any_call(1, "user2")

    @pytest.mark.asyncio
    async def test_leave_room_same_user_multiple_times(self, mock_room_repo, mock_message_repo, mock_presence_repo, mock_message_listener, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test Creator")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_message_repo.add.return_value = SystemMessage(text="test_user left", id=1)
        mock_message_listener.break_listen.return_value = True
        
        # First leave - user is in room
        mock_presence_repo.remove.return_value = True
        result1 = await use_case.use(room_id=1, username="test_user")
        assert result1 is True
        
        # Second leave - user already left
        mock_presence_repo.remove.return_value = False
        result2 = await use_case.use(room_id=1, username="test_user")
        assert result2 is False

        # Assert
        assert mock_room_repo.get_by_id.await_count == 2
        assert mock_presence_repo.remove.await_count == 2
        mock_presence_repo.remove.assert_called_with(1, "test_user")
        
        # Message should only be added when user successfully leaves
        assert mock_message_repo.add.await_count == 1
        assert mock_message_listener.break_listen.await_count == 1

    @pytest.mark.asyncio
    async def test_leave_room_different_rooms(self, mock_room_repo, mock_message_repo, mock_presence_repo, mock_message_listener, use_case) -> None:
        # Arrange
        mock_room_repo.get_by_id.side_effect = lambda id: Room(id=id, name=f"Room {id}", creator="123") if id in [1, 2] else None
        mock_presence_repo.remove.return_value = True
        mock_message_repo.add.return_value = SystemMessage(text="user left", id=1)
        mock_message_listener.break_listen.return_value = True

        # Act
        result1 = await use_case.use(room_id=1, username="test_user")
        result2 = await use_case.use(room_id=2, username="test_user")

        # Assert
        assert result1 is True
        assert result2 is True
        
        mock_room_repo.get_by_id.assert_any_call(1)
        mock_room_repo.get_by_id.assert_any_call(2)
        assert mock_room_repo.get_by_id.await_count == 2
        
        mock_presence_repo.remove.assert_any_call(1, "test_user")
        mock_presence_repo.remove.assert_any_call(2, "test_user")
        assert mock_presence_repo.remove.await_count == 2
        
        assert mock_message_repo.add.await_count == 2
        assert mock_message_listener.break_listen.await_count == 2