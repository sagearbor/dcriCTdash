# **Product Requirements Prompt (PRP): DCRI Interactive Clinical Trial Oversight Dashboard**

## 1. Goals & Overview

This project is to build a web-based **Clinical Trial Oversight Dashboard** for DCRI clinical research professionals. The tool will provide an interactive, real-time interface to monitor study progress, perform risk-based monitoring by detecting data anomalies automatically, and enable direct action to address issues.

The system will prioritize:

1. **Accelerated Data Review:** Surfacing key trends, outliers, and anomalies automatically.
  
2. **Actionability:** Enabling users to act on insights directly from the dashboard (e.g., notify sites).
  
3. **Regulatory Compliance:** Adhering to CDISC data standards and FDA guidance for risk-based monitoring.
  

## 2. User Personas

- **P1: Sam, the Study Lead:** Needs a high-level view of site performance, enrollment trends, and key risk indicators to manage trial execution and timelines.
  
- **P2: Alex, the Clinical Data Manager (CDM):** Needs to drill down into site/patient data to find outliers, inconsistencies, and ensure data integrity.
  
- **P3: Jennifer, the Study Coordinator:** Needs real-time site performance metrics to proactively address local data collection or enrollment issues.
  

## 3. User Stories (Phased Roadmap)

**Phase 1: MVP - Core Monitoring & Visualization** [COMPLETED ✅]

- **US1:** [DONE] As Sam, I want a chart of cumulative enrollment over time, compared against a projected target line, to track overall study progress.
  
- **US2:** [DONE] As Sam, I want an interactive map of all study sites, color-coded by a composite risk score, so I can quickly identify high-risk sites.
  
- **US3:** [DONE] As Alex, I want a detailed data table that is linked to the charts, allowing me to sort, filter, and inspect the raw data behind the visualizations.
  
- **US4:** [DONE] As Alex, I want a toggle to enter a "Demo Mode" which activates a mock data generator, so I can see how the dashboard behaves with live, streaming data.
  
- **US5:** [DONE] As a user, I want a button to download the currently filtered data as a CSV file.
  

**Phase 2: Advanced Analytics & Actionability**

- **US6:** As Alex, I want to view box plots of key lab value distributions by site to spot systemic measurement differences.
  
- **US7:** As Alex, I want the dashboard to automatically flag patients with data quality issues (e.g., missing key data, out-of-range lab values) in a dedicated "Data Quality" table.
  
- **US8:** As Sam, I want to click on a high-risk site on the map and use a "Notify Site" button that generates a pre-populated email draft.
  
- **US9:** As Alex, I want to click a patient ID and see a "Patient Profile" modal with a longitudinal chart of their key biomarkers.
  

**Phase 3: 3D Exploration & Reporting**

- **US10:** As Alex, I want to visualize lab data in a 3D scatter plot (Site vs. Patient vs. Lab Value) to identify complex patterns and outliers.
  
- **US11:** As Sam, I want to see a Sankey diagram of the patient disposition funnel (Screened -> Enrolled -> Completed) to understand subject attrition.
  
- **US12:** As Sam, I want a button to generate a PDF summary report of the current dashboard view to share in meetings.
  
- **US13:** As a user, I want a text box with an AI-generated natural language summary of significant changes since my last login (UI placeholder for future LLM integration).
  

## 4. Technical Specifications & Context

### 4.1. Technical Stack

- **Language:** Python 3.11+
  
- **Backend API:** FastAPI (for data endpoints and WebSocket streaming in "Demo Mode")
  
- **Frontend Framework:** Plotly/Dash
  
- **Data Processing:** Pandas, NumPy
  
- **Database:** SQLite via SQLAlchemy for local development. Code must use the ORM for easy migration to a production DB like Azure SQL.
  
- **Data Validation:** `pandera` for schema and data integrity checks.
  
- **Testing:** `pytest`
  
- **PDF Generation:** `fpdf2`
  

### 4.2. Architecture & File Structure

```
/clinical-trial-dashboard/
|-- app/                    # Main application source
|   |-- __init__.py
|   |-- main.py             # FastAPI app definition
|   |-- dashboard.py        # Dash app layout and callbacks
|   |-- components/         # Reusable Dash components (charts, tables)
|   |-- core/               # Business logic, analysis, anomaly detection
|   |-- data/
|   |   |-- models.py       # SQLAlchemy ORM models
|   |   |-- schemas.py      # Pandera validation schemas
|   |   |-- generator.py    # Mock data generator
|   |   |-- database.py     # DB session management
|-- tests/                  # Pytest tests
|-- .venv/
|-- pyproject.toml          # Project metadata and dependencies (use Poetry or PDM)
|-- README.md
```

### 4.3. Data Model & Validation

Implement the following SQLAlchemy models in `app/data/models.py` and corresponding `pandera` schemas in `app/data/schemas.py`. The model should be inspired by the CDISC LB Domain standard.

- **`sites`**: `site_id` (PK, str), `site_name` (str), `country` (str), `latitude` (float), `longitude` (float), `enrollment_target` (int)
  
- **`patients`**: `usubjid` (PK, str, "Unique Subject ID"), `site_id` (FK), `date_of_enrollment` (datetime), `age` (int), `sex` (str), `race` (str)
  
- **`visits`**: `visit_id` (PK, int), `usubjid` (FK), `visit_name` (str), `visit_num` (int), `visit_date` (datetime)
  
- **`labs`**: `lab_id` (PK, int), `usubjid` (FK), `visit_id` (FK), `lbtestcd` (str, "Lab Test Short Code"), `lbtest` (str, "Lab Test Name"), `lborres` (float, "Original Result"), `lborresu` (str, "Original Units"), `lbstresn` (float, "Standardized Numeric Result"), `lbstresu` (str, "Standardized Units"), `lbornrlo` (float, "Normal Range Low"), `lbornrhi` (float, "Normal Range High")
  

### 4.4. Anomaly Definitions

Implement functions in `app/core/` to detect the following:

- **Enrollment Lag:** Site enrollment rate is < 80% of the projected linear target.
  
- **Lab Outlier (z-score):** A lab value's site-specific z-score is 3 or $\< -3$.
  
- **Lab Outlier (Clinical):** A lab value is 3times the upper limit of normal (`lbornrhi`).
  
- **Data Quality Issue:** Key fields (`lbstresn`, `visit_date`) are missing.
  

## 5. Agent Runbook / Implementation Plan

**Phase 1: MVP Setup**

1. **Initialize Project:** Create the file structure from 4.2. Set up the virtual environment and install dependencies.
  
2. **Data Layer:** Implement the SQLAlchemy models (`models.py`) and Pandera schemas (`schemas.py`).
  
3. **Mock Data:** In `generator.py`, create a function to populate the SQLite DB with realistic data for 20 sites and ~2,000 patients, including longitudinal lab values.
  
4. **Backend API:** In `main.py`, create FastAPI endpoints to query sites, patients, and labs from the database.
  
5. **Basic Dashboard:** In `dashboard.py`, create the main Dash app layout. Fetch data from the FastAPI endpoints.
  
6. **Implement Visuals:** Create the Enrollment Timeline Chart (US1) and the interactive Site Risk Map (US2). The initial risk score can be based solely on enrollment lag.
  
7. **Implement Data Table:** Add an interactive `dash_table.DataTable` (US3).
  
8. **Implement Demo Mode & CSV Export:** Implement the data streaming toggle (US4) using a WebSocket connection from FastAPI and the CSV download button (US5).
  
9. **Initial Tests:** Write `pytest` tests for data model validation and API endpoint functionality.
  

**Phase 2: Analytics & Actions** 10. **Link Visuals:** Create callbacks so that filtering the data table updates the map and charts.
11. **Implement Box Plots:** Add the lab value distribution component (US6).
12. **Data Quality Module:** Implement the anomaly detection functions from 4.4. Display results in a "Data Quality" table (US7). Update the map's risk score to be a composite of all detected anomalies.
13. **Actionability:** Add the "Notify Site" button. The callback should open a `dcc.Modal` with a pre-filled `dcc.Textarea` (e.g., "Subject: Urgent: Enrollment Lag at Site X..."). (US8)
14. **Patient Profile:** Implement the patient drill-down modal (US9).

**Phase 3: Advanced Views & Reporting ✅ COMPLETED**
15. **3D Visualization:** ✅ COMPLETED - Implemented comprehensive 3D scatter plot component for lab data exploration (US10). Features include:
    - Interactive 3D visualization using Plotly Scatter3d with Site vs Patient vs Lab Value dimensions
    - Configurable color mapping by site, age group, or sex
    - Dynamic size scaling by lab value, age, or uniform sizing
    - Full integration with existing site and country filters
    - Rich hover tooltips showing patient details, site information, demographics, and lab values
    - Sample data fallback with realistic 3D distributions for development/testing
    - Error handling and responsive design
16. **Patient Funnel:** ✅ COMPLETED - Built comprehensive Sankey diagram for patient disposition (US11). Features include:
    - Dynamic patient status assignment with realistic distributions (Completed 70%, Active 10%, Withdrawn 15%, Screen Failed 5%)
    - Three view modes: Overall Study Flow, By Site, and By Country groupings
    - Configurable number display (absolute counts, percentages, or both)
    - Multi-level flow visualization showing transitions between study phases
    - Color-coded nodes and links with professional clinical trial styling
    - Full integration with site and country filters
    - Sample data with proper clinical trial flow patterns
17. **PDF Reporting:** ✅ COMPLETED - Comprehensive PDF report generation system (US12). Features include:
    - Four report types: Executive Summary, Detailed Analysis, Site Performance, Data Quality Report
    - Configurable section inclusion (enrollment, site map, lab analysis, data quality, disposition, 3D labs)
    - Professional PDF formatting using fpdf2 with proper headers, footers, and clinical styling
    - Filter context preservation showing applied site/country selections in report
    - Real-time generation status feedback with success/error indicators
    - Sample PDF download capability with demo data
    - Timestamp-based filename generation for organization
    - Comprehensive error handling and fallback reporting
18. **AI Summary Placeholder:** ✅ COMPLETED - Full UI implementation for future LLM integration (US13). Features include:
    - Professional interface with configurable summary types (Changes Since Last Login, Key Insights, Risk Alerts, Enrollment Trends)
    - Analysis depth selection (Brief Overview, Detailed Analysis, Executive Summary)
    - Disabled state with clear messaging about future LLM integration
    - Placeholder text area with preview of planned AI capabilities
    - Clean card-based design consistent with dashboard styling
    - Ready for backend AI service integration when available
19. **Finalize Testing:** ✅ COMPLETED - Comprehensive test suite implemented covering all dashboard functionality:
    - Created `test_phase3_features.py` with tests for 3D scatter plots, Sankey diagrams, and PDF generation
    - Added `test_dashboard_core.py` with extensive coverage of dashboard callbacks and integration
    - All core features now have robust pytest coverage with mock data validation
    - Integration testing ensures UI components work correctly with backend data processing
    - Test coverage includes error handling and edge cases for production reliability

**Phase 4A: Statistical Field Detection (Simplified Implementation) ✅ COMPLETED**

Phase 4A implements the core field detection capability (US15) using statistical correlation analysis - a simplified but effective approach to the full harmonization platform outlined in Phase 4 below.

- **US15:** ✅ COMPLETED - Statistical field detection system that intelligently infers semantic meaning of ambiguous column names:
    - Implemented `StatisticalFieldDetector` class in `/app/core/field_detection.py`
    - Successfully detects binary fields representing sex/gender by analyzing correlations with height, weight, and hemoglobin
    - Identifies vital status fields through distribution analysis and age correlations  
    - Added interactive UI with confidence threshold slider and validation interface
    - Demonstrates 80% confidence detection of "s_01" as sex field using clinical knowledge patterns
    - Real-time analysis with user validation workflow for detected field mappings
    - Foundation for more advanced ML-based detection in future phases

**Technical Implementation Highlights:**
- Created sample clinical data generator with realistic correlations for testing
- Implemented statistical t-tests and correlation analysis for group differences
- Added clinical domain knowledge patterns (height/weight differences by sex)
- Built confidence scoring system with evidence tracking
- Integrated seamlessly with existing dashboard UI and Bootstrap styling

**Phase 4: Automated Clinical Data Harmonization Platform (Future Roadmap)**

Phase 4 represents a significant evolution from a monitoring dashboard to a comprehensive data harmonization platform. This phase will enable the system to automatically ingest, normalize, and integrate clinical trial data from diverse sources and formats into a unified data model.

- **US14:** As a clinical data manager, I want to upload files in various formats (CDISC, FHIR, OMOP, REDCap CSV, JSON) and have the system automatically detect and map fields to standardized concepts without requiring manual data dictionaries.

- **US15:** As Alex, I want the system to intelligently infer that a binary column with header "s_01" represents sex/gender by analyzing statistical relationships with other identified fields (e.g., height, hormone levels).

- **US16:** As a data scientist, I want an ML-powered semantic type detection engine that can classify columns into clinical concepts (patient ID, lab values, demographics) with confidence scores.

- **US17:** As a study coordinator, I want a web interface to review and validate automatically detected field mappings before they are applied to the data transformation pipeline.

- **US18:** As Sam, I want all harmonized data to be automatically loaded into our target data model (OMOP CDM) with proper vocabulary mapping to standard concept IDs.

### Phase 4 Technical Implementation Roadmap

**4.1 Foundation - Data Ingestion & Orchestration Infrastructure**

- **Task 4.1.1:** Set up Medallion Architecture (Bronze/Silver/Gold layers)
  - Implement cloud storage infrastructure for data lake layers
  - Configure Bronze layer for immutable raw data storage
  - Set up Silver layer for semantic enrichment and profiling
  - Establish Gold layer for unified OMOP CDM target schema

- **Task 4.1.2:** Deploy Dagster Workflow Orchestrator
  - Install and configure Dagster for asset-aware pipeline orchestration
  - Create development, staging, and production environments
  - Implement automatic data lineage tracking across all layers
  - Set up integrated data quality monitoring and alerting

- **Task 4.1.3:** Build Modular Ingestion Framework
  - Implement factory pattern-based ingestion service with format-specific plugins
  - Create parsers for CDISC SDTM/ADaM using `odmlib` and `cdisc-rules-engine`
  - Build FHIR parser using `fhirpack` for Bundle resource processing
  - Develop REDCap integration using `PyCap` for API-based data extraction
  - Add generic CSV/JSON parsers with `pandas` and `dask` for large files

**4.2 Core Intelligence - Single-Column Semantic Inference**

- **Task 4.2.1:** Implement Data Profiling Pipeline
  - Create comprehensive feature engineering for column analysis
  - Extract character-level, word-level, and statistical features
  - Integrate BioBERT embeddings for biomedical domain context
  - Generate rich metadata profiles for Silver layer annotation

- **Task 4.2.2:** Deploy Sherlock Baseline Model
  - Integrate pre-trained Sherlock deep learning model for semantic type detection
  - Create training data bootstrapping system with cleanlab for label quality
  - Implement 78+ semantic type classification with confidence scoring
  - Add clinical domain-specific types (sex, lab values, patient IDs)

- **Task 4.2.3:** Enhance with Context-Aware Models
  - Implement Sato model for table context and co-occurrence patterns
  - Add Pythagoras GNN model for numerical data with graph-based inference
  - Integrate AutoType system for algorithmic pattern detection
  - Create hierarchical inference pipeline with confidence propagation

**4.3 Advanced Intelligence - Multi-Column Relational Inference**

- **Task 4.3.1:** Build Relational Feature Engineering
  - Implement statistical relationship analysis between columns
  - Create feature vectors for categorical vs continuous comparisons
  - Add correlation analysis and significance testing capabilities
  - Develop cross-field pattern recognition for ambiguous columns

- **Task 4.3.2:** Train Multi-Column Inference Models
  - Build XGBoost/Random Forest classifier for relational fingerprints
  - Create bootstrapped training dataset from public clinical data
  - Implement iterative refinement with anchor column promotion
  - Add domain knowledge patterns (height/weight relationships with sex)

- **Task 4.3.3:** Develop Pattern-Based Detection
  - Implement regex-based detection for obvious patterns (dates, IDs, emails)
  - Create clinical vocabulary dictionaries for value matching
  - Add checksum validation for coded identifiers
  - Build ensemble voting system combining multiple detection methods

**4.4 Normalization Engine - OMOP CDM Integration**

- **Task 4.4.1:** Implement Vocabulary Mapping Services
  - Integrate UMLS Python client for terminology crosswalking
  - Add SNOMED CT mapping using PyMedTermino for full-text search
  - Implement probabilistic mapping with confidence scoring
  - Create Bayesian disambiguation using prevalence priors

- **Task 4.4.2:** Build OMOP ETL Pipeline
  - Set up OMOP CDM database schema (PostgreSQL/SQL Server)
  - Integrate OHDSI tools (White Rabbit, Rabbit-in-a-Hat) for mapping specification
  - Implement The Hyve's Delphyne framework for Python-based ETL execution
  - Add Usagi integration for semi-automated concept mapping

- **Task 4.4.3:** Create Semantic-to-OMOP Bridge
  - Map inferred semantic types to OMOP table/field combinations
  - Implement NLP-based metadata mapping using BioBERT embeddings
  - Create version-controlled mapping configuration system
  - Add support for custom clinical data types and extensions

**4.5 Validation & Quality Assurance**

- **Task 4.5.1:** Integrate OHDSI Data Quality Dashboard
  - Implement automated post-load quality validation
  - Create comprehensive data quality rules and thresholds
  - Add alerts for quality violations and mapping failures
  - Generate detailed quality reports with actionable recommendations

- **Task 4.5.2:** Build User Review Interface
  - Create web interface for mapping validation and correction
  - Implement confidence-based review prioritization
  - Add bulk approval/rejection workflows for efficient review
  - Create audit trail for all manual mapping decisions

- **Task 4.5.3:** Establish MLOps Pipeline
  - Implement model versioning and performance monitoring
  - Create retraining workflows for semantic detection models
  - Add A/B testing framework for model improvements
  - Set up drift detection and model refresh automation

**4.6 Integration & Operationalization**

- **Task 4.6.1:** Dashboard Integration
  - Extend existing dashboard to display harmonization pipeline status
  - Add data source management interface for upload and monitoring
  - Create field mapping visualization and confidence reporting
  - Implement real-time processing status and error handling

- **Task 4.6.2:** API Development
  - Create RESTful APIs for programmatic data submission
  - Add GraphQL interface for flexible data querying
  - Implement webhook notifications for pipeline completion
  - Add batch processing APIs for large-scale data integration

- **Task 4.6.3:** Performance Optimization
  - Implement parallel processing for large datasets using Dask
  - Add caching layers for frequently accessed mappings
  - Optimize ML model inference for real-time processing
  - Create horizontal scaling capabilities for increased throughput

**4.7 Advanced Features & Extensions**

- **Task 4.7.1:** Federated Learning Support
  - Design privacy-preserving analysis capabilities
  - Implement DataSHIELD integration for distributed analysis
  - Add secure multiparty computation for sensitive data
  - Create standardized analysis workflows across federated sites

- **Task 4.7.2:** Large Language Model Integration
  - Integrate LLMs for assisted concept mapping and validation
  - Add natural language query interface for data exploration
  - Implement automated documentation generation for mappings
  - Create conversational interface for mapping review and refinement

## 6. Validation & Success Metrics

- **CI/CD Gates:** All `pytest` tests must pass. Code must pass linting (`ruff`) and type-checking (`mypy`). Test coverage should be >85%.
  
- **Performance:** API responses < 200ms. Initial dashboard load < 3 seconds. Interactive chart updates < 500ms.
  
- **Functional:** Anomaly detection correctly flags synthetic "bad data" injected by tests. End-to-end flow (data generation -> anomaly detection -> UI update) completes within 5 seconds in Demo Mode.
  
- **Success Metric:** The final dashboard enables a user to identify the top 3 riskiest sites and all their associated data anomalies in under 2 minutes.
