import traceback

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ...chat_service.core.models import InvalidRoomNameError
from ...chat_service.core.exceptions import RepoElementAlreadyExists
from ...chat_service.core.interfaces import ChatService
from ..dependencies import get_chat_service


router = APIRouter(prefix="/api/rooms")


class Room(BaseModel):
    id: int
    name: str
    creator: str


class GetRoomsResponse(BaseModel):
    rooms: list[Room]


depends_get_chat_service = Depends(get_chat_service)


@router.get("", response_model=GetRoomsResponse)
async def get_rooms(
    chat_service: ChatService = depends_get_chat_service,
) -> GetRoomsResponse:
    rooms = await chat_service.get_rooms.use()
    return GetRoomsResponse(
        rooms=[
            Room(
                id=room.id,
                name=room.name,
                creator=room.creator,
            )
            for room in rooms
        ]
    )


class CreateRoomRequest(BaseModel):
    room_name: str
    username: str


class CreateRoomResponse(BaseModel):
    success: bool
    detail: str | None = None
    room: Room | None = None


@router.post("")
async def create_room(
    request: CreateRoomRequest,
    chat_service: ChatService = depends_get_chat_service,
) -> CreateRoomResponse:
    try:
        room = await chat_service.create_room.use(request.room_name, request.username)
        return CreateRoomResponse(
            success=True,
            room=Room(
                id=room.id,
                name=room.name,
                creator=room.creator,
            ),
        )

    except InvalidRoomNameError as e:
        return CreateRoomResponse(success=False, detail=f"Invalid room name. {e!s}")

    except RepoElementAlreadyExists:
        return CreateRoomResponse(
            success=False,
            detail="Room already exists",
        )

    except Exception as e:
        traceback.print_exc()
        raise
