from ...core.models import Room
from ...core.interfaces import RoomsGetUseCase, RoomRepo


class RoomsGetUseCaseImpl(RoomsGetUseCase):
    def __init__(self, repo: RoomRepo):
        self.repo = repo

    async def use(self) -> list[Room]:
        return await self.repo.get_all()

