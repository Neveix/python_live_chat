from abc import ABC, abstractmethod
import hashlib
from pathlib import Path


def hash_message(message_text: str) -> str:
    return hashlib.blake2b(message_text.encode("utf-8"), digest_size=16).hexdigest()

class MessageLogger(ABC):
    @abstractmethod
    def sent(self, message: str, monotonic_ns: int) -> None: ...

    @abstractmethod
    def recv(self, message: str, monotonic_ns: int) -> None: ...

    @abstractmethod
    def srv_recv(self, message: str, monotonic_ns: int) -> None: ...

class MessageLoggerBypass(MessageLogger):
    def sent(self, message: str, monotonic_ns: int) -> None: ...

    def recv(self, message: str, monotonic_ns: int) -> None: ...

    def srv_recv(self, message: str, monotonic_ns: int) -> None: ...


class MessageLoggerImpl(MessageLogger):
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
        self.file = open(path, mode="a", encoding="utf-8", buffering=1)

    def _append_file(self, text: str):
        self.file.write(text+"\n")

    def sent(self, message: str, monotonic_ns: int):
        message_hash = hash_message(message)
        self._append_file(f"SENT {message_hash} {monotonic_ns}")

    def recv(self, message: str, monotonic_ns: int):
        message_hash = hash_message(message)
        self._append_file(f"RECV {message_hash} {monotonic_ns}")

    def srv_recv(self, message: str, monotonic_ns: int):
        message_hash = hash_message(message)
        self._append_file(f"SRV_RECV {message_hash} {monotonic_ns}")

    def __del__(self):
        self.file.close()
