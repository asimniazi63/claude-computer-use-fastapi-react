"""
FastAPI Backend for Energent AI (Challenge)
Provides REST API and WebSocket endpoints for session management and real-time communication
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Dict, Any, Optional
import json

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from .database import Database, get_db, set_db_instance
from .models import (
    SessionCreate, 
    SessionResponse, 
    MessageCreate, 
    MessageResponse,
    SessionStatus,
    MessageType
)
from .computer_use_service import ComputerUseService, serialize_datetime_for_json
from .websocket_manager import WebSocketManager


# Pydantic models for API
class SessionCreateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class MessageRequest(BaseModel):
    content: str
    message_type: str = "user"


class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]


class MessageListResponse(BaseModel):
    messages: List[MessageResponse]


# Global services
websocket_manager = WebSocketManager()
computer_use_service = ComputerUseService()

# Track background tasks to prevent them from being garbage collected
background_tasks = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize services on startup"""
    # Initialize database
    db = Database()
    await db.initialize()
    
    # Set the database instance for dependency injection
    set_db_instance(db)
    
    # Initialize computer use service
    await computer_use_service.initialize()
    
    # Inject WebSocket manager into computer use service
    computer_use_service.set_websocket_manager(websocket_manager)
    
    yield
    
    # Cleanup on shutdown
    # Cancel any remaining background tasks
    for task in list(background_tasks):
        if not task.done():
            task.cancel()
    
    # Wait for all tasks to complete or timeout
    if background_tasks:
        await asyncio.gather(*background_tasks, return_exceptions=True)
    
    await db.close()


app = FastAPI(
    title="Energent AI (Challenge) API",
    description="Backend API for managing computer use agent sessions",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "http://localhost:8080", 
        "http://frontend:3000",  # Docker container network
        "http://localhost:8501",  # Internal backend access
        "*"  # Allow all origins for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# REST API Endpoints

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Energent AI (Challenge) API", "status": "running", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "message": "Energent AI (Challenge) API is running",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "api": "running",
            "database": "connected",
            "websocket": "available"
        }
    }


@app.get("/api/sessions", response_model=SessionListResponse)
async def list_sessions(db: Database = Depends(get_db)):
    """Get all sessions"""
    sessions = await db.get_all_sessions()
    return SessionListResponse(sessions=sessions)


@app.get("/api/debug/sessions")
async def debug_sessions(db: Database = Depends(get_db)):
    """Debug endpoint to list all session IDs"""
    sessions = await db.get_all_sessions()
    return {
        "total_sessions": len(sessions),
        "session_ids": [s.id for s in sessions],
        "sessions": [{"id": s.id, "name": s.name, "status": s.status} for s in sessions]
    }


@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(
    request: SessionCreateRequest, 
    db: Database = Depends(get_db)
):
    """Create a new session"""
    session_data = SessionCreate(
        name=request.name or f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        description=request.description,
        status=SessionStatus.CREATED
    )
    
    session = await db.create_session(session_data)
    return session


@app.get("/api/sessions/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str, db: Database = Depends(get_db)):
    """Get a specific session"""
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, db: Database = Depends(get_db)):
    """Delete a session"""
    success = await db.delete_session(session_id)
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"message": "Session deleted"}


@app.get("/api/sessions/{session_id}/messages", response_model=MessageListResponse)
async def get_session_messages(session_id: str, db: Database = Depends(get_db)):
    """Get all messages for a session"""
    messages = await db.get_session_messages(session_id)
    return MessageListResponse(messages=messages)


@app.post("/api/sessions/{session_id}/messages", response_model=MessageResponse)
async def send_message(
    session_id: str,
    request: MessageRequest,
    db: Database = Depends(get_db)
):
    """Send a message to a session"""
    try:
        # Verify session exists
        session = await db.get_session(session_id)
        if not session:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Session {session_id} not found in database")
            # Let's also check what sessions do exist
            all_sessions = await db.get_all_sessions()
            logger.info(f"Available sessions: {[s.id for s in all_sessions]}")
            raise HTTPException(status_code=404, detail="Session not found")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error verifying session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")
    
    # Create user message
    # Convert string to MessageType enum
    try:
        msg_type = MessageType(request.message_type)
    except ValueError:
        msg_type = MessageType.USER  # Default fallback
    
    message_data = MessageCreate(
        session_id=session_id,
        content=request.content,
        message_type=msg_type,
        sender="user"
    )
    
    message = await db.create_message(message_data)
    
    # Notify WebSocket clients
    message_data = serialize_datetime_for_json(message.dict())
    await websocket_manager.broadcast_to_session(session_id, {
        "type": "message",
        "data": message_data
    })
    
    # Process message with computer use agent if it's a user message
    if request.message_type == "user":
        # Start processing in background with proper task management
        task = asyncio.create_task(
            computer_use_service.process_message(session_id, request.content, db)
        )
        
        # Track task to prevent garbage collection and add cleanup callback
        background_tasks.add(task)
        
        def task_cleanup(task):
            """Clean up completed task and log any errors"""
            background_tasks.discard(task)
            if task.exception():
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Background task failed: {task.exception()}")
        
        task.add_done_callback(task_cleanup)
    
    return message


@app.post("/api/sessions/{session_id}/start")
async def start_session(session_id: str, db: Database = Depends(get_db)):
    """Start/resume a session"""
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session status
    await db.update_session_status(session_id, SessionStatus.ACTIVE)
    
    # Notify WebSocket clients
    await websocket_manager.broadcast_to_session(session_id, {
        "type": "session_status",
        "data": {"status": "active"}
    })
    
    return {"message": "Session started"}


@app.post("/api/sessions/{session_id}/stop")
async def stop_session(session_id: str, db: Database = Depends(get_db)):
    """Stop a session"""
    session = await db.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update session status
    await db.update_session_status(session_id, SessionStatus.STOPPED)
    
    # Stop any running computer use processes
    await computer_use_service.stop_session(session_id)
    
    # Notify WebSocket clients
    await websocket_manager.broadcast_to_session(session_id, {
        "type": "session_status",
        "data": {"status": "stopped"}
    })
    
    return {"message": "Session stopped"}


# WebSocket endpoint for real-time communication
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket connection for real-time updates"""
    await websocket_manager.connect(websocket, session_id)
    
    try:
        while True:
            # Keep connection alive and listen for client messages
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Handle different message types
            if message_data.get("type") == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
            elif message_data.get("type") == "subscribe":
                # Client is subscribing to session updates
                await websocket.send_text(json.dumps({
                    "type": "subscribed",
                    "session_id": session_id
                }))
                
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket, session_id)


# VNC endpoint (proxy to existing VNC server)
@app.get("/api/vnc/{session_id}")
async def get_vnc_info(session_id: str):
    """Get VNC connection information"""
    # For now, return static VNC info
    # In production, you might want to create isolated VNC sessions per session
    return {
        "vnc_url": "http://localhost:8080",  # noVNC web client
        "vnc_port": 5901,
        "display": ":1"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8501,  # Match Docker port
        reload=True,
        log_level="info"
    )
