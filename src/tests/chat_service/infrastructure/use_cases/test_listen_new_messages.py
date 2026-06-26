import pytest
from typing import AsyncGenerator, AsyncIterator
from unittest.mock import AsyncMock, MagicMock

from chat_service.core.exceptions import MessageAlreadyListening, RepoError
from chat_service.core.models import Message, UserMessage
from chat_service.core.interfaces import MessageListener
from chat_service.infrastructure.use_cases.listen_new_messages import ListenNewMessagesUseCaseImpl


@pytest.mark.asyncio
async def test_listen_new_messages_success(
    mock_message_listener: AsyncMock,
    sample_user_message: UserMessage,
) -> None:
    async def _generator() -> AsyncGenerator[Message, None]:
        yield sample_user_message

    mock_message_listener.listen.return_value = _generator()
    use_case = ListenNewMessagesUseCaseImpl(message_listener=mock_message_listener)

    gen = use_case.use(room_id=1, username="test_user")
    assert isinstance(gen, AsyncGenerator)
    
    messages: list[Message] = []
    async for msg in gen:
        messages.append(msg)

    assert len(messages) == 1
    assert messages[0] == sample_user_message
    mock_message_listener.listen.assert_called_once_with(1, "test_user")


@pytest.mark.asyncio
async def test_listen_new_messages_already_listening(
    mock_message_listener: AsyncMock,
) -> None:
    mock_message_listener.listen.side_effect = MessageAlreadyListening("already listening")
    use_case = ListenNewMessagesUseCaseImpl(message_listener=mock_message_listener)

    with pytest.raises(MessageAlreadyListening):
        use_case.use(room_id=1, username="test_user")

    mock_message_listener.listen.assert_called_once_with(1, "test_user")


@pytest.mark.asyncio
async def test_listen_new_messages_repo_error(
    mock_message_listener: AsyncMock,
) -> None:
    mock_message_listener.listen.side_effect = RepoError("repo error")
    use_case = ListenNewMessagesUseCaseImpl(message_listener=mock_message_listener)

    with pytest.raises(RepoError):
        use_case.use(room_id=1, username="test_user")

    mock_message_listener.listen.assert_called_once_with(1, "test_user")