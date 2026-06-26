import asyncio
import traceback
from typing import AsyncGenerator

from ...core.exceptions import ListenCancelled, ListenTimeoutError, MessageAlreadyListening, RepoError
from ...core.models import Message
from ...core.interfaces import MessageListener, MessageSubscription, MessageRepo

class MessageListenerImpl(MessageListener):
    def __init__(self, 
        message_repo: MessageRepo,
    ):
        self.message_repo = message_repo
        self.generators: dict[int, AsyncGenerator[Message, None]] = {}
        self.closers: dict[int, MessageSubscription] = {}
        self.message_queues_by_room: dict[int, dict[str, asyncio.Queue[Message | None]]] = {}

    async def listen(self,
        room_id: int, 
        username: str,
    ) -> AsyncGenerator[Message, None]: 
        if (room_id in self.message_queues_by_room and \
            username in self.message_queues_by_room[room_id]):
            raise MessageAlreadyListening(f"{room_id=} {username=}")
        
        if room_id not in self.generators:
            gen, sub = await self.message_repo.listen_new(room_id)
            self.generators[room_id] = gen
            self.closers[room_id] = sub
            self.message_queues_by_room[room_id] = {}
            
            asyncio.create_task(self._distribute_messages(gen, room_id))
        
        self.message_queues_by_room[room_id][username] = asyncio.Queue()
            
        try:
            while True:
                value = await self.message_queues_by_room[room_id][username].get()
                if value is None:
                    break
                yield value
            
        finally:
            del self.message_queues_by_room[room_id][username]
            if not self.message_queues_by_room[room_id]:
                await self.closers[room_id].close()
                del self.generators[room_id]
                del self.closers[room_id]
                del self.message_queues_by_room[room_id]
        
        
    async def _distribute_messages(self, gen: AsyncGenerator[Message, None], room_id: int):
        async def signal_all(data: Message | None = None):
            message_queues = self.message_queues_by_room.get(room_id, {})
            for queue in message_queues.values():
                await queue.put(data)
        
        try:
            async for message in gen:
                await signal_all(message)
        
        except ListenCancelled:
            pass
         
        except ListenTimeoutError:
            tb = traceback.format_exc()
            print(f"Timeout in room {room_id}, closing subscription, traceback:\n{tb}")
            
        except RepoError as e:
            tb = traceback.format_exc()
            print(f"RepoError in room {room_id}: {e!r}, closing subscription, traceback:\n{tb}")
        
        except Exception as e:
            tb = traceback.format_exc()
            print(f"exception {e!r} caught, traceback:\n{tb}")
        
        finally:
            await signal_all(None)
        
        

    async def break_listen(self, room_id: int, username: str) -> bool:
        if room_id not in self.message_queues_by_room:
            return False
        
        if username not in self.message_queues_by_room[room_id]:
            return False
        
        await self.message_queues_by_room[room_id][username].put(None)
        return True