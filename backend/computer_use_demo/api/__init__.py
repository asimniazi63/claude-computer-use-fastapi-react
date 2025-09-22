"""
FastAPI backend for Computer Use Demo
"""

# Import only the essential components to avoid circular imports
from .models import *
from .database import Database, get_db
from .websocket_manager import WebSocketManager
from .computer_use_service import ComputerUseService

__all__ = [
    'Database',
    'get_db', 
    'WebSocketManager',
    'ComputerUseService'
]
