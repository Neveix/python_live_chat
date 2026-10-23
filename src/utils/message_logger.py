from abc import ABC, abstractmethod
import asyncio
import hashlib
from pathlib import Path
import queue
import threading


def hash_message(message_text: str) -> str:
    return hashlib.blake2b(message_text.encode("utf-8"), digest_size=16).hexdigest()

class MessageLogger(ABC):
    @abstractmethod
    def sent(self, message: str, monotonic_ns: int) -> None: ...

    @abstractmethod
    def recv(self, message: str, monotonic_ns: int) -> None: ...

    @abstractmethod
    def srv_recv(self, message: str, monotonic_ns: int) -> None: ...

    @abstractmethod
    def close(self) -> None: ...

class MessageLoggerBypass(MessageLogger):
    def sent(self, message: str, monotonic_ns: int) -> None: ...

    def recv(self, message: str, monotonic_ns: int) -> None: ...

    def srv_recv(self, message: str, monotonic_ns: int) -> None: ...

    def close(self) -> None: ...


class MessageLoggerImpl(MessageLogger):
    _STOP = object()  # sentinel для остановки потока

    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
        self.path = path
        self.queue: queue.Queue[str | object] = queue.Queue()
        self._thread = threading.Thread(
            target=self._writer_loop,
            name="MessageLoggerWriter",
            daemon=True,
        )
        self._thread.start()

    def _writer_loop(self) -> None:
        f = open(self.path, "a", encoding="utf-8", buffering=1)
        try:
            while True:
                item = self.queue.get()
                try:
                    if item is self._STOP:
                        return
                    f.write(item + "\n")  # type: ignore[arg-type]
                finally:
                    self.queue.task_done()
        finally:
            f.close()

    def _enqueue(self, line: str) -> None:
        self.queue.put_nowait(line)

    def sent(self, message: str, monotonic_ns: int) -> None:
        self._enqueue(f"SENT {hash_message(message)} {monotonic_ns}")

    def recv(self, message: str, monotonic_ns: int) -> None:
        self._enqueue(f"RECV {hash_message(message)} {monotonic_ns}")

    def srv_recv(self, message: str, monotonic_ns: int) -> None:
        self._enqueue(f"SRV_RECV {hash_message(message)} {monotonic_ns}")

    def close(self) -> None:
        self.queue.put(self._STOP)
        self._thread.join(timeout=5.0)
