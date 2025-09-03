#!/usr/bin/env python3
"""
FastAPI Backend Only Server

Runs only the FastAPI backend for API testing and development.
Use this if you only need the API endpoints without the dashboard.
"""

import uvicorn
from app.main import app

if __name__ == "__main__":
    print("🚀 Starting DCRI Clinical Trial Analytics Dashboard - API Only")
    print("   FastAPI Backend with WebSocket Support")
    print("   Navigate to: http://localhost:8000")
    print("   API Docs: http://localhost:8000/api/docs")
    print("   WebSocket: ws://localhost:8000/ws")
    print("   Health Check: http://localhost:8000/health")
    print("-" * 60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )