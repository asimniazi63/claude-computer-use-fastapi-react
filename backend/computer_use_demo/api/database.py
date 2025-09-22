"""
Database layer for the Computer Use Demo API
Uses SQLite with asyncio support
"""

import aiosqlite
import uuid
import json
import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from .models import (
    SessionCreate, SessionResponse, SessionStatus, SessionUpdate,
    MessageCreate, MessageResponse, MessageType
)


class Database:
    # def __init__(self, db_path: str = "/home/computeruse/computer_use_demo.db"):
    def __init__(self, db_path: str = "computer_use_demo.db"):
        self.db_path = db_path
        self._connection_pool = asyncio.Queue(maxsize=10)  # Connection pool
        self._pool_initialized = False

    async def _initialize_pool(self):
        """Initialize connection pool"""
        if self._pool_initialized:
            return
        
        # Pre-create some connections for the pool
        for _ in range(5):  # Initial pool size
            conn = await aiosqlite.connect(self.db_path)
            conn.row_factory = aiosqlite.Row
            await self._connection_pool.put(conn)
        
        self._pool_initialized = True

    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        await self._initialize_pool()
        
        try:
            # Try to get a connection from the pool
            conn = await asyncio.wait_for(self._connection_pool.get(), timeout=5.0)
        except asyncio.TimeoutError:
            # If pool is exhausted, create a new connection
            conn = await aiosqlite.connect(self.db_path)
            conn.row_factory = aiosqlite.Row
        
        try:
            yield conn
        finally:
            # Return connection to pool if pool isn't full
            try:
                self._connection_pool.put_nowait(conn)
            except asyncio.QueueFull:
                # Pool is full, close the connection
                await conn.close()

    async def initialize(self):
        """Initialize database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Create sessions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                )
            """)
            
            # Create messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    message_type TEXT NOT NULL,
                    sender TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages (session_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages (created_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions (status)")
            
            await db.commit()

    async def close(self):
        """Close database connections"""
        # Close all connections in the pool
        while not self._connection_pool.empty():
            try:
                conn = self._connection_pool.get_nowait()
                await conn.close()
            except asyncio.QueueEmpty:
                break

    # Session operations
    async def create_session(self, session_data: SessionCreate) -> SessionResponse:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        async with self.get_connection() as db:
            await db.execute("""
                INSERT INTO sessions (id, name, description, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                session_data.name,
                session_data.description,
                session_data.status.value,
                now,
                now
            ))
            await db.commit()
        
        return SessionResponse(
            id=session_id,
            name=session_data.name,
            description=session_data.description,
            status=session_data.status,
            created_at=now,
            updated_at=now,
            message_count=0
        )

    async def get_session(self, session_id: str) -> Optional[SessionResponse]:
        """Get a session by ID"""
        async with self.get_connection() as db:
            # Get session with message count
            cursor = await db.execute("""
                SELECT s.*, COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                WHERE s.id = ?
                GROUP BY s.id
            """, (session_id,))
            
            row = await cursor.fetchone()
            if not row:
                return None
            
            return SessionResponse(
                id=row["id"],
                name=row["name"],
                description=row["description"],
                status=SessionStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                message_count=row["message_count"]
            )

    async def get_all_sessions(self) -> List[SessionResponse]:
        """Get all sessions"""
        async with self.get_connection() as db:
            
            cursor = await db.execute("""
                SELECT s.*, COUNT(m.id) as message_count
                FROM sessions s
                LEFT JOIN messages m ON s.id = m.session_id
                GROUP BY s.id
                ORDER BY s.updated_at DESC
            """)
            
            rows = await cursor.fetchall()
            
            return [
                SessionResponse(
                    id=row["id"],
                    name=row["name"],
                    description=row["description"],
                    status=SessionStatus(row["status"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                    updated_at=datetime.fromisoformat(row["updated_at"]),
                    message_count=row["message_count"]
                )
                for row in rows
            ]

    async def update_session(self, session_id: str, updates: SessionUpdate) -> bool:
        """Update a session"""
        update_fields = []
        values = []
        
        if updates.name is not None:
            update_fields.append("name = ?")
            values.append(updates.name)
        
        if updates.description is not None:
            update_fields.append("description = ?")
            values.append(updates.description)
        
        if updates.status is not None:
            update_fields.append("status = ?")
            values.append(updates.status.value)
        
        if not update_fields:
            return True
        
        update_fields.append("updated_at = ?")
        values.append(datetime.utcnow())
        values.append(session_id)
        
        async with self.get_connection() as db:
            cursor = await db.execute(f"""
                UPDATE sessions 
                SET {', '.join(update_fields)}
                WHERE id = ?
            """, values)
            
            await db.commit()
            return cursor.rowcount > 0

    async def update_session_status(self, session_id: str, status: SessionStatus) -> bool:
        """Update session status"""
        return await self.update_session(session_id, SessionUpdate(status=status))

    async def delete_session(self, session_id: str) -> bool:
        """Delete a session and all its messages"""
        async with self.get_connection() as db:
            cursor = await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            await db.commit()
            return cursor.rowcount > 0

    # Message operations
    async def create_message(self, message_data: MessageCreate) -> MessageResponse:
        """Create a new message"""
        message_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        metadata_json = json.dumps(message_data.metadata) if message_data.metadata else None
        
        async with self.get_connection() as db:
            await db.execute("""
                INSERT INTO messages (id, session_id, content, message_type, sender, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                message_id,
                message_data.session_id,
                message_data.content,
                message_data.message_type.value,
                message_data.sender,
                metadata_json,
                now
            ))
            
            # Update session updated_at
            await db.execute("""
                UPDATE sessions SET updated_at = ? WHERE id = ?
            """, (now, message_data.session_id))
            
            await db.commit()
        
        return MessageResponse(
            id=message_id,
            session_id=message_data.session_id,
            content=message_data.content,
            message_type=message_data.message_type,
            sender=message_data.sender,
            metadata=message_data.metadata,
            created_at=now
        )

    async def get_session_messages(self, session_id: str, limit: int = 100) -> List[MessageResponse]:
        """Get messages for a session"""
        async with self.get_connection() as db:
            
            cursor = await db.execute("""
                SELECT * FROM messages 
                WHERE session_id = ? 
                ORDER BY created_at ASC 
                LIMIT ?
            """, (session_id, limit))
            
            rows = await cursor.fetchall()
            
            return [
                MessageResponse(
                    id=row["id"],
                    session_id=row["session_id"],
                    content=row["content"],
                    message_type=MessageType(row["message_type"]),
                    sender=row["sender"],
                    metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                    created_at=datetime.fromisoformat(row["created_at"])
                )
                for row in rows
            ]

    async def get_message(self, message_id: str) -> Optional[MessageResponse]:
        """Get a specific message"""
        async with self.get_connection() as db:
            
            cursor = await db.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
            row = await cursor.fetchone()
            
            if not row:
                return None
            
            return MessageResponse(
                id=row["id"],
                session_id=row["session_id"],
                content=row["content"],
                message_type=MessageType(row["message_type"]),
                sender=row["sender"],
                metadata=json.loads(row["metadata"]) if row["metadata"] else None,
                created_at=datetime.fromisoformat(row["created_at"])
            )


# Dependency injection for FastAPI
_db_instance = None

def set_db_instance(db: Database):
    """Set the database instance (called from app lifespan)"""
    global _db_instance
    _db_instance = db

async def get_db() -> Database:
    """Get database instance for dependency injection"""
    global _db_instance
    if _db_instance is None:
        raise RuntimeError("Database not initialized. Call set_db_instance() first.")
    return _db_instance
