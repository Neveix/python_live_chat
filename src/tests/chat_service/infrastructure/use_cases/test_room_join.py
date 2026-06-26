import pytest
from unittest.mock import AsyncMock
from chat_service.core.models import RoomJoinResult, SystemMessage, UserMessage, Room
from chat_service.core.exceptions import RepoError, RoomNotFoundError
from chat_service.infrastructure.use_cases.room_join import RoomJoinUseCaseImpl


class TestRoomJoinUseCase:
    @pytest.fixture
    def mock_room_repo(self) -> AsyncMock:
        return AsyncMock()
    
    @pytest.fixture
    def mock_presence_repo(self) -> AsyncMock:
        return AsyncMock()
    
    @pytest.fixture
    def mock_message_repo(self) -> AsyncMock:
        return AsyncMock()
    
    @pytest.fixture
    def use_case(self, mock_room_repo, mock_presence_repo, mock_message_repo) -> RoomJoinUseCaseImpl:
        return RoomJoinUseCaseImpl(
            room_repo=mock_room_repo,
            presence_repo=mock_presence_repo,
            message_repo=mock_message_repo,
        )

    @pytest.mark.asyncio
    async def test_join_room_success(self, mock_room_repo, mock_presence_repo, mock_message_repo, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test User")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_presence_repo.add.return_value = True
        mock_message_repo.add.return_value = SystemMessage(text="test_user joined", id=1)
        mock_message_repo.get_recent.return_value = [
            UserMessage(text="hello", sender="other_user", id=2),
            SystemMessage(text="test_user joined", id=1),
        ]

        # Act
        result = await use_case.use(room_id=1, username="test_user")

        # Assert
        assert isinstance(result, RoomJoinResult)
        assert result.success is True
        assert result.detail is None
        assert result.recent_messages is not None
        assert len(result.recent_messages) == 2
        
        mock_room_repo.get_by_id.assert_awaited_once_with(1)
        mock_presence_repo.add.assert_awaited_once_with(1, "test_user")
        
        actual_call = mock_message_repo.add.await_args_list[0]
        assert actual_call.args[0] == 1
        assert actual_call.args[1].text == "test_user joined"
        
        mock_message_repo.get_recent.assert_awaited_once_with(1)

    @pytest.mark.asyncio
    async def test_join_room_not_found(self, mock_room_repo, mock_presence_repo, mock_message_repo, use_case) -> None:
        # Arrange
        mock_room_repo.get_by_id.return_value = None

        # Act & Assert
        with pytest.raises(RoomNotFoundError):
            await use_case.use(room_id=999, username="test_user")
        
        mock_room_repo.get_by_id.assert_awaited_once_with(999)
        mock_presence_repo.add.assert_not_awaited()
        mock_message_repo.add.assert_not_awaited()
        mock_message_repo.get_recent.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_join_room_already_present(self, mock_room_repo, mock_presence_repo, mock_message_repo, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test User")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_presence_repo.add.return_value = False
        
        # Act
        result = await use_case.use(room_id=1, username="test_user")

        # Assert
        assert isinstance(result, RoomJoinResult)
        assert result.success is False
        assert result.detail is not None
        assert "already" in result.detail
        assert result.recent_messages is None
        
        mock_room_repo.get_by_id.assert_awaited_once_with(1)
        mock_presence_repo.add.assert_awaited_once_with(1, "test_user")
        mock_message_repo.add.assert_not_awaited()
        mock_message_repo.get_recent.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_join_room_repo_error_rollback(self, mock_room_repo, mock_presence_repo, mock_message_repo, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test User")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_presence_repo.add.return_value = True
        mock_message_repo.add.side_effect = RepoError("Database error")
        mock_presence_repo.remove.return_value = True

        # Act & Assert
        with pytest.raises(RepoError):
            await use_case.use(room_id=1, username="test_user")

        mock_room_repo.get_by_id.assert_awaited_once_with(1)
        mock_presence_repo.add.assert_awaited_once_with(1, "test_user")
        
        actual_call = mock_message_repo.add.await_args_list[0]
        assert actual_call.args[0] == 1
        assert actual_call.args[1].text == "test_user joined"
        
        mock_presence_repo.remove.assert_awaited_once_with(1, "test_user")
        mock_message_repo.get_recent.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_join_room_repo_error_rollback_fails(self, mock_room_repo, mock_presence_repo, mock_message_repo, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test User")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_presence_repo.add.return_value = True
        mock_message_repo.add.side_effect = RepoError("Database error")
        mock_presence_repo.remove.side_effect = RepoError("Rollback error")

        # Act & Assert
        with pytest.raises(RepoError):
            await use_case.use(room_id=1, username="test_user")

        mock_room_repo.get_by_id.assert_awaited_once_with(1)
        mock_presence_repo.add.assert_awaited_once_with(1, "test_user")
        
        actual_call = mock_message_repo.add.await_args_list[0]
        assert actual_call.args[0] == 1
        assert actual_call.args[1].text == "test_user joined"
        
        mock_presence_repo.remove.assert_awaited_once_with(1, "test_user")
        mock_message_repo.get_recent.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_join_room_without_recent_messages(self, mock_room_repo, mock_presence_repo, mock_message_repo, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test User")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_presence_repo.add.return_value = True
        mock_message_repo.add.return_value = SystemMessage(text="test_user joined", id=1)
        mock_message_repo.get_recent.return_value = []

        # Act
        result = await use_case.use(room_id=1, username="test_user")

        # Assert
        assert isinstance(result, RoomJoinResult)
        assert result.success is True
        assert result.detail is None
        assert result.recent_messages == []
        
        mock_room_repo.get_by_id.assert_awaited_once_with(1)
        mock_presence_repo.add.assert_awaited_once_with(1, "test_user")
        
        actual_call = mock_message_repo.add.await_args_list[0]
        assert actual_call.args[0] == 1
        assert actual_call.args[1].text == "test_user joined"
        
        mock_message_repo.get_recent.assert_awaited_once_with(1)

    @pytest.mark.asyncio
    async def test_join_room_multiple_users_same_room(self, mock_room_repo, mock_presence_repo, mock_message_repo, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test User")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_presence_repo.add.return_value = True
        mock_message_repo.add.return_value = SystemMessage(text="user1 joined", id=1)
        mock_message_repo.get_recent.return_value = []
        
        # Act - First user
        result1 = await use_case.use(room_id=1, username="user1")
        assert result1.success is True
        
        # Reset mocks for second user
        mock_message_repo.add.return_value = SystemMessage(text="user2 joined", id=2)
        mock_message_repo.get_recent.return_value = [
            SystemMessage(text="user1 joined", id=1),
            SystemMessage(text="user2 joined", id=2),
        ]
        
        # Act - Second user
        result2 = await use_case.use(room_id=1, username="user2")
        
        # Assert
        assert result2.success is True
        assert result2.recent_messages is not None
        assert len(result2.recent_messages) == 2
        
        assert mock_room_repo.get_by_id.await_count == 2
        assert mock_presence_repo.add.await_count == 2
        mock_presence_repo.add.assert_any_call(1, "user1")
        mock_presence_repo.add.assert_any_call(1, "user2")

    @pytest.mark.asyncio
    async def test_join_room_then_rejoin(self, mock_room_repo, mock_presence_repo, mock_message_repo, use_case) -> None:
        # Arrange
        mock_room = Room(id=1, name="Test Room", creator="Test User")
        mock_room_repo.get_by_id.return_value = mock_room
        mock_presence_repo.add.return_value = True
        mock_message_repo.add.return_value = SystemMessage(text="test_user joined", id=1)
        mock_message_repo.get_recent.return_value = []
        
        # Act - First join
        result1 = await use_case.use(room_id=1, username="test_user")
        assert result1.success is True
        
        # Act - Second join (rejoin)
        mock_message_repo.add.return_value = SystemMessage(text="test_user joined", id=2)
        mock_message_repo.get_recent.return_value = [
            SystemMessage(text="test_user joined", id=1),
            SystemMessage(text="test_user joined", id=2),
        ]
        
        result2 = await use_case.use(room_id=1, username="test_user")
        
        # Assert
        assert result2.success is True
        assert result2.detail is None
        assert result2.recent_messages is not None
        assert len(result2.recent_messages) == 2
        
        assert mock_room_repo.get_by_id.await_count == 2
        assert mock_presence_repo.add.await_count == 2
        mock_presence_repo.add.assert_called_with(1, "test_user")
        
        assert mock_message_repo.add.await_count == 2
        
        first_call = mock_message_repo.add.await_args_list[0]
        assert first_call.args[0] == 1
        assert first_call.args[1].text == "test_user joined"
        
        second_call = mock_message_repo.add.await_args_list[1]
        assert second_call.args[0] == 1
        assert second_call.args[1].text == "test_user joined"