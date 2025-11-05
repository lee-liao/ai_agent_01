"""
SSE (Server-Sent Events) connection manager for pushing messages to clients.
Used to deliver mentor replies in real-time to parent chat sessions via SSE.
"""

from typing import Dict, Set
import asyncio
import json


class SSEManager:
    """Manages active SSE connections per session."""
    
    def __init__(self):
        # Map session_id -> Set of async queues (one per SSE connection)
        self.active_connections: Dict[str, Set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()
    
    async def register(self, session_id: str, queue: asyncio.Queue):
        """Register an SSE connection queue for a session."""
        async with self._lock:
            if session_id not in self.active_connections:
                self.active_connections[session_id] = set()
            self.active_connections[session_id].add(queue)
    
    async def unregister(self, session_id: str, queue: asyncio.Queue):
        """Remove an SSE connection queue from a session."""
        async with self._lock:
            if session_id in self.active_connections:
                self.active_connections[session_id].discard(queue)
                if not self.active_connections[session_id]:
                    del self.active_connections[session_id]
    
    async def send_to_session(self, session_id: str, message: dict):
        """Send a message to all SSE connections for a session."""
        async with self._lock:
            queues = self.active_connections.get(session_id, set()).copy()
        
        # Send to all queues for this session
        dead_queues = set()
        for queue in queues:
            try:
                await queue.put(message)
            except Exception:
                # Queue is dead, mark for removal
                dead_queues.add(queue)
        
        # Clean up dead queues
        if dead_queues:
            async with self._lock:
                if session_id in self.active_connections:
                    self.active_connections[session_id] -= dead_queues
                    if not self.active_connections[session_id]:
                        del self.active_connections[session_id]


# Global SSE manager instance
sse_manager = SSEManager()


async def create_sse_stream(session_id: str):
    """
    Create a persistent SSE stream for a session.
    Yields messages as they arrive.
    """
    queue = asyncio.Queue()
    await sse_manager.register(session_id, queue)
    
    try:
        # Send initial connection message
        yield f"data: {json.dumps({'type': 'connected', 'session_id': session_id})}\n\n"
        
        # Keep connection alive with periodic heartbeats
        while True:
            try:
                # Wait for message with timeout for heartbeat
                message = await asyncio.wait_for(queue.get(), timeout=30.0)
                
                # Send the message
                yield f"data: {json.dumps(message)}\n\n"
                
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield f": heartbeat\n\n"
            except Exception as e:
                # Connection error, break the loop
                break
    finally:
        await sse_manager.unregister(session_id, queue)

