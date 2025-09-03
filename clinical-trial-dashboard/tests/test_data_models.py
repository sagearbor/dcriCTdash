"""
Test suite for data models and database operations.

Tests SQLAlchemy models, CDISC compliance, and database functionality.
"""

import pytest
from datetime import date, datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.data.models import Base, Site, Patient, Visit, Lab

# Test database setup
@pytest.fixture
def test_db():
    """Create in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def sample_site():
    """Create sample site for testing."""
    return Site(
        site_id="SITE001",
        site_name="Test Medical Center",
        country="US",
        latitude=35.7796,
        longitude=-78.6382,
        enrollment_target=100
    )

@pytest.fixture  
def sample_patient(sample_site):
    """Create sample patient for testing."""
    return Patient(
        usubjid="DCRI-SITE001-0001",
        site_id=sample_site.site_id,
        date_of_enrollment=date(2024, 1, 15),
        age=45,
        sex="M",
        race="WHITE"
    )

class TestSiteModel:
    """Test Site model functionality."""
    
    def test_create_site(self, test_db, sample_site):
        """Test creating a site record."""
        test_db.add(sample_site)
        test_db.commit()
        
        retrieved_site = test_db.query(Site).filter_by(site_id="SITE001").first()
        assert retrieved_site is not None
        assert retrieved_site.site_name == "Test Medical Center"
        assert retrieved_site.country == "US"
        assert retrieved_site.enrollment_target == 100
    
    def test_site_string_representation(self, sample_site):
        """Test site string representation."""
        site_str = str(sample_site)
        assert "SITE001" in site_str
        assert "Test Medical Center" in site_str

class TestPatientModel:
    """Test Patient model functionality."""
    
    def test_create_patient(self, test_db, sample_site, sample_patient):
        """Test creating a patient record."""
        test_db.add(sample_site)
        test_db.add(sample_patient)
        test_db.commit()
        
        retrieved_patient = test_db.query(Patient).filter_by(usubjid="DCRI-SITE001-0001").first()
        assert retrieved_patient is not None
        assert retrieved_patient.site_id == "SITE001"
        assert retrieved_patient.age == 45
        assert retrieved_patient.sex == "M"
    
    def test_patient_site_relationship(self, test_db, sample_site, sample_patient):
        """Test patient-site relationship."""
        test_db.add(sample_site)
        test_db.add(sample_patient)
        test_db.commit()
        
        patient = test_db.query(Patient).filter_by(usubjid="DCRI-SITE001-0001").first()
        assert patient.site.site_name == "Test Medical Center"
    
    def test_cdisc_usubjid_format(self, sample_patient):
        """Test USUBJID follows CDISC format."""
        usubjid = sample_patient.usubjid
        assert usubjid.startswith("DCRI-")
        assert "SITE001" in usubjid
        assert len(usubjid.split("-")) == 3  # Study-Site-Subject format

class TestVisitModel:
    """Test Visit model functionality."""
    
    def test_create_visit(self, test_db, sample_site, sample_patient):
        """Test creating a visit record."""
        visit = Visit(
            visit_id="VIS000001",
            usubjid=sample_patient.usubjid,
            visit_name="Screening",
            visit_num=1,
            visit_date=date(2024, 1, 10)
        )
        
        test_db.add(sample_site)
        test_db.add(sample_patient)
        test_db.add(visit)
        test_db.commit()
        
        retrieved_visit = test_db.query(Visit).filter_by(visit_id="VIS000001").first()
        assert retrieved_visit is not None
        assert retrieved_visit.visit_name == "Screening"
        assert retrieved_visit.visit_num == 1

class TestLabModel:
    """Test Lab model functionality."""
    
    def test_create_lab_result(self, test_db, sample_site, sample_patient):
        """Test creating a lab result record."""
        visit = Visit(
            visit_id="VIS000001",
            usubjid=sample_patient.usubjid,
            visit_name="Baseline",
            visit_num=2,
            visit_date=date(2024, 1, 15)
        )
        
        lab = Lab(
            lab_id="LAB00000001",
            usubjid=sample_patient.usubjid,
            visit_id=visit.visit_id,
            lbtestcd="GLUC",
            lbtest="Glucose",
            lborres="95",
            lbstresn=95.0,
            lbstresu="mg/dL",
            lbnrind="NORMAL",
            collection_date=date(2024, 1, 15)
        )
        
        test_db.add(sample_site)
        test_db.add(sample_patient)
        test_db.add(visit)
        test_db.add(lab)
        test_db.commit()
        
        retrieved_lab = test_db.query(Lab).filter_by(lab_id="LAB00000001").first()
        assert retrieved_lab is not None
        assert retrieved_lab.lbtestcd == "GLUC"
        assert retrieved_lab.lbstresn == 95.0
        assert retrieved_lab.lbnrind == "NORMAL"
    
    def test_lab_cdisc_compliance(self, test_db, sample_site, sample_patient):
        """Test lab result CDISC LB domain compliance."""
        visit = Visit(
            visit_id="VIS000001",
            usubjid=sample_patient.usubjid,
            visit_name="Baseline",
            visit_num=2,
            visit_date=date(2024, 1, 15)
        )
        
        lab = Lab(
            lab_id="LAB00000001",
            usubjid=sample_patient.usubjid,
            visit_id=visit.visit_id,
            lbtestcd="HGB",
            lbtest="Hemoglobin",
            lborres="14.2",
            lbstresn=14.2,
            lbstresu="g/dL",
            lbnrind="NORMAL",
            collection_date=date(2024, 1, 15)
        )
        
        # Test CDISC field presence
        assert hasattr(lab, 'lbtestcd')  # Test code
        assert hasattr(lab, 'lbtest')    # Test name
        assert hasattr(lab, 'lborres')   # Original result
        assert hasattr(lab, 'lbstresn')  # Standardized numeric result
        assert hasattr(lab, 'lbstresu')  # Standardized units
        assert hasattr(lab, 'lbnrind')   # Normal range indicator

class TestModelRelationships:
    """Test model relationships and constraints."""
    
    def test_site_patient_relationship(self, test_db, sample_site):
        """Test site can have multiple patients."""
        patient1 = Patient(
            usubjid="DCRI-SITE001-0001",
            site_id=sample_site.site_id,
            date_of_enrollment=date(2024, 1, 15),
            age=45,
            sex="M",
            race="WHITE"
        )
        
        patient2 = Patient(
            usubjid="DCRI-SITE001-0002", 
            site_id=sample_site.site_id,
            date_of_enrollment=date(2024, 1, 16),
            age=38,
            sex="F",
            race="BLACK OR AFRICAN AMERICAN"
        )
        
        test_db.add(sample_site)
        test_db.add(patient1)
        test_db.add(patient2)
        test_db.commit()
        
        site = test_db.query(Site).filter_by(site_id="SITE001").first()
        assert len(site.patients) == 2