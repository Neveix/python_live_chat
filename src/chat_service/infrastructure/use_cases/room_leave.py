from ...core.exceptions import RoomNotFoundError
from ...core.models import SystemMessage
from ...core.interfaces import MessageListener, MessageRepo, PresenceRepo, RoomLeaveUseCase, RoomRepo


class RoomLeaveUseCaseImpl(RoomLeaveUseCase):
    def __init__(self,
        room_repo: RoomRepo,
        message_repo: MessageRepo,
        presence_repo: PresenceRepo,
        message_listener: MessageListener,
    ) -> None:
        self.room_repo = room_repo
        self.messages_repo = message_repo
        self.presence_repo = presence_repo
        self.message_listener = message_listener
    
    async def use(self, room_id: int, username: str, ) -> bool:
        if await self.room_repo.get_by_id(room_id) is None:
            raise RoomNotFoundError()
        
        success = await self.presence_repo.remove(room_id, username)
        if success == False:
            return False
        
        await self.messages_repo.add(room_id, SystemMessage(f"{username} left"))
        await self.message_listener.break_listen(room_id, username)
        
        return True