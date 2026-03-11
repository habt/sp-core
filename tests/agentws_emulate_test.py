# client.py
import asyncio
import websockets
import time
import json
import time

SEND_TIMER = 100

COMMANDS = [
    {"message": "new_recommendation", "timestamp": time.time()},
    {"message": "change_update_timer", "value": 20, "timestamp": time.time()},
]
async def connect_and_send():
    uri = "ws://172.22.231.71:6400/corews" 
    try:

        # Connect to WebSocket server
        async with websockets.connect(uri) as websocket:
            
            print("Connected to server")
            send_time = time.time()

            data = COMMANDS[0]
            message = json.dumps(data)
            await websocket.send(message)
            
            while True:
                if time.time() - send_time > SEND_TIMER:
                    
                    data = COMMANDS[0]
                    message = json.dumps(data)
                    
                    print(f"Sending recommendation request to server: {message}")
                    await websocket.send(message)
                    
                    send_time = time.time()
                
                print("Waiting to receive recommendation from server...")
                response = await websocket.recv()
                print(f"Received from server: {response}")

    except websockets.exceptions.ConnectionClosed:
        print("Connection closed")
    
    except Exception as e:
        print(f"Error: {e}")

# Run the client
asyncio.run(connect_and_send())