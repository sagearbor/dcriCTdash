"""
WebSocket Client for Real-time Demo Mode

Handles WebSocket connections to the FastAPI backend for real-time data streaming
in demo mode. Provides async functionality for live dashboard updates.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Callable, Optional
import websockets
import threading
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketClient:
    """WebSocket client for real-time dashboard updates."""
    
    def __init__(self, url: str = "ws://localhost:8000/ws"):
        """
        Initialize WebSocket client.
        
        Args:
            url: WebSocket server URL
        """
        self.url = url
        self.websocket = None
        self.is_connected = False
        self.demo_active = False
        self.message_handlers = {}
        self.connection_thread = None
        
    async def connect(self) -> bool:
        """
        Connect to WebSocket server.
        
        Returns:
            bool: True if connection successful
        """
        try:
            self.websocket = await websockets.connect(self.url)
            self.is_connected = True
            logger.info(f"Connected to WebSocket: {self.url}")
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            self.is_connected = False
            return False
    
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("WebSocket disconnected")
    
    async def send_message(self, message: Dict[str, Any]):
        """
        Send message to WebSocket server.
        
        Args:
            message: Message dictionary to send
        """
        if self.websocket and self.is_connected:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send WebSocket message: {e}")
    
    async def listen_for_messages(self):
        """Listen for incoming WebSocket messages."""
        if not self.websocket or not self.is_connected:
            return
        
        try:
            async for raw_message in self.websocket:
                try:
                    message = json.loads(raw_message)
                    message_type = message.get('type', 'unknown')
                    
                    # Handle different message types
                    if message_type in self.message_handlers:
                        self.message_handlers[message_type](message)
                    else:
                        logger.info(f"Received unhandled message type: {message_type}")
                        
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode WebSocket message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"WebSocket listening error: {e}")
            self.is_connected = False
    
    def add_message_handler(self, message_type: str, handler: Callable):
        """
        Add handler for specific message type.
        
        Args:
            message_type: Type of message to handle
            handler: Function to call when message received
        """
        self.message_handlers[message_type] = handler
    
    async def start_demo_mode(self):
        """Start demo mode data streaming."""
        if not self.is_connected:
            await self.connect()
        
        if self.is_connected:
            self.demo_active = True
            await self.send_message({
                "type": "subscribe_demo",
                "timestamp": time.time()
            })
            logger.info("Demo mode started")
    
    async def stop_demo_mode(self):
        """Stop demo mode data streaming."""
        self.demo_active = False
        if self.is_connected:
            await self.send_message({
                "type": "unsubscribe_demo",
                "timestamp": time.time()
            })
            logger.info("Demo mode stopped")
    
    def run_in_background(self):
        """Run WebSocket client in background thread."""
        def run_async():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._background_task())
            except Exception as e:
                logger.error(f"Background WebSocket task failed: {e}")
            finally:
                loop.close()
        
        if not self.connection_thread or not self.connection_thread.is_alive():
            self.connection_thread = threading.Thread(target=run_async, daemon=True)
            self.connection_thread.start()
    
    async def _background_task(self):
        """Background task for maintaining WebSocket connection."""
        while True:
            try:
                if not self.is_connected:
                    await self.connect()
                
                if self.is_connected:
                    await self.listen_for_messages()
                else:
                    # Wait before trying to reconnect
                    await asyncio.sleep(5)
                    
            except Exception as e:
                logger.error(f"Background WebSocket error: {e}")
                await asyncio.sleep(5)

# Global WebSocket client instance
ws_client = WebSocketClient()

def get_websocket_client() -> WebSocketClient:
    """Get the global WebSocket client instance."""
    return ws_client

def initialize_websocket_handlers():
    """Initialize default WebSocket message handlers."""
    
    def handle_connection(message):
        """Handle connection confirmation."""
        logger.info("WebSocket connection confirmed")
    
    def handle_enrollment_update(message):
        """Handle enrollment update message."""
        logger.info(f"Enrollment update: {message.get('new_enrollments', 0)} new patients")
    
    def handle_demo_complete(message):
        """Handle demo completion message."""
        logger.info("Demo mode completed")
        ws_client.demo_active = False
    
    def handle_error(message):
        """Handle error message."""
        logger.error(f"WebSocket error: {message.get('message', 'Unknown error')}")
    
    # Register handlers
    ws_client.add_message_handler('connection', handle_connection)
    ws_client.add_message_handler('enrollment_update', handle_enrollment_update)
    ws_client.add_message_handler('demo_complete', handle_demo_complete)
    ws_client.add_message_handler('error', handle_error)

# Initialize handlers when module is imported
initialize_websocket_handlers()