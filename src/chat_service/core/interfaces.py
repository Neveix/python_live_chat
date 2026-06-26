from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import AsyncGenerator, Protocol, TypeVar

from .models import Message, Room, RoomJoinResult


# ------------------------- Use Cases --------------------------- #

class RoomsGetUseCase(ABC):
    @abstractmethod
    async def use(self) -> list[Room]:
        """
        :raises RepoError:
        """
        # Просто проксируем ответ из репозитория
        ...

class RoomJoinUseCase(ABC):
    @abstractmethod
    async def use(self, room_id: int, username: str, ) -> RoomJoinResult:
        """
        :raises RoomNotFoundError:
        :raises RepoError:
        """
        # Добавляем пользователя в presence
        # Создаём сообщение о новом входе
        ...

class RoomLeaveUseCase(ABC):
    @abstractmethod
    async def use(self, room_id: int, username: str, ) -> bool:
        """
        :raises RoomNotFoundError:
        :raises RepoError:
        """
        # Создаём сообщение о выходе
        # Удаляем из presense
        # Разрываем listen
        ...

class RoomCreateUseCase(ABC):
    @abstractmethod
    async def use(self, room_name: str, username: str, ) -> Room:
        """
        :raises RepoElementAlreadyExists:
        :raises RepoError:
        """
        # Создаём комнату
        # Создаём сообщение о создании
        ...
        
class MessageSendUseCase(ABC):
    @abstractmethod
    async def use(self, room_id: int, username: str, text: str, ) -> None:
        """
        :raises RepoError:
        """
        # Создаём новое сообщение
        ...

class ListenNewMessagesUseCase(ABC):
    @abstractmethod
    def use(self, room_id: int, username: str, ) -> AsyncGenerator[Message, None]:
        """
        :raises MessageAlreadyListening:
        :raises RepoError:
        """
        # Проксируем генератор новых сообщений.
        ...


@dataclass
class ChatService:
    get_rooms: RoomsGetUseCase
    join_room: RoomJoinUseCase
    leave_room: RoomLeaveUseCase
    create_room: RoomCreateUseCase
    send_message: MessageSendUseCase
    listen_new_messages: ListenNewMessagesUseCase

# ------------------------- Business-Logic --------------------------- #


class MessageListener(ABC):
    @abstractmethod
    def listen(self, room_id: int, username: str) -> AsyncGenerator[Message, None]:
        """
        :raises MessageAlreadyListening:
        :raises RepoError:
        """
        ...
        
    @abstractmethod
    async def break_listen(self, room_id: int, username: str) -> bool:
        """
        :raises RepoError:
        """
        ...


# -------------------------  Repositories  --------------------------- #

class RoomRepo(ABC):
    @abstractmethod
    async def get_all(self) -> list[Room]:
        """
        :raises RepoError:
        """
        ...

    @abstractmethod
    async def get_by_id(self, room_id: int) -> Room | None:
        """
        :raises RepoError:
        """
        ...

    @abstractmethod
    async def get_by_name(self, room_name: str) -> Room | None:
        """
        :raises RepoError:
        """
        ...

    @abstractmethod
    async def create(self, room_name: str, username: str, ) -> Room:
        """
        :raises RepoElementAlreadyExists:
        :raises RepoError:
        """
        ...

    @abstractmethod
    async def delete(self, room_id: int) -> bool:
        """
        :raises RepoError:
        """
        ...


MessageT = TypeVar("MessageT", bound=Message)


class MessageSubscription(Protocol):
    async def close(self) -> None: ...


class MessageRepo(ABC):
    @abstractmethod
    async def add(self, room_id: int, message: MessageT) -> MessageT:
        """
        :raises RepoError:
        """
        ...
    
    @abstractmethod
    async def get_recent(self, room_id: int, limit: int = 50) -> list[Message]:
        """
        :raises RepoError:
        """
        ...
    
    @abstractmethod
    async def listen_new(self, room_id: int) -> tuple[AsyncGenerator[Message, None], MessageSubscription]:
        """
        Async Generator can raise ListenTimeoutError, RepoError
        
        :raises RepoError:
        """
        ...

 
class PresenceRepo(ABC):
    @abstractmethod
    async def add(self, room_id: int, username: str) -> bool:
        """
        :raises RepoError:
        """
        ...
    
    @abstractmethod
    async def remove(self, room_id: int, username: str) -> bool:
        """
        :raises RepoError:
        """
        ...
    
    @abstractmethod
    async def get_all(self, room_id: int) -> list[str]:
        """
        :raises RepoError:
        """
        ...
    
