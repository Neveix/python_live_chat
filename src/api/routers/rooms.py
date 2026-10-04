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


# class JoinRoomResponse(BaseModel):
#     success: bool
#     detail: str | None = None
#     recent_messages: list[Message] | None = None


# @router.post("/{room_id}/users/{username}")
# async def join_room(
#     room_id: int,
#     username: str,
#     chat_service: ChatService = Depends(get_chat_service),
# ) -> JoinRoomResponse:
#     result = await chat_service.join_room.use(room_id, username)
#     return JoinRoomResponse(
#         success=result.success,
#         detail=result.detail,
#         recent_messages=result.recent_messages,
#     )


# class LeaveRoomResult(BaseModel):
#     success: bool
#     detail: str | None = None

# @router.delete("/{room_id}/users/{username}")
# async def leave_room(
#     room_id: int,
#     username: str,
#     chat_service: ChatService = Depends(get_chat_service),
# ):
#     success = await chat_service.leave_room.use(room_id, username)
#     if success:
#         return LeaveRoomResult(
#             success=success,
#             detail=None,
#         )
#     else:
#         return LeaveRoomResult(
#             success=success,
#             detail="User is no longer in the room"
#         )
