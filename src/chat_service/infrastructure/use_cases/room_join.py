from ...core.exceptions import RepoError, RoomNotFoundError
from ...core.models import RoomJoinResult, SystemMessage
from ...core.interfaces import MessageRepo, PresenceRepo, RoomJoinUseCase, RoomRepo



class RoomJoinUseCaseImpl(RoomJoinUseCase):
    def __init__(self, 
        room_repo: RoomRepo,
        presence_repo: PresenceRepo,
        message_repo: MessageRepo,
    ):
        self.room_repo = room_repo
        self.presence_repo = presence_repo
        self.message_repo = message_repo

    async def use(self, room_id: int, username: str, ) -> RoomJoinResult:
        room = await self.room_repo.get_by_id(room_id)
        if room is None:
            raise RoomNotFoundError()
        
        success = await self.presence_repo.add(room_id, username)
        if success == False:
            return RoomJoinResult(False, detail="The user is already in the room")
        
        try:
            await self.message_repo.add(room_id, SystemMessage(f"{username} joined"))
            
        except RepoError:
            await self.presence_repo.remove(room_id, username)
            raise
        
        recent_messages = await self.message_repo.get_recent(room_id)
        return RoomJoinResult(True, recent_messages=recent_messages)