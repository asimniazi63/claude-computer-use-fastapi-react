"""
WebSocket connection manager for real-time communication
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any
from fastapi import WebSocket
import logging

logger = logging.getLogger(__name__)


class DateTimeJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class WebSocketManager:
    def __init__(self):
        # Dictionary mapping session_id to list of WebSocket connections
        self.connections: Dict[str, List[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, session_id: str):
        """Accept a new WebSocket connection for a session"""
        await websocket.accept()
        
        if session_id not in self.connections:
            self.connections[session_id] = []
        
        self.connections[session_id].append(websocket)
        logger.info(f"WebSocket connected for session {session_id}. Total connections: {len(self.connections[session_id])}")
        
    def disconnect(self, websocket: WebSocket, session_id: str):
        """Remove a WebSocket connection"""
        if session_id in self.connections:
            try:
                self.connections[session_id].remove(websocket)
                logger.info(f"WebSocket disconnected for session {session_id}. Remaining connections: {len(self.connections[session_id])}")
                
                # Clean up empty session lists
                if not self.connections[session_id]:
                    del self.connections[session_id]
                    
            except ValueError:
                # WebSocket not in list
                pass
    
    async def send_to_connection(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket connection"""
        try:
            print(f"🟨 Sending the message to the WebSocket is: {message}")
            await websocket.send_text(json.dumps(message, cls=DateTimeJSONEncoder))
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            
    async def broadcast_to_session(self, session_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections for a session"""
        if session_id not in self.connections:
            logger.warning(f"No WebSocket connections for session {session_id}")
            return
        
        # Create a copy of the connections list to avoid modification during iteration
        connections = self.connections[session_id].copy()
        
        # Send messages to all connections concurrently for better performance
        async def send_with_cleanup(websocket):
            try:
                await self.send_to_connection(websocket, message)
                return None  # Success
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket in session {session_id}: {e}")
                return websocket  # Failed websocket for cleanup
        
        # Execute all sends concurrently
        results = await asyncio.gather(
            *[send_with_cleanup(ws) for ws in connections],
            return_exceptions=True
        )
        
        # Remove disconnected WebSockets
        for websocket in results:
            if websocket is not None:  # Failed websocket
                self.disconnect(websocket, session_id)
    
    async def broadcast_to_all(self, message: Dict[str, Any]):
        """Broadcast a message to all connected WebSockets"""
        session_ids = list(self.connections.keys())
        
        # Broadcast to all sessions concurrently for better performance
        await asyncio.gather(
            *[self.broadcast_to_session(session_id, message) for session_id in session_ids],
            return_exceptions=True
        )
    
    def get_session_connection_count(self, session_id: str) -> int:
        """Get the number of active connections for a session"""
        return len(self.connections.get(session_id, []))
    
    def get_total_connections(self) -> int:
        """Get the total number of active connections"""
        return sum(len(connections) for connections in self.connections.values())
    
    def get_active_sessions(self) -> List[str]:
        """Get list of session IDs with active connections"""
        return list(self.connections.keys())
