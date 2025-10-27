#!/usr/bin/env python3
"""
Test WebSocket connection to verify endpoint is accessible
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:5000/ws/executions?api_key=dev-key-change-in-production"

    print(f"Attempting to connect to: {uri}")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection successful!")

            # Wait for initial message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"📨 Received initial message: {message}")
            except asyncio.TimeoutError:
                print("⏱️  No initial message received (this is OK)")

            # Try sending a message
            test_message = {"type": "ping", "message": "test"}
            await websocket.send(json.dumps(test_message))
            print(f"📤 Sent test message: {test_message}")

            # Wait for response
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"📨 Received response: {response}")
            except asyncio.TimeoutError:
                print("⏱️  No response received (this is OK)")

            print("\n✅ WebSocket endpoint is accessible and working!")

    except ConnectionRefusedError:
        print("❌ Connection refused - is the server running?")
    except Exception as e:
        print(f"❌ Error connecting to WebSocket: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
