from redis.asyncio import Redis

from ..infrastructure.business_logic.message_listener import MessageListenerImpl
from ..infrastructure.use_cases.listen_new_messages import ListenNewMessagesUseCaseImpl
from ..infrastructure.use_cases.message_send import MessageSendUseCaseImpl
from ..infrastructure.use_cases.room_create import RoomCreateUseCaseImpl
from ..infrastructure.use_cases.room_leave import RoomLeaveUseCaseImpl
from ..infrastructure.use_cases.room_join import RoomJoinUseCaseImpl
from ..infrastructure.repository.presence_repo_inmemory import PresenceRepoInMemory
from ..infrastructure.repository.rooms_repo_redis import RoomsRepoRedis
from ..infrastructure.repository.message_repo_redis import MessagesRepoRedis
from ..infrastructure.use_cases.rooms_get import RoomsGetUseCaseImpl
from ..core.interfaces import ChatService


class ChatServiceFactory:
    def __init__(self, 
        redis: Redis,
        pubsub_redis: Redis,
    ) -> None:
        self.redis = redis
        self.pubsub_redis = pubsub_redis
    
    def create(self) -> ChatService:
        message_repo = MessagesRepoRedis(self.redis, self.pubsub_redis)
        room_repo = RoomsRepoRedis(self.redis)
        presence_repo = PresenceRepoInMemory()
        message_listener = MessageListenerImpl(message_repo)
        
        return ChatService(
            get_rooms = RoomsGetUseCaseImpl(room_repo),
            join_room = RoomJoinUseCaseImpl(
                room_repo, presence_repo, message_repo,),
            leave_room = RoomLeaveUseCaseImpl(
                room_repo, message_repo, presence_repo, message_listener),
            create_room = RoomCreateUseCaseImpl(
                room_repo, message_repo),
            send_message = MessageSendUseCaseImpl(message_repo),
            listen_new_messages = ListenNewMessagesUseCaseImpl(
                message_listener),
        )