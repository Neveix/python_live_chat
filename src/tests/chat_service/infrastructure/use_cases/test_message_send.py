import pytest
from unittest.mock import AsyncMock

from chat_service.core.models import UserMessage, Message
from chat_service.core.exceptions import RepoError
from chat_service.infrastructure.use_cases.message_send import MessageSendUseCaseImpl


class TestMessageSendUseCase:
    @pytest.mark.asyncio
    async def test_send_message_success(self, mock_messages_repo: AsyncMock) -> None:
        mock_messages_repo.add.return_value = UserMessage(
            text="hello",
            sender="test_user",
            id=1
        )
        use_case = MessageSendUseCaseImpl(messages_repo=mock_messages_repo)
        await use_case.use(room_id=1, username="test_user", text="hello")
        mock_messages_repo.add.assert_awaited_once()
        call_args = mock_messages_repo.add.call_args
        assert call_args is not None
        args, _ = call_args
        assert args[0] == 1
        assert isinstance(args[1], UserMessage)
        assert args[1].text == "hello"
        assert args[1].sender == "test_user"

    @pytest.mark.asyncio
    async def test_send_message_repo_error(self, mock_messages_repo: AsyncMock) -> None:
        mock_messages_repo.add.side_effect = RepoError()
        use_case = MessageSendUseCaseImpl(messages_repo=mock_messages_repo)
        with pytest.raises(RepoError):
            await use_case.use(room_id=1, username="test_user", text="hello")