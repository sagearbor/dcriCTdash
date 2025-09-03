# DCRI Clinical Trial Analytics Dashboard

FDA-compliant web application for real-time monitoring and analysis of clinical trial data at Duke Clinical Research Institute.

## Overview

This application provides comprehensive monitoring and analysis capabilities for clinical trials, featuring:

- **Real-time enrollment monitoring** with interactive dashboards
- **Risk-based monitoring** following ICH E6(R2) guidelines  
- **CDISC-compliant data management** with validation
- **Anomaly detection** for data quality assurance
- **3D data visualizations** for advanced analytics
- **Regulatory compliance** supporting FDA 21 CFR Part 11

## Technology Stack

- **Backend**: FastAPI 0.104+ with WebSocket support
- **Frontend**: Plotly Dash 2.14+ for interactive dashboards  
- **Database**: SQLite (development) → Azure SQL (production)
- **Data Processing**: Pandas 2.0+, NumPy 1.24+
- **Validation**: Pandera (schema validation), Pydantic v2 (API models)
- **Testing**: Pytest 7.4+ with >85% coverage requirement

## Project Structure

```
clinical-trial-dashboard/
├── app/                    # Main application source
│   ├── main.py             # FastAPI app definition
│   ├── dashboard.py        # Dash app layout and callbacks
│   ├── components/         # Reusable Dash components
│   ├── core/               # Business logic and analysis
│   └── data/
│       ├── models.py       # SQLAlchemy ORM models
│       ├── schemas.py      # Pandera validation schemas
│       ├── generator.py    # Mock data generator
│       └── database.py     # Database session management
├── tests/                  # Pytest tests
├── pyproject.toml          # Project dependencies and configuration
└── README.md
```

## Quick Start

### Prerequisites

- Python 3.10+ 
- Virtual environment (recommended)

### Installation

```bash
# Clone the repository (when available)
git clone <repository-url>
cd clinical-trial-dashboard

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Database Setup

```bash
# Initialize database and create tables
python -c "from app.data.database import initialize_database; initialize_database(with_sample_data=True)"
```

### Running the Application

```bash
# Start the application (development mode)
python app/main.py

# Or using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The application will be available at:
- Main application: http://localhost:8000
- API documentation: http://localhost:8000/api/docs
- Dashboard: http://localhost:8000/dashboard

### Development

```bash
# Run tests
pytest tests/ -v

# Run tests with coverage
pytest --cov=app --cov-report=html

# Code quality checks
ruff check .        # Linting
mypy app/          # Type checking
black .            # Code formatting
```

## Data Model

The application uses CDISC-compliant data models:

- **Sites**: Clinical trial site information with geographic data
- **Patients**: Subject enrollment and demographics (USUBJID standard)
- **Visits**: Patient visit scheduling and attendance
- **Labs**: Laboratory results following CDISC LB Domain standards

## Features

### Phase 1 (MVP)
- [x] Project infrastructure and dependencies
- [ ] CDISC-compliant data models  
- [ ] Mock data generation (20 sites, ~2,000 patients)
- [ ] FastAPI backend with basic endpoints
- [ ] Dash dashboard layout and components
- [ ] Basic enrollment monitoring charts

### Phase 2 (Risk Analytics)
- [ ] Real-time data streaming with WebSocket
- [ ] Site risk assessment algorithms
- [ ] Interactive site risk maps
- [ ] Data quality metrics and alerts
- [ ] Demo mode with live data simulation

### Phase 3 (Advanced Features)
- [ ] 3D laboratory data visualizations
- [ ] Advanced anomaly detection algorithms
- [ ] PDF report generation
- [ ] Audit trail and compliance features
- [ ] User authentication and authorization

## Configuration

### Environment Variables

```bash
# Database configuration
DATABASE_URL=sqlite:///clinical_trial.db    # Development default
DB_ECHO=false                               # SQL query logging

# Application settings
ENVIRONMENT=development                     # development/production
DEBUG=true                                 # Debug mode
```

### Production Deployment

For production deployment:

1. Set `DATABASE_URL` to Azure SQL connection string
2. Configure authentication and authorization
3. Enable HTTPS and security headers
4. Set up monitoring and logging
5. Configure backup and disaster recovery

## Compliance

This application is designed to meet:

- **FDA 21 CFR Part 11**: Electronic records and signatures
- **ICH E6(R2)**: Risk-based monitoring guidelines
- **CDISC Standards**: SDTM/ADaM data standards
- **HIPAA**: Data privacy and security requirements

## Contributing

1. Follow the established code style (Black, isort)
2. Maintain >85% test coverage
3. Update documentation for new features
4. Follow CDISC standards for data structures
5. Ensure FDA compliance requirements are met

## License

[License information to be determined]

## Support

For technical support or questions, contact the DCRI development team.

---

**Duke Clinical Research Institute**  
Clinical Trial Analytics Dashboard  
Version 0.1.0