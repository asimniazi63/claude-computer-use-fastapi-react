"""
Pydantic models for the Computer Use Demo API
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import json


class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class SessionStatus(str, Enum):
    CREATED = "created"
    ACTIVE = "active"
    STOPPED = "stopped"
    ERROR = "error"


class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"
    THINKING = "thinking"


class SessionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: SessionStatus = SessionStatus.CREATED


class SessionResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def dict(self, **kwargs):
        """Override dict method to ensure datetime serialization"""
        data = super().dict(**kwargs)
        # Convert datetime objects to ISO format strings
        if isinstance(data.get('created_at'), datetime):
            data['created_at'] = data['created_at'].isoformat()
        if isinstance(data.get('updated_at'), datetime):
            data['updated_at'] = data['updated_at'].isoformat()
        return data


class MessageCreate(BaseModel):
    session_id: str
    content: str
    message_type: MessageType
    sender: str
    metadata: Optional[Dict[str, Any]] = None


class MessageResponse(BaseModel):
    id: str
    session_id: str
    content: str
    message_type: MessageType
    sender: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def dict(self, **kwargs):
        """Override dict method to ensure datetime serialization"""
        data = super().dict(**kwargs)
        # Convert datetime objects to ISO format strings
        if isinstance(data.get('created_at'), datetime):
            data['created_at'] = data['created_at'].isoformat()
        return data


class ToolUse(BaseModel):
    id: str
    name: str
    input: Dict[str, Any]


class ToolResult(BaseModel):
    tool_use_id: str
    content: str
    is_error: bool = False
    base64_image: Optional[str] = None


class ComputerUseMessage(BaseModel):
    """Message format for computer use agent communication"""
    role: str  # "user", "assistant"
    content: List[Dict[str, Any]]  # Claude API format


class SessionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[SessionStatus] = None
