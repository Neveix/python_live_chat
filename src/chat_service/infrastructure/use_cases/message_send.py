from ...core.models import UserMessage
from ...core.interfaces import MessageSendUseCase, MessageRepo


class MessageSendUseCaseImpl(MessageSendUseCase):
    def __init__(self,
        messages_repo: MessageRepo
    ):
        self.messages_repo = messages_repo
    
    async def use(self, room_id: int, username: str, text: str, ) -> None:
        await self.messages_repo.add(room_id, 
            UserMessage(text, username))