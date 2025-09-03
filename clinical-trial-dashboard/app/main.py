"""
FastAPI Main Application

Entry point for the DCRI Clinical Trial Analytics Dashboard FastAPI application.
Handles API routes, WebSocket connections for real-time data, and Dash app integration.
"""

import os
import asyncio
import json
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union
from io import StringIO

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

# Database and model imports
from .data.database import get_database_session, get_database_info, initialize_database, get_table_counts
from .data.models import Site, Patient, Visit, Lab

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API responses
class SiteResponse(BaseModel):
    site_id: str
    site_name: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    enrollment_target: int
    current_enrollment: int = 0
    enrollment_rate: float = 0.0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PatientResponse(BaseModel):
    usubjid: str
    site_id: str
    date_of_enrollment: date
    age: Optional[int] = None
    sex: Optional[str] = None
    race: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class VisitResponse(BaseModel):
    visit_id: str
    usubjid: str
    visit_name: str
    visit_num: int
    visit_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class LabResponse(BaseModel):
    lab_id: str
    usubjid: str
    visit_id: str
    lbtestcd: str
    lbtest: str
    lborres: Optional[str] = None
    lbstresn: Optional[float] = None
    lbstresu: Optional[str] = None
    lbnrind: Optional[str] = None
    collection_date: date
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class StatsResponse(BaseModel):
    total_sites: int
    total_patients: int
    total_visits: int
    total_labs: int
    enrollment_by_site: List[Dict[str, Any]]
    enrollment_timeline: List[Dict[str, Any]]
    lab_abnormalities: Dict[str, int]

class HealthResponse(BaseModel):
    status: str
    service: str
    database_status: str
    table_counts: Dict[str, int]
    database_info: Dict[str, Any]

# WebSocket connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                disconnected.append(connection)
        
        # Remove disconnected connections
        for conn in disconnected:
            self.disconnect(conn)

# FastAPI app initialization
app = FastAPI(
    title="DCRI Clinical Trial Analytics Dashboard",
    description="FDA-compliant web application for real-time monitoring and analysis of clinical trial data",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# WebSocket manager
manager = ConnectionManager()

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event to initialize database
@app.on_event("startup")
async def startup_event():
    """Initialize database and setup on application startup."""
    try:
        logger.info("Initializing DCRI Clinical Trial Dashboard...")
        initialize_database(with_sample_data=True)
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

# Health check endpoint with comprehensive status
@app.get("/health", response_model=HealthResponse)
async def health_check(db: Session = Depends(get_database_session)) -> HealthResponse:
    """Enhanced health check endpoint with database and system status."""
    try:
        # Test database connection
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        
        # Get table counts
        table_counts = get_table_counts()
        
        # Get database info
        db_info = get_database_info()
        
        return HealthResponse(
            status="healthy",
            service="dcri-clinical-trial-dashboard",
            database_status=db_status,
            table_counts=table_counts,
            database_info=db_info
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            service="dcri-clinical-trial-dashboard",
            database_status="error",
            table_counts={},
            database_info={"error": str(e)}
        )

# API version endpoint
@app.get("/api/version")
async def get_version() -> Dict[str, str]:
    """Get application version information."""
    return {"version": "0.1.0", "api_version": "v1"}

# Root endpoint - redirect to dashboard
@app.get("/")
async def root():
    """Root endpoint redirects to the dashboard."""
    return RedirectResponse(url="/dashboard")

# Dashboard endpoint
@app.get("/dashboard")
async def dashboard():
    """Serve the main dashboard (placeholder until Dash integration)."""
    return HTMLResponse("""
    <html>
        <head>
            <title>DCRI Clinical Trial Analytics Dashboard</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .status { background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }
                .api-links a { display: inline-block; margin: 10px; padding: 8px 16px; 
                              background: #007cba; color: white; text-decoration: none; border-radius: 4px; }
                .api-links a:hover { background: #005a8a; }
            </style>
        </head>
        <body>
            <h1>DCRI Clinical Trial Analytics Dashboard</h1>
            <div class="status">
                <h3>✅ FastAPI Backend Running</h3>
                <p>Backend API is operational and ready for dashboard integration.</p>
            </div>
            <div class="api-links">
                <h3>Available API Endpoints:</h3>
                <a href="/api/docs" target="_blank">API Documentation</a>
                <a href="/api/sites" target="_blank">Sites API</a>
                <a href="/api/patients" target="_blank">Patients API</a>
                <a href="/api/stats" target="_blank">Statistics API</a>
                <a href="/health" target="_blank">Health Check</a>
            </div>
        </body>
    </html>
    """)

# Sites API endpoints
@app.get("/api/sites", response_model=List[SiteResponse])
async def get_sites(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    country: Optional[str] = Query(None),
    db: Session = Depends(get_database_session)
):
    """Get clinical trial sites with optional filtering."""
    try:
        query = db.query(Site)
        
        # Apply country filter if provided
        if country:
            query = query.filter(Site.country == country.upper())
        
        # Apply pagination
        sites = query.offset(offset).limit(limit).all()
        
        # Enhance with enrollment data
        site_responses = []
        for site in sites:
            current_enrollment = db.query(func.count(Patient.usubjid)).filter(
                Patient.site_id == site.site_id
            ).scalar() or 0
            
            # Calculate enrollment rate (patients per day since site creation)
            days_active = (datetime.now() - site.created_at).days
            enrollment_rate = current_enrollment / max(days_active, 1)
            
            site_data = SiteResponse.from_orm(site)
            site_data.current_enrollment = current_enrollment
            site_data.enrollment_rate = round(enrollment_rate, 2)
            site_responses.append(site_data)
        
        return site_responses
    except Exception as e:
        logger.error(f"Error fetching sites: {e}")
        raise HTTPException(status_code=500, detail="Error fetching sites data")

@app.get("/api/sites/{site_id}", response_model=SiteResponse)
async def get_site(site_id: str, db: Session = Depends(get_database_session)):
    """Get specific site details."""
    try:
        site = db.query(Site).filter(Site.site_id == site_id).first()
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        
        # Get current enrollment
        current_enrollment = db.query(func.count(Patient.usubjid)).filter(
            Patient.site_id == site.site_id
        ).scalar() or 0
        
        # Calculate enrollment rate
        days_active = (datetime.now() - site.created_at).days
        enrollment_rate = current_enrollment / max(days_active, 1)
        
        site_data = SiteResponse.from_orm(site)
        site_data.current_enrollment = current_enrollment
        site_data.enrollment_rate = round(enrollment_rate, 2)
        
        return site_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching site {site_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching site data")

# Patients API endpoints
@app.get("/api/patients", response_model=List[PatientResponse])
async def get_patients(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    site_id: Optional[str] = Query(None),
    sex: Optional[str] = Query(None),
    min_age: Optional[int] = Query(None, ge=0),
    max_age: Optional[int] = Query(None, le=120),
    db: Session = Depends(get_database_session)
):
    """Get patient enrollment data with filtering options."""
    try:
        query = db.query(Patient)
        
        # Apply filters
        if site_id:
            query = query.filter(Patient.site_id == site_id)
        if sex:
            query = query.filter(Patient.sex == sex.upper())
        if min_age is not None:
            query = query.filter(Patient.age >= min_age)
        if max_age is not None:
            query = query.filter(Patient.age <= max_age)
        
        # Order by enrollment date (most recent first)
        query = query.order_by(desc(Patient.date_of_enrollment))
        
        # Apply pagination
        patients = query.offset(offset).limit(limit).all()
        
        return [PatientResponse.from_orm(patient) for patient in patients]
    except Exception as e:
        logger.error(f"Error fetching patients: {e}")
        raise HTTPException(status_code=500, detail="Error fetching patients data")

@app.get("/api/patients/{usubjid}", response_model=PatientResponse)
async def get_patient(usubjid: str, db: Session = Depends(get_database_session)):
    """Get specific patient details."""
    try:
        patient = db.query(Patient).filter(Patient.usubjid == usubjid).first()
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        return PatientResponse.from_orm(patient)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching patient {usubjid}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching patient data")

# Visits API endpoints
@app.get("/api/visits", response_model=List[VisitResponse])
async def get_visits(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    usubjid: Optional[str] = Query(None),
    site_id: Optional[str] = Query(None),
    db: Session = Depends(get_database_session)
):
    """Get visit data with filtering options."""
    try:
        query = db.query(Visit)
        
        # Apply filters
        if usubjid:
            query = query.filter(Visit.usubjid == usubjid)
        if site_id:
            query = query.join(Patient).filter(Patient.site_id == site_id)
        
        # Order by visit date (most recent first)
        query = query.order_by(desc(Visit.visit_date))
        
        # Apply pagination
        visits = query.offset(offset).limit(limit).all()
        
        return [VisitResponse.from_orm(visit) for visit in visits]
    except Exception as e:
        logger.error(f"Error fetching visits: {e}")
        raise HTTPException(status_code=500, detail="Error fetching visits data")

@app.get("/api/visits/{visit_id}", response_model=VisitResponse)
async def get_visit(visit_id: str, db: Session = Depends(get_database_session)):
    """Get specific visit details."""
    try:
        visit = db.query(Visit).filter(Visit.visit_id == visit_id).first()
        if not visit:
            raise HTTPException(status_code=404, detail="Visit not found")
        
        return VisitResponse.from_orm(visit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching visit {visit_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching visit data")

# Labs API endpoints
@app.get("/api/labs", response_model=List[LabResponse])
async def get_labs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    usubjid: Optional[str] = Query(None),
    lbtestcd: Optional[str] = Query(None),
    lbnrind: Optional[str] = Query(None),
    db: Session = Depends(get_database_session)
):
    """Get laboratory data with filtering options."""
    try:
        query = db.query(Lab)
        
        # Apply filters
        if usubjid:
            query = query.filter(Lab.usubjid == usubjid)
        if lbtestcd:
            query = query.filter(Lab.lbtestcd == lbtestcd.upper())
        if lbnrind:
            query = query.filter(Lab.lbnrind == lbnrind.upper())
        
        # Order by collection date (most recent first)
        query = query.order_by(desc(Lab.collection_date))
        
        # Apply pagination
        labs = query.offset(offset).limit(limit).all()
        
        return [LabResponse.from_orm(lab) for lab in labs]
    except Exception as e:
        logger.error(f"Error fetching labs: {e}")
        raise HTTPException(status_code=500, detail="Error fetching labs data")

@app.get("/api/labs/{lab_id}", response_model=LabResponse)
async def get_lab(lab_id: str, db: Session = Depends(get_database_session)):
    """Get specific lab result details."""
    try:
        lab = db.query(Lab).filter(Lab.lab_id == lab_id).first()
        if not lab:
            raise HTTPException(status_code=404, detail="Lab result not found")
        
        return LabResponse.from_orm(lab)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching lab {lab_id}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching lab data")

# Statistics API endpoint
@app.get("/api/stats", response_model=StatsResponse)
async def get_stats(db: Session = Depends(get_database_session)):
    """Get enrollment and summary statistics."""
    try:
        # Basic counts
        total_sites = db.query(func.count(Site.site_id)).scalar() or 0
        total_patients = db.query(func.count(Patient.usubjid)).scalar() or 0
        total_visits = db.query(func.count(Visit.visit_id)).scalar() or 0
        total_labs = db.query(func.count(Lab.lab_id)).scalar() or 0
        
        # Enrollment by site
        enrollment_by_site = db.query(
            Site.site_id,
            Site.site_name,
            func.count(Patient.usubjid).label('enrollment_count')
        ).outerjoin(Patient).group_by(Site.site_id, Site.site_name).all()
        
        enrollment_by_site_data = [
            {
                "site_id": row.site_id,
                "site_name": row.site_name,
                "enrollment_count": row.enrollment_count
            }
            for row in enrollment_by_site
        ]
        
        # Enrollment timeline (by month) - SQLite compatible
        enrollment_timeline = db.query(
            func.strftime('%Y-%m', Patient.date_of_enrollment).label('month'),
            func.count(Patient.usubjid).label('enrollments')
        ).group_by('month').order_by('month').all()
        
        enrollment_timeline_data = [
            {
                "month": row.month if row.month else 'Unknown',
                "enrollments": row.enrollments
            }
            for row in enrollment_timeline
        ]
        
        # Lab abnormalities count
        lab_abnormalities = db.query(
            Lab.lbnrind,
            func.count(Lab.lab_id).label('count')
        ).filter(Lab.lbnrind.isnot(None)).group_by(Lab.lbnrind).all()
        
        lab_abnormalities_data = {
            row.lbnrind: row.count for row in lab_abnormalities
        }
        
        return StatsResponse(
            total_sites=total_sites,
            total_patients=total_patients,
            total_visits=total_visits,
            total_labs=total_labs,
            enrollment_by_site=enrollment_by_site_data,
            enrollment_timeline=enrollment_timeline_data,
            lab_abnormalities=lab_abnormalities_data
        )
    except Exception as e:
        logger.error(f"Error calculating statistics: {e}")
        raise HTTPException(status_code=500, detail="Error calculating statistics")

# CSV Export endpoint
@app.get("/api/export/csv")
async def export_csv(
    table: str = Query(..., description="Table to export: sites, patients, visits, labs"),
    db: Session = Depends(get_database_session)
):
    """Export filtered data as CSV."""
    try:
        if table not in ["sites", "patients", "visits", "labs"]:
            raise HTTPException(status_code=400, detail="Invalid table name")
        
        # Query the appropriate table
        if table == "sites":
            data = db.query(Site).all()
        elif table == "patients":
            data = db.query(Patient).all()
        elif table == "visits":
            data = db.query(Visit).all()
        elif table == "labs":
            data = db.query(Lab).all()
        
        if not data:
            raise HTTPException(status_code=404, detail="No data found")
        
        # Convert to CSV
        import pandas as pd
        
        # Convert SQLAlchemy objects to dictionaries
        records = []
        for item in data:
            record = {}
            for column in item.__table__.columns:
                value = getattr(item, column.name)
                if isinstance(value, (date, datetime)):
                    value = value.isoformat()
                record[column.name] = value
            records.append(record)
        
        df = pd.DataFrame(records)
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_data = csv_buffer.getvalue()
        
        # Return as streaming response
        def generate():
            yield csv_data
        
        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={table}_export.csv"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting {table}: {e}")
        raise HTTPException(status_code=500, detail="Error exporting data")

# WebSocket endpoint for real-time demo mode
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time data streaming in demo mode."""
    await manager.connect(websocket)
    try:
        # Send initial connection confirmation
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "status": "connected",
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get("type") == "ping":
                    await manager.send_personal_message(
                        json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        }),
                        websocket
                    )
                elif message.get("type") == "subscribe_demo":
                    # Start demo mode data streaming
                    await start_demo_mode(websocket)
                    
            except WebSocketDisconnect:
                break
            except json.JSONDecodeError:
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": "Invalid JSON"}),
                    websocket
                )
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await manager.send_personal_message(
                    json.dumps({"type": "error", "message": str(e)}),
                    websocket
                )
                break
                
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected normally")
    finally:
        manager.disconnect(websocket)

async def start_demo_mode(websocket: WebSocket):
    """Start streaming demo data updates."""
    import random
    
    try:
        # Send demo updates every 5 seconds
        for i in range(12):  # Run for 1 minute
            # Simulate enrollment update
            demo_data = {
                "type": "enrollment_update",
                "timestamp": datetime.now().isoformat(),
                "new_enrollments": random.randint(0, 5),
                "site_id": f"SITE{random.randint(1, 20):03d}",
                "total_enrollments": random.randint(800, 2000)
            }
            
            await manager.send_personal_message(json.dumps(demo_data), websocket)
            await asyncio.sleep(5)
            
        # Send completion message
        await manager.send_personal_message(
            json.dumps({
                "type": "demo_complete",
                "message": "Demo mode completed",
                "timestamp": datetime.now().isoformat()
            }),
            websocket
        )
        
    except Exception as e:
        logger.error(f"Demo mode error: {e}")
        await manager.send_personal_message(
            json.dumps({"type": "error", "message": "Demo mode interrupted"}),
            websocket
        )

def main():
    """Main entry point for running the application."""
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable for development
        log_level="info"
    )

if __name__ == "__main__":
    main()