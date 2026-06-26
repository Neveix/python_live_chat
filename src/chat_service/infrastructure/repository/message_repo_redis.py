import json
from typing import AsyncGenerator

from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from redis.exceptions import ConnectionError as RedisConnectionError

from ...core.exceptions import ListenCancelled, ListenTimeoutError, RepoError
from ...core.models import Message, deserialize_message
from ...core.interfaces import MessageSubscription, MessageRepo, MessageT


class RedisMessageSubscription(MessageSubscription):
    def __init__(self, pubsub: PubSub, channel: str):
        self.pubsub = pubsub
        self.channel = channel
    
    async def close(self) -> None:
        await self.pubsub.unsubscribe(self.channel)
        await self.pubsub.close()



class MessagesRepoRedis(MessageRepo):
    def __init__(self, 
        redis: Redis,
        pubsub_redis: Redis,
    ):
        self.redis = redis
        self.pubsub_redis = pubsub_redis
        self.HISTORY_LIMIT = 100
        
    async def add(self, room_id: int, message: MessageT) -> MessageT:
        try:
            message.id = await self.redis.incr(f"message_id:{room_id}")
            message_json = json.dumps(message.serialize())

            await self.redis.lpush(f"history:{room_id}", message_json)
            await self.redis.ltrim(f"history:{room_id}", 0, self.HISTORY_LIMIT - 1)
            
            await self.redis.publish(f"room:{room_id}", message_json)
            
            return message
        
        except Exception as e:
            raise RepoError() from e
    
    async def get_recent(self, room_id: int, limit: int = 50) -> list[Message]:
        try:
            messages_json = await self.redis.lrange(f"history:{room_id}", 0, limit - 1)
            
            messages: list[Message] = []
            for message_json in reversed(messages_json):
                data = deserialize_message(json.loads(message_json))
                messages.append(data)
                
            return messages
        
        except Exception as e:
            raise RepoError() from e
            
        
    
    async def listen_new(self,
        room_id: int
    ) -> tuple[AsyncGenerator[Message, None], MessageSubscription]:
        try:
            pubsub = self.pubsub_redis.pubsub()
            channel = f"room:{room_id}"
            
            await pubsub.subscribe(channel)
            
            subscription = RedisMessageSubscription(pubsub, channel)
            
            async def generator():
                try:
                    async for data in pubsub.listen():
                        if data["type"] == "message":
                            data = deserialize_message(json.loads(data["data"]))
                            yield data
                    
                except TimeoutError as e:
                    raise ListenTimeoutError() from e
                
                except RedisConnectionError as e:
                    raise ListenCancelled() from e
                
                except Exception as e:
                    raise RepoError() from e
            
            return generator(), subscription
        
        except Exception as e:
            raise RepoError() from e