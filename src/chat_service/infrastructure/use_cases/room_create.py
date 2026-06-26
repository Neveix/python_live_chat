from ...core.models import InvalidRoomNameError, Room, SystemMessage
from ...core.interfaces import MessageRepo, RoomCreateUseCase, RoomRepo


class RoomCreateUseCaseImpl(RoomCreateUseCase):
    def __init__(
        self,
        rooms_repo: RoomRepo,
        messages_repo: MessageRepo,
    ):
        self.rooms_repo = rooms_repo
        self.messages_repo = messages_repo

    async def use(
        self,
        room_name: str,
        username: str,
    ) -> Room:
        if not room_name or len(room_name) > 30:
            raise InvalidRoomNameError("Room name is out of bounds")

        if all([c.isspace() for c in room_name]):
            raise InvalidRoomNameError("all chars are invisible")

        # Создаём комнату
        room = await self.rooms_repo.create(room_name, username)
        # Создаём сообщение о создании
        await self.messages_repo.add(
            room.id, SystemMessage(f"Room {room_name} created")
        )

        return room

