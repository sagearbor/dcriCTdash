"""
Database Session Management

SQLAlchemy database configuration, session management, and initialization utilities.
Designed for easy migration from SQLite (development) to Azure SQL (production).
"""

import os
from typing import Generator, Optional
from sqlalchemy import create_engine, Engine, MetaData
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging

# Import models
from .models import Base

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseConfig:
    """
    Database configuration management.
    
    Handles different database configurations for development, testing, and production.
    """
    
    def __init__(self):
        self.database_url = self._get_database_url()
        self.engine = self._create_engine()
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def _get_database_url(self) -> str:
        """
        Get database URL based on environment configuration.
        
        Returns:
            str: Database connection URL
        """
        # Check for environment-specific database URL
        db_url = os.getenv("DATABASE_URL")
        
        if db_url:
            # Production or custom database URL
            logger.info("Using DATABASE_URL from environment")
            return db_url
        
        # Development default - SQLite
        db_path = os.getenv("DB_PATH", "clinical_trial.db")
        sqlite_url = f"sqlite:///{db_path}"
        logger.info(f"Using SQLite database: {sqlite_url}")
        
        return sqlite_url
    
    def _create_engine(self) -> Engine:
        """
        Create SQLAlchemy engine with appropriate configuration.
        
        Returns:
            Engine: Configured SQLAlchemy engine
        """
        if self.database_url.startswith("sqlite"):
            # SQLite-specific configuration
            engine = create_engine(
                self.database_url,
                connect_args={"check_same_thread": False},  # Allow multi-threading
                poolclass=StaticPool,  # Use static pool for SQLite
                echo=os.getenv("DB_ECHO", "false").lower() == "true"  # SQL logging
            )
        else:
            # PostgreSQL/Azure SQL configuration
            engine = create_engine(
                self.database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,  # Verify connections before use
                echo=os.getenv("DB_ECHO", "false").lower() == "true"
            )
        
        logger.info(f"Created database engine: {type(engine).__name__}")
        return engine
    
    def get_session(self) -> Session:
        """
        Get a new database session.
        
        Returns:
            Session: SQLAlchemy session instance
        """
        return self.SessionLocal()

# Global database configuration instance
db_config = DatabaseConfig()

# Dependency injection for FastAPI
def get_database_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database session injection.
    
    Yields:
        Session: Database session that will be automatically closed
    """
    session = db_config.get_session()
    try:
        yield session
    finally:
        session.close()

@contextmanager
def get_db_session():
    """
    Context manager for database sessions.
    
    Yields:
        Session: Database session with automatic cleanup
    """
    session = db_config.get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()

def create_database_tables(drop_existing: bool = False) -> None:
    """
    Create all database tables.
    
    Args:
        drop_existing: Whether to drop existing tables first
    """
    if drop_existing:
        logger.info("Dropping existing tables...")
        Base.metadata.drop_all(bind=db_config.engine)
    
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=db_config.engine)
    logger.info("Database tables created successfully")

def check_database_connection() -> bool:
    """
    Check database connectivity.
    
    Returns:
        bool: True if connection is successful
    """
    try:
        from sqlalchemy import text
        with get_db_session() as session:
            # Simple connectivity test
            session.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def get_database_info() -> dict:
    """
    Get database configuration information.
    
    Returns:
        dict: Database configuration details
    """
    return {
        "database_url": db_config.database_url.split("://")[0] + "://***",  # Hide credentials
        "engine_type": type(db_config.engine).__name__,
        "pool_size": getattr(db_config.engine.pool, 'size', None),
        "echo_enabled": db_config.engine.echo,
        "tables_exist": check_tables_exist()
    }

def check_tables_exist() -> bool:
    """
    Check if all required tables exist in the database.
    
    Returns:
        bool: True if all tables exist
    """
    try:
        from sqlalchemy import inspect
        inspector = inspect(db_config.engine)
        existing_tables = inspector.get_table_names()
        
        required_tables = ["sites", "patients", "visits", "labs"]
        tables_exist = all(table in existing_tables for table in required_tables)
        
        if tables_exist:
            logger.info("All required tables exist")
        else:
            missing_tables = [t for t in required_tables if t not in existing_tables]
            logger.warning(f"Missing tables: {missing_tables}")
        
        return tables_exist
    except Exception as e:
        logger.error(f"Error checking tables: {e}")
        return False

def initialize_database(with_sample_data: bool = False) -> None:
    """
    Initialize database with schema and optionally sample data.
    
    Args:
        with_sample_data: Whether to populate with mock data
    """
    logger.info("Initializing database...")
    
    # Create tables
    create_database_tables(drop_existing=False)
    
    # Check connection
    if not check_database_connection():
        raise RuntimeError("Failed to establish database connection")
    
    if with_sample_data:
        logger.info("Loading sample data...")
        populate_sample_data()
    
    logger.info("Database initialization complete")

def populate_sample_data() -> None:
    """
    Populate database with mock clinical trial data.
    """
    try:
        from .generator import generate_mock_data
        from .models import Site, Patient, Visit, Lab
        
        # Generate mock data
        mock_data = generate_mock_data()
        
        with get_db_session() as session:
            # Clear existing data
            session.query(Lab).delete()
            session.query(Visit).delete()
            session.query(Patient).delete()
            session.query(Site).delete()
            
            # Insert sites
            for _, site_row in mock_data["sites"].iterrows():
                site = Site(**site_row.to_dict())
                session.add(site)
            
            # Insert patients
            for _, patient_row in mock_data["patients"].iterrows():
                patient = Patient(**patient_row.to_dict())
                session.add(patient)
            
            # Insert visits
            for _, visit_row in mock_data["visits"].iterrows():
                visit = Visit(**visit_row.to_dict())
                session.add(visit)
            
            # Insert labs
            for _, lab_row in mock_data["labs"].iterrows():
                lab = Lab(**lab_row.to_dict())
                session.add(lab)
            
            session.commit()
            logger.info("Sample data populated successfully")
            
    except Exception as e:
        logger.error(f"Error populating sample data: {e}")
        raise

# Database utility functions for the application
def get_table_counts() -> dict:
    """
    Get record counts for all main tables.
    
    Returns:
        dict: Table names and their record counts
    """
    try:
        with get_db_session() as session:
            from .models import Site, Patient, Visit, Lab
            
            counts = {
                "sites": session.query(Site).count(),
                "patients": session.query(Patient).count(), 
                "visits": session.query(Visit).count(),
                "labs": session.query(Lab).count()
            }
            
            return counts
    except Exception as e:
        logger.error(f"Error getting table counts: {e}")
        return {"error": str(e)}

def backup_database(backup_path: str) -> bool:
    """
    Create a backup of the database (SQLite only).
    
    Args:
        backup_path: Path for backup file
        
    Returns:
        bool: True if backup successful
    """
    try:
        if not db_config.database_url.startswith("sqlite"):
            logger.warning("Database backup only supported for SQLite")
            return False
        
        import shutil
        db_path = db_config.database_url.replace("sqlite:///", "")
        shutil.copy2(db_path, backup_path)
        logger.info(f"Database backup created: {backup_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")
        return False

# Export main components
__all__ = [
    "db_config",
    "get_database_session", 
    "get_db_session",
    "create_database_tables",
    "check_database_connection",
    "get_database_info",
    "initialize_database",
    "populate_sample_data",
    "get_table_counts",
    "backup_database"
]