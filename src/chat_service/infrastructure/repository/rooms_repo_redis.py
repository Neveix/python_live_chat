from redis.asyncio import Redis

from ...core.exceptions import RepoElementAlreadyExists, RepoError
from ...core.models import Room
from ...core.interfaces import RoomRepo


class RoomsRepoRedis(RoomRepo):
    def __init__(self, redis: Redis):
        self.redis = redis
    
    async def get_all(self) -> list[Room]:
        try:
            room_ids = await self.redis.smembers("rooms:all")
            
            rooms: list[Room] = []
            for room_id in room_ids:
                room_id = int(room_id)
                room = await self.get_by_id(room_id)
                if room is None:
                    continue
                
                rooms.append(room)
            
            return rooms
        
        except Exception as e:
            raise RepoError() from e

    async def get_by_id(self, room_id: int) -> Room | None:
        try:
            raw_data = await self.redis.hgetall(f"room:{room_id}")
            
            if not raw_data:
                return None
            
            data: dict[str, str] = {}
            for key in ["name", "creator"]:
                candidate = raw_data[key.encode()]
                if isinstance(candidate, bytes):
                    data[key] = candidate.decode()
                else:
                    data[key] = candidate
                
            return Room(
                id=room_id,
                name=data["name"],
                creator=data["creator"]
            )
            
        except Exception as e:
            raise RepoError() from e
        
    async def get_by_name(self, room_name: str) -> Room | None:
        try:
            room_id = await self.redis.get(f"room:name:{room_name}")
            if not room_id:
                return None
            return await self.get_by_id(int(room_id))
        
        except Exception as e:
            raise RepoError() from e

    async def create(self, room_name: str, username: str, ) -> Room:
        try:
            existing = await self.get_by_name(room_name)
            if existing:
                raise RepoElementAlreadyExists(f"Room '{room_name}' already exists")

            room_id = await self.redis.incr("rooms:next_id")
            room = Room(
                id=room_id,
                name=room_name,
                creator=username,
            )
            await self.redis.hset(f"room:{room_id}", mapping={
                "name": room.name,
                "creator": room.creator
            })
            
            await self.redis.set(f"room:name:{room_name}", room_id)
            await self.redis.sadd("rooms:all", str(room_id))

            return room
        
        except RepoElementAlreadyExists:
            raise
        
        except Exception as e:
            raise RepoError() from e

    async def delete(self, room_id: int) -> bool:
        try:
            room = await self.get_by_id(room_id)
            if not room:
                return False
            
            await self.redis.delete(f"room:{room_id}")
            await self.redis.delete(f"room:name:{room.name}")  # удаляем индекс
            await self.redis.srem("rooms:all", str(room_id))
            
            return True
        
        except Exception as e:
            raise RepoError() from e