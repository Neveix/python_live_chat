import hashlib
from pathlib import Path


def hash_message(message_text: str) -> str:
    return hashlib.blake2b(message_text.encode("utf-8"), digest_size=16).hexdigest()

class ClientLogger:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("")
        self.file = open(path, mode="a", encoding="utf-8", buffering=1)

    def _append_file(self, text: str):
        self.file.write(text+"\n")

    def sent(self, message: str, sent_monotonic_ns: int):
        message_hash = hash_message(message)
        self._append_file(f"SENT {message_hash} {sent_monotonic_ns}")

    def recv(self, message: str, recv_monotonic_ns: int):
        message_hash = hash_message(message)
        self._append_file(f"RECV {message_hash} {recv_monotonic_ns}")

    def __del__(self):
        self.file.close()
