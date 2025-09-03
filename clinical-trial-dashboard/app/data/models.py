"""
SQLAlchemy ORM Models

CDISC-compliant database models for clinical trial data including sites, 
patients, visits, and laboratory results following CDISC LB Domain standards.
"""

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    Column, String, Integer, Float, DateTime, Date, Boolean, 
    Text, ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Session
from sqlalchemy.sql import func

# SQLAlchemy base class
Base = declarative_base()

class Site(Base):
    """
    Clinical trial site information.
    
    Attributes:
        site_id: Unique site identifier
        site_name: Site name/institution  
        country: Country code (ISO 3166-1 alpha-2)
        latitude: Geographic latitude for mapping
        longitude: Geographic longitude for mapping
        enrollment_target: Target patient enrollment count
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    __tablename__ = "sites"
    
    site_id = Column(String(20), primary_key=True, index=True)
    site_name = Column(String(200), nullable=False)
    country = Column(String(2), nullable=False)  # ISO country code
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    enrollment_target = Column(Integer, nullable=False, default=100)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    patients = relationship("Patient", back_populates="site")
    
    def __repr__(self) -> str:
        return f"<Site(site_id='{self.site_id}', name='{self.site_name}')>"

class Patient(Base):
    """
    Patient/subject information following CDISC standards.
    
    Attributes:
        usubjid: Unique Subject Identifier (CDISC standard)
        site_id: Reference to clinical site
        date_of_enrollment: Patient enrollment date
        age: Patient age at enrollment
        sex: Patient sex (M/F/U/UNDIFFERENTIATED)
        race: Patient race category
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    __tablename__ = "patients"
    
    usubjid = Column(String(50), primary_key=True, index=True)  # CDISC standard
    site_id = Column(String(20), ForeignKey("sites.site_id"), nullable=False)
    date_of_enrollment = Column(Date, nullable=False)
    age = Column(Integer, nullable=True)
    sex = Column(String(20), nullable=True)  # M, F, U, UNDIFFERENTIATED
    race = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    site = relationship("Site", back_populates="patients")
    visits = relationship("Visit", back_populates="patient")
    labs = relationship("Lab", back_populates="patient")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_patient_site_enrollment", site_id, date_of_enrollment),
    )
    
    def __repr__(self) -> str:
        return f"<Patient(usubjid='{self.usubjid}', site='{self.site_id}')>"

class Visit(Base):
    """
    Patient visit information following CDISC standards.
    
    Attributes:
        visit_id: Unique visit identifier
        usubjid: Reference to patient (CDISC standard)
        visit_name: Visit name/description
        visit_num: Visit sequence number
        visit_date: Actual visit date
        created_at: Record creation timestamp  
        updated_at: Record last update timestamp
    """
    __tablename__ = "visits"
    
    visit_id = Column(String(50), primary_key=True, index=True)
    usubjid = Column(String(50), ForeignKey("patients.usubjid"), nullable=False)
    visit_name = Column(String(100), nullable=False)  # e.g., "Screening", "Week 4"
    visit_num = Column(Integer, nullable=False)  # Sequential visit number
    visit_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    patient = relationship("Patient", back_populates="visits")
    labs = relationship("Lab", back_populates="visit")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("usubjid", "visit_num", name="uq_patient_visit_num"),
        Index("idx_visit_patient_date", usubjid, visit_date),
    )
    
    def __repr__(self) -> str:
        return f"<Visit(visit_id='{self.visit_id}', patient='{self.usubjid}', visit_num={self.visit_num})>"

class Lab(Base):
    """
    Laboratory results following CDISC LB Domain standards.
    
    Attributes:
        lab_id: Unique lab result identifier
        usubjid: Reference to patient (CDISC standard)
        visit_id: Reference to visit
        lbtestcd: Lab test code (CDISC standard)
        lbtest: Lab test name (CDISC standard)
        lborres: Original result as collected (CDISC standard)
        lbstresn: Standardized numeric result (CDISC standard)
        lbstresu: Standardized result units (CDISC standard)
        lbnrind: Reference range indicator (CDISC standard)
        collection_date: Lab specimen collection date
        created_at: Record creation timestamp
        updated_at: Record last update timestamp
    """
    __tablename__ = "labs"
    
    lab_id = Column(String(50), primary_key=True, index=True)
    usubjid = Column(String(50), ForeignKey("patients.usubjid"), nullable=False)
    visit_id = Column(String(50), ForeignKey("visits.visit_id"), nullable=False)
    
    # CDISC LB Domain fields
    lbtestcd = Column(String(20), nullable=False)  # e.g., "GLUC", "HGB"
    lbtest = Column(String(100), nullable=False)   # e.g., "Glucose", "Hemoglobin"
    lborres = Column(String(100), nullable=True)   # Original result
    lbstresn = Column(Float, nullable=True)        # Standardized numeric result
    lbstresu = Column(String(20), nullable=True)   # Standardized units
    lbnrind = Column(String(20), nullable=True)    # Normal/Abnormal indicator
    
    collection_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    patient = relationship("Patient", back_populates="labs")
    visit = relationship("Visit", back_populates="labs")
    
    # Indexes for performance
    __table_args__ = (
        Index("idx_lab_patient_test", usubjid, lbtestcd),
        Index("idx_lab_test_date", lbtestcd, collection_date),
        Index("idx_lab_abnormal", lbnrind),
    )
    
    def __repr__(self) -> str:
        return f"<Lab(lab_id='{self.lab_id}', patient='{self.usubjid}', test='{self.lbtestcd}')>"

# Utility functions for model operations
def get_enrollment_stats(db: Session) -> dict:
    """Get enrollment statistics across all sites."""
    # Placeholder - will implement with actual database queries
    return {"total_patients": 0, "total_sites": 0}

def get_site_risk_scores(db: Session) -> List[dict]:
    """Calculate risk scores for all sites.""" 
    # Placeholder - will implement risk-based monitoring algorithms
    return []

def get_data_quality_metrics(db: Session) -> dict:
    """Calculate data quality metrics."""
    # Placeholder - will implement data quality assessments
    return {"completeness": 0.0, "accuracy": 0.0}