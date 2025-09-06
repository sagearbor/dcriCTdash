#!/usr/bin/env python3
"""
Integrated Server for DCRI Clinical Trial Dashboard

This script runs both the FastAPI backend and Dash frontend in a unified application.
The Dash app will be served on the same port as the FastAPI app for seamless integration.
"""

import os
import sys
import asyncio
import logging
from threading import Thread
import time
import uvicorn
from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.serving import run_simple

# Add app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Import our applications
from app.main import app as fastapi_app
from app.dashboard import create_dash_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_integrated_app():
    """
    Create an integrated application that serves both FastAPI and Dash.
    
    Returns:
        DispatcherMiddleware: Combined WSGI application
    """
    # Create Dash app
    dash_app = create_dash_app()
    
    # Create WSGI applications
    dash_wsgi = dash_app.server
    
    # Create the dispatcher middleware to route requests
    application = DispatcherMiddleware(dash_wsgi, {
        '/api': fastapi_app,
        '/health': fastapi_app,
        '/ws': fastapi_app,
        '/docs': fastapi_app,
        '/redoc': fastapi_app
    })
    
    return application, dash_app

def run_fastapi_server():
    """Run FastAPI server in a separate thread for API endpoints."""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8002,  # Changed from 8000 to avoid JupyterHub conflict
        reload=False,  # Disable reload to prevent conflicts
        log_level="info"
    )

def main():
    """Main entry point for the integrated server."""
    print("🚀 Starting DCRI Clinical Trial Analytics Dashboard")
    print("   Integrated FastAPI Backend + Dash Frontend")
    print("   Navigate to: http://localhost:8050 (Dashboard)")
    print("   API Endpoints: http://localhost:8002/api/*")
    print("   API Docs: http://localhost:8002/api/docs")
    print("   WebSocket: ws://localhost:8002/ws")
    print("-" * 60)
    
    try:
        # Start FastAPI server in background thread
        fastapi_thread = Thread(target=run_fastapi_server, daemon=True)
        fastapi_thread.start()
        
        # Give FastAPI a moment to start
        time.sleep(2)
        
        # Create and run the Dash app
        dash_app = create_dash_app()
        
        print("✅ FastAPI Backend: Running on http://localhost:8002")
        print("✅ Dash Frontend: Starting on http://localhost:8050")
        print("🎯 Access the complete dashboard at: http://localhost:8050")
        
        # Run Dash app (this will block)
        dash_app.run(
            debug=True,
            port=8050,
            host="0.0.0.0"
        )
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down DCRI Clinical Trial Dashboard...")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        logger.error(f"Server error: {e}")

if __name__ == "__main__":
    main()