"""
Computer Use Service - integrates the existing computer use agent loop with the new backend
"""

import asyncio
import os
import platform
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

# Import the existing computer use components
try:
    from ..loop import (
        APIProvider,
        sampling_loop,
        SYSTEM_PROMPT
    )
    from ..tools import (
        TOOL_GROUPS_BY_VERSION,
        ToolCollection,
        ToolResult,
        ToolVersion
    )
    from anthropic.types.beta import (
        BetaContentBlockParam,
        BetaTextBlockParam,
        BetaToolResultBlockParam,
        BetaMessageParam
    )
    COMPUTER_USE_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import computer use components: {e}")
    # Fallback - create dummy classes to allow FastAPI to start
    class APIProvider:
        pass
    def sampling_loop(*args, **kwargs):
        pass
    SYSTEM_PROMPT = "Computer use not available"
    class ToolCollection:
        pass
    class ToolResult:
        pass
    TOOL_GROUPS_BY_VERSION = {}
    COMPUTER_USE_AVAILABLE = False

from .models import MessageCreate, MessageType, SessionStatus
from .database import Database
from .websocket_manager import WebSocketManager


def serialize_datetime_for_json(data: dict) -> dict:
    """Convert datetime objects to ISO strings for JSON serialization"""
    serialized = data.copy()
    for key, value in serialized.items():
        if hasattr(value, 'isoformat'):
            serialized[key] = value.isoformat()
    return serialized


class ComputerUseService:
    def __init__(self):
        # Active sessions and their configurations
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Default configuration
        self.default_config = {
            "model": "claude-sonnet-4-20250514",
            "provider": APIProvider.ANTHROPIC,
            "api_key": os.getenv("ANTHROPIC_API_KEY", ""),
            "tool_version": "computer_use_20250124",
            "max_tokens": 8192,
            "thinking_budget": 4096,
            "only_n_most_recent_images": 3,
            "token_efficient_tools_beta": False,
            "system_prompt_suffix": ""
        }
        
        # WebSocket manager reference (will be injected)
        self.websocket_manager: Optional[WebSocketManager] = None
    
    async def initialize(self):
        """Initialize the computer use service"""
        logger.info("Initializing Computer Use Service")
        
        if not COMPUTER_USE_AVAILABLE:
            logger.warning("Computer use components not available - running in limited mode")
            return
        
        # Validate API key
        if not self.default_config["api_key"]:
            logger.warning("No ANTHROPIC_API_KEY found in environment variables")
    
    def set_websocket_manager(self, websocket_manager: WebSocketManager):
        """Inject WebSocket manager dependency"""
        self.websocket_manager = websocket_manager
    
    async def process_message(self, session_id: str, user_message: str, db: Database):
        """Process a user message through the computer use agent"""
        try:
            logger.info(f"Processing message for session {session_id}: {user_message[:100]}...")
            
            # Get or create session configuration
            if session_id not in self.active_sessions:
                await self._initialize_session(session_id, db)
            
            session_config = self.active_sessions[session_id]
            
            # Update session status to active
            await db.update_session_status(session_id, SessionStatus.ACTIVE)
            
            # Broadcast session status update
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_session(session_id, {
                    "type": "session_status",
                    "data": {"status": "active", "message": "Processing message..."}
                })
            
            # Get existing messages for context
            existing_messages = await db.get_session_messages(session_id)
            
            # Convert to Claude API format
            claude_messages = await self._convert_messages_to_claude_format(existing_messages)
            
            # Add the new user message
            claude_messages.append({
                "role": "user",
                "content": [BetaTextBlockParam(type="text", text=user_message)]
            })
            
            # Create callbacks for real-time updates
            output_callback = self._create_output_callback(session_id, db)
            tool_output_callback = self._create_tool_output_callback(session_id, db)
            api_response_callback = self._create_api_response_callback(session_id)
            
            # Run the sampling loop
            updated_messages = await sampling_loop(
                model=session_config["model"],
                provider=session_config["provider"],
                system_prompt_suffix=session_config["system_prompt_suffix"],
                messages=claude_messages,
                output_callback=output_callback,
                tool_output_callback=tool_output_callback,
                api_response_callback=api_response_callback,
                api_key=session_config["api_key"],
                only_n_most_recent_images=session_config["only_n_most_recent_images"],
                max_tokens=session_config["max_tokens"],
                tool_version=session_config["tool_version"],
                thinking_budget=session_config["thinking_budget"],
                token_efficient_tools_beta=session_config["token_efficient_tools_beta"]
            )
            
            # Update session messages
            self.active_sessions[session_id]["messages"] = updated_messages
            
            # Update session status
            await db.update_session_status(session_id, SessionStatus.STOPPED)
            
            # Broadcast completion
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_session(session_id, {
                    "type": "session_status",
                    "data": {"status": "completed", "message": "Message processing completed"}
                })
            
        except Exception as e:
            logger.error(f"Error processing message for session {session_id}: {e}")
            
            # Create error message
            error_message = MessageCreate(
                session_id=session_id,
                content=f"Error: {str(e)}",
                message_type=MessageType.SYSTEM,
                sender="system",
                metadata={"error": True}
            )
            
            await db.create_message(error_message)
            
            # Update session status
            await db.update_session_status(session_id, SessionStatus.ERROR)
            
            # Broadcast error
            if self.websocket_manager:
                await self.websocket_manager.broadcast_to_session(session_id, {
                    "type": "error",
                    "data": {"message": str(e)}
                })
    
    async def stop_session(self, session_id: str):
        """Stop processing for a session"""
        if session_id in self.active_sessions:
            logger.info(f"Stopping session {session_id}")
            # In a more complex implementation, you would interrupt the sampling loop
            # For now, we just remove it from active sessions
            self.active_sessions[session_id]["stopped"] = True
    
    async def _initialize_session(self, session_id: str, db: Database):
        """Initialize a new session with default configuration"""
        self.active_sessions[session_id] = {
            **self.default_config,
            "messages": [],
            "stopped": False
        }
        
        logger.info(f"Initialized session {session_id} with default configuration")
    
    async def _convert_messages_to_claude_format(self, messages) -> List[BetaMessageParam]:
        """Convert database messages to Claude API format"""
        claude_messages = []
        
        for msg in messages:
            if msg.message_type == MessageType.USER:
                claude_messages.append({
                    "role": "user",
                    "content": [BetaTextBlockParam(type="text", text=msg.content)]
                })
            elif msg.message_type == MessageType.ASSISTANT:
                # Parse assistant message content
                try:
                    import json
                    content = json.loads(msg.content) if isinstance(msg.content, str) else msg.content
                    claude_messages.append({
                        "role": "assistant",
                        "content": content
                    })
                except:
                    # Fallback for simple text messages
                    claude_messages.append({
                        "role": "assistant",
                        "content": [BetaTextBlockParam(type="text", text=msg.content)]
                    })
        
        return claude_messages
    
    def _create_output_callback(self, session_id: str, db: Database) -> Callable:
        """Create callback for agent output"""
        async def output_callback(content_block: BetaContentBlockParam):
            try:
                # Create message in database
                if isinstance(content_block, dict):
                    content_str = content_block.get("text", str(content_block))
                    message_type = MessageType.THINKING if content_block.get("type") == "thinking" else MessageType.ASSISTANT
                else:
                    content_str = str(content_block)
                    message_type = MessageType.ASSISTANT
                
                message = MessageCreate(
                    session_id=session_id,
                    content=content_str,
                    message_type=message_type,
                    sender="assistant",
                    metadata={"content_block": content_block if isinstance(content_block, dict) else None}
                )
                
                db_message = await db.create_message(message)
                
                # Broadcast via WebSocket
                if self.websocket_manager:
                    message_data = serialize_datetime_for_json(db_message.dict())
                    await self.websocket_manager.broadcast_to_session(session_id, {
                        "type": "message",
                        "data": message_data
                    })
                    
            except Exception as e:
                logger.error(f"Error in output callback: {e}")
        
        return output_callback
    
    def _create_tool_output_callback(self, session_id: str, db: Database) -> Callable:
        """Create callback for tool output"""
        async def tool_output_callback(tool_result: ToolResult, tool_id: str):
            try:
                # Create tool message in database
                content = ""
                if tool_result.output:
                    content += tool_result.output
                if tool_result.error:
                    content += f"\nError: {tool_result.error}"
                
                message = MessageCreate(
                    session_id=session_id,
                    content=content,
                    message_type=MessageType.TOOL,
                    sender="tool",
                    metadata={
                        "tool_id": tool_id,
                        "has_image": bool(tool_result.base64_image),
                        "is_error": bool(tool_result.error)
                    }
                )
                
                db_message = await db.create_message(message)
                
                # Broadcast via WebSocket
                if self.websocket_manager:
                    message_data = serialize_datetime_for_json(db_message.dict())
                    await self.websocket_manager.broadcast_to_session(session_id, {
                        "type": "tool_result",
                        "data": {
                            **message_data,
                            "base64_image": tool_result.base64_image
                        }
                    })
                    
            except Exception as e:
                logger.error(f"Error in tool output callback: {e}")
        
        return tool_output_callback
    
    def _create_api_response_callback(self, session_id: str) -> Callable:
        """Create callback for API responses (for debugging)"""
        async def api_response_callback(request, response, error):
            try:
                # Log API calls for debugging
                if error:
                    logger.error(f"API error for session {session_id}: {error}")
                else:
                    logger.info(f"API call completed for session {session_id}")
                
                # Optionally broadcast API status
                if self.websocket_manager:
                    await self.websocket_manager.broadcast_to_session(session_id, {
                        "type": "api_status",
                        "data": {
                            "status": "error" if error else "success",
                            "error": str(error) if error else None
                        }
                    })
                    
            except Exception as e:
                logger.error(f"Error in API response callback: {e}")
        
        return api_response_callback
