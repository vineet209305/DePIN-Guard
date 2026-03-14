from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()
active_connections = []

@router.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)

# Helper function to broadcast data to all connected users
async def broadcast_data(data: dict):
    for connection in active_connections:
        await connection.send_json(data)
