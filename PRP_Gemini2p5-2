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

**Phase 1: MVP - Core Monitoring & Visualization**

- **US1:** As Sam, I want a chart of cumulative enrollment over time, compared against a projected target line, to track overall study progress.
  
- **US2:** As Sam, I want an interactive map of all study sites, color-coded by a composite risk score, so I can quickly identify high-risk sites.
  
- **US3:** As Alex, I want a detailed data table that is linked to the charts, allowing me to sort, filter, and inspect the raw data behind the visualizations.
  
- **US4:** As Alex, I want a toggle to enter a "Demo Mode" which activates a mock data generator, so I can see how the dashboard behaves with live, streaming data.
  
- **US5:** As a user, I want a button to download the currently filtered data as a CSV file.
  

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

**Phase 3: Advanced Views & Reporting** 15. **3D Visualization:** Implement the 3D scatter plot component for lab data exploration (US10).
16. **Patient Funnel:** Build the Sankey diagram for patient disposition (US11). You will need to add a `status` column to the `patients` table (e.g., 'Screened', 'Enrolled', 'Completed', 'Withdrawn').
17. **PDF Reporting & AI Summary:** Add the PDF generation button (US12) and the placeholder text area for the AI summary (US13).
18. **Finalize Testing:** Expand `pytest` coverage to include all anomaly detection functions and major dashboard callbacks. Ensure the app handles empty/filtered data gracefully.

## 6. Validation & Success Metrics

- **CI/CD Gates:** All `pytest` tests must pass. Code must pass linting (`ruff`) and type-checking (`mypy`). Test coverage should be >85%.
  
- **Performance:** API responses < 200ms. Initial dashboard load < 3 seconds. Interactive chart updates < 500ms.
  
- **Functional:** Anomaly detection correctly flags synthetic "bad data" injected by tests. End-to-end flow (data generation -> anomaly detection -> UI update) completes within 5 seconds in Demo Mode.
  
- **Success Metric:** The final dashboard enables a user to identify the top 3 riskiest sites and all their associated data anomalies in under 2 minutes.
