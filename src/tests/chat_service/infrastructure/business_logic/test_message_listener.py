import asyncio
from typing import AsyncGenerator, AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from chat_service.core.exceptions import MessageAlreadyListening
from chat_service.core.interfaces import MessageListener, MessageSubscription, MessageRepo
from chat_service.core.models import Message, SystemMessage, UserMessage
from chat_service.infrastructure.business_logic.message_listener import MessageListenerImpl


@pytest.fixture
def mock_messages_repo() -> AsyncMock:
    repo = AsyncMock(spec=MessageRepo)
    return repo


@pytest.fixture
def listener(mock_messages_repo: AsyncMock) -> MessageListenerImpl:
    return MessageListenerImpl(message_repo=mock_messages_repo)


async def wait_for_messages(gen: AsyncGenerator[Message, None]) -> list[Message]:
    messages = []
    async for msg in gen:
        messages.append(msg)
    return messages


class TestMessageListenerImpl:
    @pytest.mark.asyncio()
    async def test_listen_new_room(self, listener: MessageListenerImpl, mock_messages_repo: AsyncMock) -> None:
        async def message_generator() -> AsyncGenerator[Message, None]:
            yield UserMessage(text="hello", sender="user1", id=1)

        mock_subscription = AsyncMock(spec=MessageSubscription)
        mock_messages_repo.listen_new.return_value = (message_generator(), mock_subscription)

        gen = listener.listen(room_id=1, username="user1")
        assert isinstance(gen, AsyncIterator)

        messages = [msg async for msg in gen]
        assert len(messages) == 1
        assert messages[0].text == "hello"
        mock_messages_repo.listen_new.assert_awaited_once_with(1)

    @pytest.mark.asyncio()
    async def test_listen_existing_room(self, listener: MessageListenerImpl, mock_messages_repo: AsyncMock) -> None:
        async def message_generator() -> AsyncGenerator[Message, None]:
            yield UserMessage(text="hello", sender="user1", id=1)

        mock_subscription = AsyncMock(spec=MessageSubscription)
        mock_messages_repo.listen_new.return_value = (message_generator(), mock_subscription)

        gen1 = listener.listen(room_id=1, username="user1")
        gen2 = listener.listen(room_id=1, username="user2")
        
        results = await asyncio.gather(*[
            wait_for_messages(gen1),
            wait_for_messages(gen2)
        ])
        messages1 = results[0]
        messages2 = results[1]
        
        mock_messages_repo.listen_new.assert_awaited_once_with(1)
        assert len(messages1) == 1
        assert len(messages2) == 1

    @pytest.mark.asyncio()
    async def test_listen_already_listening(self, listener: MessageListenerImpl, mock_messages_repo: AsyncMock) -> None:
        async def message_generator() -> AsyncGenerator[Message, None]:
            yield UserMessage(text="hello", sender="user1", id=1)

        mock_subscription = AsyncMock(spec=MessageSubscription)
        mock_messages_repo.listen_new.return_value = (message_generator(), mock_subscription)

        gen1 = listener.listen(room_id=1, username="user1")
        gen2 = listener.listen(room_id=1, username="user1")

        with pytest.raises(MessageAlreadyListening):
            results = await asyncio.gather(*[
                wait_for_messages(gen1),
                wait_for_messages(gen2)
            ])

    @pytest.mark.asyncio()
    async def test_break_listen_success(self, listener: MessageListenerImpl, mock_messages_repo: AsyncMock) -> None:
        async def message_generator() -> AsyncGenerator[Message, None]:
            yield UserMessage(text="hello", sender="user1", id=1)

        mock_subscription = AsyncMock(spec=MessageSubscription)
        mock_messages_repo.listen_new.return_value = (message_generator(), mock_subscription)

        gen = listener.listen(room_id=1, username="user1")
        
        results = await asyncio.gather(*[
            wait_for_messages(gen),
            listener.break_listen(room_id=1, username="user1"),
        ])
        
        assert len(results[0]) == 0
        assert results[1] is True

    @pytest.mark.asyncio()
    async def test_break_listen_not_listening(self, listener: MessageListenerImpl, mock_messages_repo: AsyncMock) -> None:
        result = await listener.break_listen(room_id=1, username="nonexistent")
        assert result is False

    @pytest.mark.asyncio()
    async def test_message_distribution(self, listener: MessageListenerImpl, mock_messages_repo: AsyncMock) -> None:
        async def message_generator() -> AsyncGenerator[Message, None]:
            yield UserMessage(text="msg1", sender="user1", id=1)
            yield UserMessage(text="msg2", sender="user2", id=2)

        mock_subscription = AsyncMock(spec=MessageSubscription)
        mock_messages_repo.listen_new.return_value = (message_generator(), mock_subscription)

        gen1 = listener.listen(room_id=1, username="user1")
        gen2 = listener.listen(room_id=1, username="user2")

        results = await asyncio.gather(*[
            wait_for_messages(gen1),
            wait_for_messages(gen2)
        ])
        
        messages1 = results[0]
        messages2 = results[1]

        assert len(messages1) == 2
        assert len(messages2) == 2
        assert messages1[0].text == "msg1"
        assert messages1[1].text == "msg2"
        assert messages2[0].text == "msg1"
        assert messages2[1].text == "msg2"

    @pytest.mark.asyncio()
    async def test_listener_disconnect(self, listener: MessageListenerImpl, mock_messages_repo: AsyncMock) -> None:
        async def message_generator() -> AsyncGenerator[Message, None]:
            yield UserMessage(text="msg1", sender="user1", id=1)

        mock_subscription = AsyncMock(spec=MessageSubscription)
        mock_messages_repo.listen_new.return_value = (message_generator(), mock_subscription)

        gen = listener.listen(room_id=1, username="user1")

        messages = [msg async for msg in gen]
        assert len(messages) == 1

        assert 1 not in listener.generators
        assert 1 not in listener.closers
        assert 1 not in listener.message_queues_by_room
        mock_subscription.close.assert_awaited_once()