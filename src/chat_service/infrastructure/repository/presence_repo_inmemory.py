from ...core.interfaces import PresenceRepo


class PresenceRepoInMemory(PresenceRepo):
    def __init__(self):
        self.data: set[tuple[int, str]] = set()
    
    async def add(self, room_id: int, username: str) -> bool:
        element = (room_id, username)
        if element in self.data:
            return False
        
        self.data.add(element)
        return True
    
    async def remove(self, room_id: int, username: str) -> bool:
        element = (room_id, username)
        if element not in self.data:
            return False
        
        self.data.remove(element)
        return True
    
    async def get_all(self, room_id: int) -> list[str]:
        return [
            username 
            for room_id_iter, username in self.data 
            if room_id_iter == room_id
        ]
    
