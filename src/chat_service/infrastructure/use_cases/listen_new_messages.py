from typing import AsyncGenerator

from ...core.models import Message
from ...core.interfaces import ListenNewMessagesUseCase, MessageListener


class ListenNewMessagesUseCaseImpl(ListenNewMessagesUseCase):
    def __init__(self,
        message_listener: MessageListener,
    ):
        self.message_listener = message_listener
    
    def use(self, room_id: int, username: str, ) -> AsyncGenerator[Message, None]:
        return self.message_listener.listen(room_id, username)