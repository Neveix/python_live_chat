import asyncio
import json
import websockets
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout
from datetime import datetime

async def test_chat_client():
    room_id = 1
    username = input("Prompt your name:")
    uri = f"ws://localhost:47116/ws/messages/{room_id}/{username}"
    
    print(f"Connecting to {uri}...")
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected!")
            
            # Задача: слушать входящие сообщения
            async def listen():
                try:
                    async for message in websocket:
                        data = json.loads(message)
                        kind = data.get("kind")
                        
                        if kind == "history":
                            print(f"\n📜 History ({len(data['messages'])} messages):")
                            for msg in data["messages"][-5:]:  # Последние 5
                                if msg['type'] == "system":
                                    print(f"  [SYSTEM] {msg['text']}")
                                else:
                                    print(f"  {msg.get('sender', 'system')}: {msg['text']}")
                        
                        elif kind == "message":
                            msg = data
                            if msg['type'] == "system":
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
            
            # Отправляем сообщения
            async def send_messages():
                prompt_session = PromptSession()
                try:
                    while True:
                        with patch_stdout():
                            text: str = await prompt_session.prompt_async(
                                "\n✏️  Message (or 'quit' to exit): ")
                        if text.lower() == 'quit':
                            break
                        
                        if text.strip():
                            await websocket.send(json.dumps({"text": text}))
                            print(f"📤 Sent: {text}")
                        
                except asyncio.CancelledError:
                    print("\n👋 Cancelling prompt session...")
                        
                except KeyboardInterrupt:
                    print("\n👋 Disconnecting...")
            
            send_messages_task = asyncio.create_task(send_messages())
            listen_task = asyncio.create_task(listen())
            
            try:
                _, pending = await asyncio.wait(
                    [
                        send_messages_task, 
                        listen_task,
                    ], 
                    return_when=asyncio.FIRST_COMPLETED
                )
                for task in pending:
                    task.cancel()
            finally:
                await websocket.close()
                
    except websockets.exceptions.WebSocketException as e:
        print(f"❌ Connection failed: {e}")
        
    except ConnectionRefusedError:
        print("❌ Server not running on localhost:8000")

if __name__ == "__main__":
    asyncio.run(test_chat_client())