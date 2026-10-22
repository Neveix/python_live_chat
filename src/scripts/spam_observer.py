import argparse
import asyncio
import json
from pathlib import Path
import time

import websockets
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from ..utils.message_logger import MessageLogger, MessageLoggerImpl


async def run_observer(*,
        port: int,
        room_id: int,
        username: str,
        logger: MessageLogger,
    ):
    uri = f"ws://localhost:{port}/ws/messages/{room_id}/{username}"
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")

            async def listen():
                try:
                    async for message in websocket:
                        recv_monotonic_ns = time.monotonic_ns()
                        data = json.loads(message)
                        kind = data.get("kind")

                        if kind == "message":
                            msg = data
                            if msg["type"] != "system":
                                logger.recv(msg["text"], recv_monotonic_ns)
                                print(f"received user message {msg["text"]}")

                except websockets.exceptions.ConnectionClosed:
                    print("\n🔌 Connection closed")

                except asyncio.CancelledError:
                    pass

            await listen()

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ Connection failed: {e}")

    except ConnectionRefusedError:
        print(f"❌ Server not running on localhost:{port}")

parser = argparse.ArgumentParser()
parser.add_argument("--run-id", "-i", type=int, default=1, dest="run_id")
parser.add_argument("--port", "-p", type=int, default=47116)
parser.add_argument("--room", "-r", type=int, default=None)
parsed = parser.parse_args()
program_name = parser.prog

if parsed.room is None:
    print(f"room id expected. Pass it with `{program_name} --room <id>`")
    exit(1)
    
run_id: int = parsed.run_id
room_id: int = parsed.room
port: int = parsed.port


if __name__ == "__main__":
    asyncio.run(run_observer(
        port = port,
        room_id = room_id,
        username = "spam_observer",
        logger=MessageLoggerImpl(Path("log") / f"spam_bots-{run_id}.txt")
    ))


