from fastapi import FastAPI, Request, status
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from .chat_service.core.exceptions import RepoError, RoomNotFoundError
from .api.routers.rooms import router as rooms_router
from .api.routers.messages import router as messages_router


app = FastAPI()
app.include_router(messages_router)
app.include_router(rooms_router)


class RegularExceptionInfo(BaseModel):
    error_type: str
    detail: str


@app.exception_handler(RoomNotFoundError)
async def handle_room_not_found_error(request: Request, exc: RoomNotFoundError):
    room_id = request.path_params.get("room_id")
    room_id_str = "" if room_id is None else f"{room_id} "
    detail = f"Room {room_id_str}not found"

    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=RegularExceptionInfo(
            error_type="RoomNotFoundError",
            detail=detail,
        ).model_dump(),
    )


@app.exception_handler(RepoError)
async def handle_repo_error(request: Request, exc: RepoError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content=RegularExceptionInfo(
            error_type="RepoError",
            detail="Temporary Error",
        ).model_dump(),
        headers={"Retry-After": "1"},
    )


@app.exception_handler(Exception)
async def handle_general_error(request: Request, exc: Exception):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=RegularExceptionInfo(
            error_type="InternalError",
            detail="Internal Server Error",
        ).model_dump(),
    )


@app.get("/")
async def root():
    return FileResponse("src/static/index.html")


@app.get("/src/static/app.js")
async def app_js():
    return FileResponse("src/static/app.js")
