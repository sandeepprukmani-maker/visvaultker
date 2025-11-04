"""
WebSocket Service for Real-time Execution Monitoring
Provides live progress updates, browser previews, and logs
"""

from typing import Dict, Set
import json
import asyncio
from datetime import datetime

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, Set] = {}
        self.execution_states: Dict[str, Dict] = {}
    
    async def connect(self, websocket, execution_id: str):
        """Register a WebSocket connection for an execution"""
        if execution_id not in self.connections:
            self.connections[execution_id] = set()
        
        self.connections[execution_id].add(websocket)
        
        # Send current state if execution is in progress
        if execution_id in self.execution_states:
            await websocket.send_json(self.execution_states[execution_id])
    
    async def disconnect(self, websocket, execution_id: str):
        """Remove a WebSocket connection"""
        if execution_id in self.connections:
            self.connections[execution_id].discard(websocket)
            
            if len(self.connections[execution_id]) == 0:
                del self.connections[execution_id]
    
    async def broadcast_progress(
        self,
        execution_id: str,
        event_type: str,
        data: Dict
    ):
        """Broadcast progress update to all connected clients"""
        
        message = {
            'execution_id': execution_id,
            'event_type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Store current state
        self.execution_states[execution_id] = message
        
        # Broadcast to all connections
        if execution_id in self.connections:
            disconnected = set()
            
            for websocket in self.connections[execution_id]:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    print(f"Error sending to websocket: {e}")
                    disconnected.add(websocket)
            
            # Remove disconnected websockets
            for ws in disconnected:
                self.connections[execution_id].discard(ws)
    
    async def send_log(self, execution_id: str, log_message: str):
        """Send log message"""
        await self.broadcast_progress(
            execution_id,
            'log',
            {'message': log_message}
        )
    
    async def send_screenshot(self, execution_id: str, screenshot_path: str):
        """Send screenshot update"""
        await self.broadcast_progress(
            execution_id,
            'screenshot',
            {'path': screenshot_path}
        )
    
    async def send_status_update(
        self,
        execution_id: str,
        status: str,
        current_step: int = None,
        total_steps: int = None
    ):
        """Send status update"""
        await self.broadcast_progress(
            execution_id,
            'status',
            {
                'status': status,
                'current_step': current_step,
                'total_steps': total_steps
            }
        )
    
    async def send_completion(
        self,
        execution_id: str,
        result: Dict
    ):
        """Send execution completion"""
        await self.broadcast_progress(
            execution_id,
            'completed',
            result
        )
        
        # Clean up state after some time
        await asyncio.sleep(300)  # 5 minutes
        if execution_id in self.execution_states:
            del self.execution_states[execution_id]


websocket_manager = WebSocketManager()
