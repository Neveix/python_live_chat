import argparse
import asyncio
import json
import sys

import websockets
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout


async def listen(websocket: websockets.ClientConnection):
    try:
        async for message in websocket:
            data = json.loads(message)
            kind = data.get("kind")

            if kind == "history":
                print(f"\n📜 History ({len(data['messages'])} messages):")
                for msg in data["messages"][-5:]:  # Последние 5
                    if msg["type"] == "system":
                        print(f"  [SYSTEM] {msg['text']}")
                    else:
                        print(
                            f"  {msg.get('sender', 'system')}: {msg['text']}"
                        )

            elif kind == "message":
                msg = data
                if msg["type"] == "system":
                    print(f"  [SYSTEM] {msg['text']}")
                else:
                    print(f"  {msg.get('sender', 'system')}: {msg['text']}")

            elif kind == "error":
                print(f"\n❌ Error [{data['error_type']}]: {data['detail']}")
                return

    except websockets.exceptions.ConnectionClosed:
        print("\n🔌 Connection closed")

    finally:
        pass


async def send_messages(websocket: websockets.ClientConnection):
    prompt_session = PromptSession()
    try:
        while True:
            with patch_stdout():
                text: str = await prompt_session.prompt_async(
                    "\n✏️  Message (or 'quit' to exit): "
                )
            if text.lower() == "quit":
                break

            if text.strip():
                await websocket.send(json.dumps({"text": text}))
                print(f"📤 Sent: {text}")

    except asyncio.CancelledError:
        print("\n👋 Cancelling prompt session...")

    except KeyboardInterrupt:
        print("\n👋 Disconnecting...")


async def test_chat_client(room_id: int, username: str, port: int):
    uri = f"ws://localhost:{port}/ws/messages/{room_id}/{username}"
    print(f"Connecting to {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            listen_task = asyncio.create_task(listen(websocket))

            await asyncio.sleep(2)
            send_messages_task = asyncio.create_task(send_messages(websocket))

            try:
                _, pending = await asyncio.wait(
                    [
                        send_messages_task,
                        listen_task,
                    ],
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for task in pending:
                    task.cancel()
            finally:
                await websocket.close()

    except websockets.exceptions.WebSocketException as e:
        print(f"❌ Connection failed: {e}")

    except ConnectionRefusedError:
        print(f"❌ Server not running on localhost:{port}")


async def main():
    parser = argparse.ArgumentParser(
        "Console client",
        usage="console_client --name <your name>",
    )
    parser.add_argument("--port", "-p", type=int, default=47116)
    parser.add_argument("--room", "-r", type=int, default=1)
    parser.add_argument("--name", "-n", type=str, default=None)
    parsed = parser.parse_args()
    if not parsed.name:
        print("error: pass your name with --name <your name>")
        sys.exit(1)
    name: str = parsed.name
    room: int = parsed.room
    port: int = parsed.port

    await test_chat_client(room, name, port)


if __name__ == "__main__":
    asyncio.run(main())
