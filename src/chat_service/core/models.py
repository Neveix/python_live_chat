from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Room:
    id: int
    name: str
    creator: str


@dataclass
class UserMessage:
    text: str
    sender: str
    timestamp: datetime = field(default_factory=datetime.now)
    id: int | None = None

    @property
    def type(self) -> str:
        return "user"

    @property
    def is_persisted(self) -> bool:
        """Проверка, сохранено ли сообщение в БД"""
        return self.id is not None

    def serialize(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": self.type,
            "text": self.text,
            "sender": self.sender,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.id is not None:
            result["id"] = self.id
        return result

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "UserMessage":
        return cls(
            id=data.get("id"),
            text=data["text"],
            sender=data["sender"],
            timestamp=data["timestamp"],
        )


@dataclass
class SystemMessage:
    text: str
    timestamp: datetime = field(default_factory=datetime.now)
    id: int | None = None

    @property
    def type(self) -> str:
        return "system"

    @property
    def is_persisted(self) -> bool:
        return self.id is not None

    def serialize(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "type": self.type,
            "text": self.text,
            "timestamp": self.timestamp.isoformat(),
        }
        if self.id is not None:
            result["id"] = self.id
        return result

    @classmethod
    def deserialize(cls, data: dict[str, Any]) -> "SystemMessage":
        return cls(
            id=data.get("id"),
            text=data["text"],
            timestamp=data["timestamp"],
        )


Message = UserMessage | SystemMessage


def deserialize_message(data: dict[str, Any]) -> Message:
    if data["type"] == "user":
        return UserMessage.deserialize(data)
    elif data["type"] == "system":
        return SystemMessage.deserialize(data)
    raise ValueError(f"unknown message type: {data['type']}")


@dataclass
class RoomJoinResult:
    success: bool
    detail: str | None = None
    recent_messages: list[Message] | None = None


class InvalidRoomNameError(Exception): ...
