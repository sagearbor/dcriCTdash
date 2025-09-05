"""
Dash Application Layout and Callbacks

Complete clinical trial analytics dashboard with real-time monitoring capabilities.
Integrates with FastAPI backend for live data updates and WebSocket streaming.
"""

import json
import asyncio
import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
import requests

import dash
from dash import dcc, html, Input, Output, State, callback, dash_table, ALL
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import numpy as np
import websocket
from threading import Thread
import time

# Phase 4: Field Detection
from app.core.field_detection import detect_field_types, create_sample_clinical_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for WebSocket and demo mode
ws_connection = None
demo_mode_active = False
demo_data_store = {}

# API Configuration
API_BASE_URL = "http://localhost:8003/api"
WS_URL = "ws://localhost:8003/ws"

def create_dash_app() -> dash.Dash:
    """
    Create and configure the main Dash application.
    
    Returns:
        dash.Dash: Configured Dash application instance
    """
    # Initialize Dash app
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css",
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
        ],
        external_scripts=[
            "https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"
        ],
        suppress_callback_exceptions=True,
        title="DCRI Clinical Trial Analytics Dashboard",
        update_title="Loading...",
        meta_tags=[
            {"name": "viewport", "content": "width=device-width, initial-scale=1"}
        ]
    )
    
    # Define app layout
    app.layout = create_layout()
    
    # Register callbacks
    register_callbacks(app)
    
    return app

def create_layout() -> html.Div:
    """
    Create the main dashboard layout with Bootstrap styling.
    
    Returns:
        html.Div: Complete dashboard layout
    """
    return html.Div([
        # Header Section
        html.Div([
            html.Div([
                html.H1([
                    html.I(className="fas fa-chart-line me-3", style={"color": "#007cba"}),
                    "DCRI Clinical Trial Analytics Dashboard"
                ], className="display-4 mb-0 text-center"),
                html.P("Real-time monitoring and analysis of clinical trial data", 
                       className="lead text-center text-muted mt-2 mb-4"),
                html.Hr(className="my-4")
            ], className="container")
        ], className="bg-light py-4 mb-4"),
        
        # Control Panel
        html.Div([
            html.Div([
                html.Div([
                    # Demo Mode Toggle
                    html.Div([
                        html.Label("Demo Mode", className="form-label fw-bold"),
                        html.Div([
                            dcc.Dropdown(
                                id='demo-mode-toggle',
                                options=[
                                    {'label': '🔴 Live Data (Empty)', 'value': False},
                                    {'label': '🟢 Demo Mode (Sample Data)', 'value': True}
                                ],
                                value=True,  # Default to demo mode
                                clearable=False,
                                className="mb-2"
                            )
                        ])
                    ], className="col-md-3"),
                    
                    # Site Filter
                    html.Div([
                        html.Label("Filter by Site", className="form-label fw-bold"),
                        dcc.Dropdown(
                            id='site-filter',
                            placeholder="All Sites",
                            className="mb-2",
                            style={'fontSize': '12px'},
                            optionHeight=50,
                            multi=True
                        )
                    ], className="col-md-3"),
                    
                    # Country Filter
                    html.Div([
                        html.Label("Filter by Country", className="form-label fw-bold"),
                        dcc.Dropdown(
                            id='country-filter',
                            placeholder="All Countries",
                            className="mb-2",
                            multi=True
                        )
                    ], className="col-md-3"),
                    
                    # Export Button
                    html.Div([
                        html.Label("Export Data", className="form-label fw-bold"),
                        html.Div([
                            html.Button([
                                html.I(className="fas fa-download me-2"),
                                "CSV Export"
                            ], id="export-btn", className="btn btn-success w-100")
                        ])
                    ], className="col-md-3"),
                    
                ], className="row g-3")
            ], className="card-body")
        ], className="card mb-4"),
        
        # Key Metrics Cards
        html.Div([
            html.Div(id="metrics-cards", className="row g-3")
        ], className="mb-4"),
        
        # Charts Section
        html.Div([
            # Enrollment Timeline Chart
            html.Div([
                html.Div([
                    html.Div([
                        html.H4([
                            html.I(className="fas fa-chart-area me-2"),
                            "Patient Enrollment Timeline"
                        ], className="card-title"),
                        dcc.Graph(
                            id="enrollment-chart",
                            config={'displayModeBar': True, 'displaylogo': False},
                            style={'height': '400px'}
                        )
                    ], className="card-body")
                ], className="card h-100")
            ], className="col-lg-8"),
            
            # Site Risk Map
            html.Div([
                html.Div([
                    html.Div([
                        html.H4([
                            html.I(className="fas fa-map-marked-alt me-2"),
                            "Site Risk Assessment"
                        ], className="card-title"),
                        dcc.Graph(
                            id="site-risk-map",
                            config={'displayModeBar': True, 'displaylogo': False},
                            style={'height': '400px'}
                        )
                    ], className="card-body")
                ], className="card h-100")
            ], className="col-lg-4"),
        ], className="row mb-4"),
        
        # Lab Results Analysis
        html.Div([
            html.Div([
                html.Div([
                    html.H4([
                        html.I(className="fas fa-flask me-2"),
                        "Laboratory Results Analysis"
                    ], className="card-title"),
                    dcc.Graph(
                        id="lab-analysis-chart",
                        config={'displayModeBar': True, 'displaylogo': False},
                        style={'height': '400px'}
                    )
                ], className="card-body")
            ], className="card")
        ], className="mb-4"),
        
        # Box Plot Section
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.H4([
                            html.I(className="fas fa-chart-box me-2"),
                            "Lab Value Distribution by Site"
                        ], className="card-title"),
                        html.P("Select a lab test to view value distributions across study sites. Box plots show median, quartiles, and outliers for each site.", 
                               className="text-muted mb-3"),
                        html.Div([
                            html.Label("Lab Test:", className="form-label"),
                            dcc.Dropdown(
                                id="lab-test-selector",
                                options=[
                                    {"label": "Hemoglobin (HGB)", "value": "HGB"},
                                    {"label": "Glucose (GLUC)", "value": "GLUC"},
                                    {"label": "Creatinine (CREAT)", "value": "CREAT"},
                                    {"label": "White Blood Cell Count (WBC)", "value": "WBC"},
                                    {"label": "Alanine Aminotransferase (ALT)", "value": "ALT"},
                                    {"label": "Total Cholesterol (CHOL)", "value": "CHOL"},
                                    {"label": "HDL Cholesterol (HDL)", "value": "HDL"},
                                    {"label": "LDL Cholesterol (LDL)", "value": "LDL"},
                                    {"label": "Triglycerides (TRIG)", "value": "TRIG"},
                                    {"label": "Hemoglobin A1c (HBA1C)", "value": "HBA1C"}
                                ],
                                value="HGB",
                                className="mb-3"
                            )
                        ]),
                        dcc.Graph(
                            id="lab-box-plot",
                            config={'displayModeBar': True, 'displaylogo': False},
                            style={'height': '450px'}
                        )
                    ], className="card-body")
                ], className="card h-100")
            ], className="col-12")
        ], className="row mb-4"),
        
        # Data Quality Section
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.H4([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            "Data Quality Issues"
                        ], className="card-title"),
                        html.P("Automatically detected data quality issues requiring attention. Issues are color-coded by severity.", 
                               className="text-muted mb-3"),
                        html.Div(id="data-quality-container")
                    ], className="card-body")
                ], className="card h-100")
            ], className="col-12")
        ], className="row mb-4"),
        
        # 3D Visualization Section
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.H4([
                            html.I(className="fas fa-cube me-2"),
                            "3D Lab Data Explorer"
                        ], className="card-title"),
                        html.P("Explore complex patterns and outliers in lab data using interactive 3D visualization. View relationships between sites, patients, and lab values in three-dimensional space.", 
                               className="text-muted mb-3"),
                        html.Div([
                            html.Div([
                                html.Label("Lab Test:", className="form-label"),
                                dcc.Dropdown(
                                    id="lab-test-3d-selector",
                                    options=[
                                        {"label": "Hemoglobin (HGB)", "value": "HGB"},
                                        {"label": "Glucose (GLUC)", "value": "GLUC"},
                                        {"label": "Creatinine (CREAT)", "value": "CREAT"},
                                        {"label": "White Blood Cell Count (WBC)", "value": "WBC"},
                                        {"label": "Alanine Aminotransferase (ALT)", "value": "ALT"}
                                    ],
                                    value="HGB",
                                    className="mb-2"
                                )
                            ], className="col-md-4"),
                            html.Div([
                                html.Label("Color By:", className="form-label"),
                                dcc.Dropdown(
                                    id="color-by-selector",
                                    options=[
                                        {"label": "Site", "value": "site"},
                                        {"label": "Age Group", "value": "age_group"},
                                        {"label": "Sex", "value": "sex"}
                                    ],
                                    value="site",
                                    className="mb-2"
                                )
                            ], className="col-md-4"),
                            html.Div([
                                html.Label("Size By:", className="form-label"),
                                dcc.Dropdown(
                                    id="size-by-selector",
                                    options=[
                                        {"label": "Lab Value", "value": "lab_value"},
                                        {"label": "Patient Age", "value": "age"},
                                        {"label": "Uniform", "value": "uniform"}
                                    ],
                                    value="lab_value",
                                    className="mb-2"
                                )
                            ], className="col-md-4")
                        ], className="row mb-3"),
                        dcc.Graph(
                            id="lab-3d-scatter",
                            config={'displayModeBar': True, 'displaylogo': False},
                            style={'height': '600px'}
                        )
                    ], className="card-body")
                ], className="card h-100")
            ], className="col-12")
        ], className="row mb-4"),
        
        # Patient Disposition Sankey Diagram Section
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.H4([
                            html.I(className="fas fa-project-diagram me-2"),
                            "Patient Disposition Flow"
                        ], className="card-title"),
                        html.P("Track patient progression through study phases from screening to completion. This flow diagram helps understand subject attrition and identify potential bottlenecks.", 
                               className="text-muted mb-3"),
                        html.Div([
                            html.Div([
                                html.Label("View Mode:", className="form-label"),
                                dcc.Dropdown(
                                    id="sankey-view-selector",
                                    options=[
                                        {"label": "Overall Study Flow", "value": "overall"},
                                        {"label": "By Site", "value": "by_site"},
                                        {"label": "By Country", "value": "by_country"}
                                    ],
                                    value="overall",
                                    className="mb-2"
                                )
                            ], className="col-md-6"),
                            html.Div([
                                html.Label("Show Numbers:", className="form-label"),
                                dcc.Dropdown(
                                    id="sankey-numbers-toggle",
                                    options=[
                                        {"label": "Absolute Counts", "value": "absolute"},
                                        {"label": "Percentages", "value": "percentage"},
                                        {"label": "Both", "value": "both"}
                                    ],
                                    value="absolute",
                                    className="mb-2"
                                )
                            ], className="col-md-6")
                        ], className="row mb-3"),
                        dcc.Graph(
                            id="patient-disposition-sankey",
                            config={'displayModeBar': True, 'displaylogo': False},
                            style={'height': '500px'}
                        )
                    ], className="card-body")
                ], className="card h-100")
            ], className="col-12")
        ], className="row mb-4"),
        
        # PDF Report Generation Section
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.H4([
                            html.I(className="fas fa-file-pdf me-2"),
                            "PDF Report Generation"
                        ], className="card-title"),
                        html.P("Generate comprehensive PDF reports of the current dashboard view for sharing in meetings and regulatory submissions.", 
                               className="text-muted mb-3"),
                        html.Div([
                            html.Div([
                                html.Label("Report Type:", className="form-label"),
                                dcc.Dropdown(
                                    id="pdf-report-type",
                                    options=[
                                        {"label": "Executive Summary", "value": "executive"},
                                        {"label": "Detailed Analysis", "value": "detailed"},
                                        {"label": "Site Performance", "value": "site_performance"},
                                        {"label": "Data Quality Report", "value": "data_quality"}
                                    ],
                                    value="executive",
                                    className="mb-3"
                                )
                            ], className="col-md-6"),
                            html.Div([
                                html.Label("Include Sections:", className="form-label"),
                                dcc.Checklist(
                                    id="pdf-sections-checklist",
                                    options=[
                                        {"label": "Enrollment Chart", "value": "enrollment"},
                                        {"label": "Site Risk Map", "value": "site_map"},
                                        {"label": "Lab Analysis", "value": "lab_analysis"},
                                        {"label": "Data Quality Issues", "value": "data_quality"},
                                        {"label": "Patient Disposition", "value": "disposition"},
                                        {"label": "3D Lab Explorer", "value": "3d_labs"}
                                    ],
                                    value=["enrollment", "site_map", "lab_analysis", "data_quality"],
                                    inline=False,
                                    className="mb-3"
                                )
                            ], className="col-md-6")
                        ], className="row"),
                        html.Hr(),
                        html.Div([
                            html.Button([
                                html.I(className="fas fa-file-pdf me-2"),
                                "Generate PDF Report"
                            ], id="generate-pdf-btn", className="btn btn-primary me-2"),
                            html.Button([
                                html.I(className="fas fa-download me-2"),
                                "Download Sample Report"
                            ], id="download-sample-pdf-btn", className="btn btn-outline-secondary"),
                            html.Div(id="pdf-generation-status", className="mt-3")
                        ])
                    ], className="card-body")
                ], className="card h-100")
            ], className="col-12")
        ], className="row mb-4"),
        
        # AI Summary Section (US13)
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.H4([
                            html.I(className="fas fa-robot me-2"),
                            "AI-Generated Summary"
                        ], className="card-title"),
                        html.P("AI-powered analysis of significant changes and insights since your last login. This feature will be enabled with future LLM integration.", 
                               className="text-muted mb-3"),
                        html.Div([
                            html.Div([
                                html.Label("Summary Type:", className="form-label"),
                                dcc.Dropdown(
                                    id="ai-summary-type",
                                    options=[
                                        {"label": "Changes Since Last Login", "value": "changes"},
                                        {"label": "Key Insights", "value": "insights"},
                                        {"label": "Risk Alerts", "value": "alerts"},
                                        {"label": "Enrollment Trends", "value": "trends"}
                                    ],
                                    value="changes",
                                    className="mb-3"
                                )
                            ], className="col-md-6"),
                            html.Div([
                                html.Label("Analysis Depth:", className="form-label"),
                                dcc.Dropdown(
                                    id="ai-analysis-depth",
                                    options=[
                                        {"label": "Brief Overview", "value": "brief"},
                                        {"label": "Detailed Analysis", "value": "detailed"},
                                        {"label": "Executive Summary", "value": "executive"}
                                    ],
                                    value="brief",
                                    className="mb-3"
                                )
                            ], className="col-md-6")
                        ], className="row"),
                        html.Div([
                            html.Button([
                                html.I(className="fas fa-magic me-2"),
                                "Generate AI Summary"
                            ], id="generate-ai-summary-btn", className="btn btn-info me-2", disabled=True),
                            html.Small("(Feature coming soon with LLM integration)", className="text-muted")
                        ], className="mb-3"),
                        html.Div([
                            dcc.Textarea(
                                id="ai-summary-output",
                                className="form-control",
                                style={"height": "200px", "backgroundColor": "#f8f9fa"},
                                placeholder="AI-generated summary will appear here once LLM integration is implemented...\n\nPlanned features:\n• Automatic detection of significant changes\n• Risk pattern analysis\n• Enrollment trend predictions\n• Data quality recommendations\n• Site performance insights",
                                disabled=True,
                                value=""
                            )
                        ])
                    ], className="card-body")
                ], className="card h-100")
            ], className="col-12")
        ], className="row mb-4"),
        
        # Phase 4: Field Detection Section
        html.Div([
            html.Div([
                html.Div([
                    html.H4([
                        html.I(className="fas fa-search me-2"),
                        "Automated Field Detection"
                    ], className="card-title mb-3"),
                    html.P("Phase 4: Statistical correlation analysis to automatically detect the semantic meaning of ambiguous clinical data fields.", 
                           className="text-muted mb-3"),
                    
                    # Field Detection Controls
                    html.Div([
                        html.Div([
                            html.Label("Confidence Threshold:", className="form-label"),
                            dcc.Slider(
                                id="field-detection-confidence-slider",
                                min=0.3,
                                max=1.0,
                                step=0.1,
                                value=0.6,
                                marks={i/10: f"{i/10}" for i in range(3, 11)},
                                className="mb-3"
                            )
                        ], className="col-md-6"),
                        
                        html.Div([
                            html.Button([
                                html.I(className="fas fa-magic me-2"),
                                "Analyze Fields"
                            ], 
                            id="run-field-detection-btn", 
                            className="btn btn-primary btn-lg",
                            n_clicks=0)
                        ], className="col-md-6 d-flex align-items-end")
                    ], className="row mb-4"),
                    
                    # Detection Results
                    html.Div([
                        html.Div(id="field-detection-results", className="mb-4"),
                        html.Div(id="field-detection-validation", style={"display": "none"})
                    ])
                ], className="card-body")
            ], className="card")
        ], className="mb-4"),
        
        # Data Table Section
        html.Div([
            html.Div([
                html.Div([
                    html.H4([
                        html.I(className="fas fa-table me-2"),
                        "Patient Data Table"
                    ], className="card-title mb-3"),
                    html.Div(id="data-table-container")
                ], className="card-body")
            ], className="card")
        ], className="mb-4"),
        
        # Hidden divs for data storage
        html.Div(id="websocket-data", style={"display": "none"}),
        html.Div(id="api-data-store", style={"display": "none"}),
        
        # Auto-refresh interval
        dcc.Interval(
            id='interval-component',
            interval=30*1000,  # Update every 30 seconds
            n_intervals=0
        ),
        
        # Export download component
        dcc.Download(id="download-csv"),
        
        # PDF download component
        dcc.Download(id="download-pdf"),
        
        # Site notification modal
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.H5("Site Notification", className="modal-title"),
                        html.Button("×", **{
                            "type": "button",
                            "className": "btn-close",
                            "data-bs-dismiss": "modal"
                        })
                    ], className="modal-header"),
                    html.Div([
                        html.Div(id="notification-content"),
                        html.Hr(),
                        html.Div([
                            html.Label("Email Subject:", className="form-label"),
                            dcc.Input(
                                id="email-subject",
                                type="text",
                                className="form-control",
                                placeholder="Enter email subject..."
                            )
                        ], className="mb-3"),
                        html.Div([
                            html.Label("Email Body:", className="form-label"),
                            dcc.Textarea(
                                id="email-body",
                                className="form-control",
                                style={"height": "200px"},
                                placeholder="Email content will be pre-populated..."
                            )
                        ], className="mb-3"),
                        html.Div([
                            html.Label("Notification Type:", className="form-label"),
                            dcc.Dropdown(
                                id="notification-type",
                                options=[
                                    {"label": "Enrollment Lag Alert", "value": "enrollment_lag"},
                                    {"label": "Data Quality Issues", "value": "data_quality"},
                                    {"label": "General Follow-up", "value": "follow_up"},
                                    {"label": "Risk Assessment Alert", "value": "risk_alert"}
                                ],
                                value="enrollment_lag",
                                className="form-control"
                            )
                        ], className="mb-3")
                    ], className="modal-body"),
                    html.Div([
                        html.Button("Close", className="btn btn-secondary me-2", **{"data-bs-dismiss": "modal"}),
                        html.Button("Send Email", id="send-email-btn", className="btn btn-primary"),
                        html.Button("Copy to Clipboard", id="copy-email-btn", className="btn btn-outline-secondary ms-2")
                    ], className="modal-footer")
                ], className="modal-content")
            ], className="modal-dialog modal-lg")
        ], className="modal fade", id="site-notification-modal", **{"tabIndex": "-1"}),
        
        # Store for selected site data
        html.Div(id="selected-site-store", style={"display": "none"}),
        
        # Patient profile modal
        html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.H5("Patient Profile", className="modal-title"),
                        html.Button("×", **{
                            "type": "button",
                            "className": "btn-close",
                            "data-bs-dismiss": "modal"
                        })
                    ], className="modal-header"),
                    html.Div([
                        html.Div(id="patient-profile-content"),
                        html.Hr(),
                        html.Div([
                            dcc.Graph(
                                id="patient-biomarker-chart",
                                config={'displayModeBar': True, 'displaylogo': False},
                                style={'height': '400px'}
                            )
                        ], className="mb-3"),
                        html.Div([
                            html.H6("Visit History", className="text-primary"),
                            html.Div(id="patient-visit-history")
                        ], className="mb-3")
                    ], className="modal-body"),
                    html.Div([
                        html.Button("Close", className="btn btn-secondary me-2", **{"data-bs-dismiss": "modal"}),
                        html.Button("Export Patient Data", id="export-patient-btn", className="btn btn-primary")
                    ], className="modal-footer")
                ], className="modal-content")
            ], className="modal-dialog modal-xl")
        ], className="modal fade", id="patient-profile-modal", **{"tabIndex": "-1"}),
        
        # Store for selected patient data
        html.Div(id="selected-patient-store", style={"display": "none"})
        
    ], className="container-fluid", style={"padding": "0 15px"})

def fetch_api_data(endpoint: str, params: Dict = None) -> Dict:
    """
    Fetch data from FastAPI backend.
    
    Args:
        endpoint: API endpoint path
        params: Query parameters
        
    Returns:
        Dict: API response data
    """
    try:
        url = f"{API_BASE_URL}{endpoint}"
        response = requests.get(url, params=params or {}, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed for {endpoint}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Unexpected error fetching {endpoint}: {e}")
        return {}

def create_metrics_cards(stats_data: Dict, is_filtered: bool = False) -> List[html.Div]:
    """
    Create metrics cards from statistics data.
    
    Args:
        stats_data: Statistics from API
        is_filtered: Whether data is filtered (changes labels)
        
    Returns:
        List of metric cards
    """
    if not stats_data:
        return [html.Div("Loading metrics...", className="col-12 text-center")]
    
    # Change labels based on filtering
    site_label = "Selected Sites" if is_filtered else "Total Sites"
    patient_label = "Filtered Patients" if is_filtered else "Total Patients"
    visit_label = "Filtered Visits" if is_filtered else "Total Visits"
    lab_label = "Filtered Labs" if is_filtered else "Lab Results"
    
    metrics = [
        {
            "title": site_label,
            "value": stats_data.get('total_sites', 0),
            "icon": "fas fa-hospital",
            "color": "primary"
        },
        {
            "title": patient_label,
            "value": stats_data.get('total_patients', 0),
            "icon": "fas fa-users",
            "color": "success"
        },
        {
            "title": visit_label,
            "value": stats_data.get('total_visits', 0),
            "icon": "fas fa-calendar-check",
            "color": "info"
        },
        {
            "title": lab_label,
            "value": stats_data.get('total_labs', 0),
            "icon": "fas fa-flask",
            "color": "warning"
        }
    ]
    
    cards = []
    for metric in metrics:
        card = html.Div([
            html.Div([
                html.Div([
                    html.Div([
                        html.I(className=f"{metric['icon']} fa-2x text-{metric['color']}")
                    ], className="col-3 d-flex align-items-center justify-content-center"),
                    html.Div([
                        html.H3(f"{metric['value']:,}", className="mb-0"),
                        html.P(metric['title'], className="text-muted mb-0")
                    ], className="col-9")
                ], className="row")
            ], className="card-body")
        ], className="card h-100")
        cards.append(html.Div(card, className="col-md-3"))
    
    return cards

def create_enrollment_chart(stats_data: Dict, demo_mode: bool = False) -> go.Figure:
    """
    Create enrollment timeline chart.
    
    Args:
        stats_data: Statistics data from API
        demo_mode: Whether demo mode is active
        
    Returns:
        go.Figure: Plotly enrollment chart
    """
    fig = go.Figure()
    
    if not stats_data or 'enrollment_timeline' not in stats_data:
        # Create placeholder with sample data
        sample_dates = pd.date_range(start="2024-01-01", periods=12, freq="M")
        sample_values = [10, 25, 45, 80, 120, 180, 250, 320, 410, 520, 650, 800]
        
        fig.add_trace(go.Scatter(
            x=sample_dates,
            y=sample_values,
            mode='lines+markers',
            name='Cumulative Enrollment',
            line=dict(color='#007cba', width=3),
            marker=dict(size=8, color='#007cba'),
            hovertemplate='<b>%{x}</b><br>Patients: %{y}<extra></extra>'
        ))
        
        fig.update_layout(
            title="Patient Enrollment Over Time" + (" (Sample Data)" if not demo_mode else " (Demo Mode)"),
            xaxis_title="Date",
            yaxis_title="Cumulative Patients",
            hovermode='x unified',
            template="plotly_white",
            height=400,
            autosize=False,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        return fig
    
    # Process real data
    timeline_data = stats_data['enrollment_timeline']
    
    if timeline_data:
        df = pd.DataFrame(timeline_data)
        df['month'] = pd.to_datetime(df['month'], errors='coerce')
        df = df.dropna().sort_values('month')
        df['cumulative'] = df['enrollments'].cumsum()
        
        fig.add_trace(go.Scatter(
            x=df['month'],
            y=df['cumulative'],
            mode='lines+markers',
            name='Cumulative Enrollment',
            line=dict(color='#007cba', width=3),
            marker=dict(size=8, color='#007cba'),
            hovertemplate='<b>%{x}</b><br>Total Patients: %{y}<br>New: %{text}<extra></extra>',
            text=df['enrollments']
        ))
    
    fig.update_layout(
        title="Patient Enrollment Over Time",
        xaxis_title="Date",
        yaxis_title="Cumulative Patients",
        hovermode='x unified',
        template="plotly_white",
        height=400,
        autosize=False,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig

def generate_email_template(site_data: Dict, notification_type: str, site_metrics: Dict = None) -> Dict[str, str]:
    """
    Generate email template based on site data and notification type.
    
    Args:
        site_data: Site information
        notification_type: Type of notification
        site_metrics: Additional metrics for the site
        
    Returns:
        Dict containing subject and body
    """
    site_name = site_data.get('site_name', 'Unknown Site')
    current_enrollment = site_data.get('current_enrollment', 0)
    target_enrollment = site_data.get('enrollment_target', 100)
    progress = (current_enrollment / target_enrollment * 100) if target_enrollment > 0 else 0
    
    templates = {
        "enrollment_lag": {
            "subject": f"URGENT: Enrollment Lag Alert - {site_name}",
            "body": f"""Dear {site_name} Team,

We hope this message finds you well. We are writing to address a concerning trend in enrollment progress at your site.

CURRENT ENROLLMENT STATUS:
• Site: {site_name}
• Current Enrollment: {current_enrollment} patients
• Target Enrollment: {target_enrollment} patients  
• Progress: {progress:.1f}%
• Status: {'BEHIND TARGET' if progress < 80 else 'ON TRACK'}

IMMEDIATE ACTION REQUIRED:
{'• Your site is significantly behind the target enrollment pace' if progress < 80 else '• Please maintain current enrollment momentum'}
• Please review your enrollment strategies and identify potential barriers
• Consider implementing enhanced recruitment initiatives
• Provide an updated enrollment forecast by end of week

We are here to support you and would appreciate a call to discuss how we can help accelerate enrollment at your site.

Best regards,
Clinical Operations Team
DCRI Clinical Trial Oversight"""
        },
        "data_quality": {
            "subject": f"Data Quality Review Required - {site_name}",
            "body": f"""Dear {site_name} Data Management Team,

Our quality monitoring system has identified data quality issues that require your immediate attention.

SITE INFORMATION:
• Site: {site_name}
• Enrolled Patients: {current_enrollment}
• Review Priority: HIGH

ISSUES IDENTIFIED:
• Missing critical data fields
• Out-of-range laboratory values
• Incomplete visit records
• Protocol deviations requiring documentation

NEXT STEPS:
• Please review the data quality issues in your system
• Submit corrective action plan within 48 hours
• Schedule data review call with our team
• Implement additional quality checks going forward

Please contact us immediately if you need clarification on any of these findings.

Best regards,
Data Management Team
DCRI Clinical Trial Oversight"""
        },
        "risk_alert": {
            "subject": f"Site Risk Assessment Alert - {site_name}",
            "body": f"""Dear {site_name} Leadership,

Our risk-based monitoring system has flagged your site for immediate review due to multiple risk indicators.

SITE RISK PROFILE:
• Site: {site_name}
• Risk Level: HIGH
• Enrollment Status: {current_enrollment}/{target_enrollment} ({progress:.1f}%)

RISK FACTORS IDENTIFIED:
• Enrollment performance below targets
• Data quality concerns
• Protocol compliance issues
• Missing critical documentation

CORRECTIVE ACTIONS REQUIRED:
• Immediate site audit and remediation plan
• Enhanced monitoring and oversight
• Additional training for site staff
• Weekly progress reports to sponsor

We need to schedule an urgent call to discuss these findings and develop an action plan.

Please respond within 24 hours.

Regards,
Risk Management Team
DCRI Clinical Trial Oversight"""
        },
        "follow_up": {
            "subject": f"Follow-up Required - {site_name}",
            "body": f"""Dear {site_name} Team,

We hope you are doing well. We wanted to follow up on your site's progress and see how we can better support your clinical trial activities.

SITE SUMMARY:
• Site: {site_name}
• Current Enrollment: {current_enrollment} patients
• Target: {target_enrollment} patients
• Progress: {progress:.1f}%

FOLLOW-UP ITEMS:
• How can we better support your enrollment efforts?
• Are there any protocol or operational challenges?
• Do you need additional training or resources?
• Any feedback on study procedures?

Please let us know a convenient time for a brief call to discuss your site's needs and address any concerns.

Thank you for your continued partnership.

Best regards,
Clinical Operations Team
DCRI Clinical Trial Oversight"""
        }
    }
    
    return templates.get(notification_type, templates["follow_up"])

def create_patient_biomarker_chart(patient_data: Dict, labs_data: List[Dict], visits_data: List[Dict]) -> go.Figure:
    """
    Create longitudinal biomarker chart for a specific patient.
    
    Args:
        patient_data: Patient information
        labs_data: Lab results for the patient
        visits_data: Visit data for the patient
        
    Returns:
        go.Figure: Plotly line chart with biomarkers over time
    """
    fig = go.Figure()
    
    if not labs_data:
        fig.add_annotation(
            text="No laboratory data available for this patient",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="gray")
        )
        fig.update_layout(
            title="Patient Biomarker Timeline",
            height=400
        )
        return fig
    
    # Convert to DataFrame for easier processing
    df_labs = pd.DataFrame(labs_data)
    df_visits = pd.DataFrame(visits_data)
    
    # Merge with visit dates
    if not df_visits.empty:
        df_merged = df_labs.merge(df_visits[['visit_id', 'visit_date']], on='visit_id', how='left')
        df_merged['visit_date'] = pd.to_datetime(df_merged['visit_date'])
        df_merged = df_merged.sort_values('visit_date')
    else:
        df_merged = df_labs.copy()
        df_merged['visit_date'] = pd.to_datetime('2024-01-01')  # Fallback date
    
    # Key biomarkers to display
    key_biomarkers = ['HGB', 'GLUC', 'CREAT', 'WBC', 'ALT']
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']
    
    for i, biomarker in enumerate(key_biomarkers):
        biomarker_data = df_merged[df_merged['lbtestcd'] == biomarker]
        
        if not biomarker_data.empty:
            # Get reference ranges
            normal_low = biomarker_data['lbornrlo'].iloc[0] if not biomarker_data['lbornrlo'].isna().all() else None
            normal_high = biomarker_data['lbornrhi'].iloc[0] if not biomarker_data['lbornrhi'].isna().all() else None
            
            # Add biomarker line
            fig.add_trace(go.Scatter(
                x=biomarker_data['visit_date'],
                y=biomarker_data['lbstresn'],
                mode='lines+markers',
                name=biomarker_data['lbtest'].iloc[0] if not biomarker_data.empty else biomarker,
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=8),
                hovertemplate='<b>%{fullData.name}</b><br>' +
                             'Date: %{x}<br>' +
                             'Value: %{y}<br>' +
                             'Units: ' + str(biomarker_data['lbstresu'].iloc[0] if not biomarker_data.empty else '') +
                             '<extra></extra>'
            ))
            
            # Add reference range shading if available
            if normal_low is not None and normal_high is not None:
                x_range = biomarker_data['visit_date'].tolist()
                if len(x_range) > 1:
                    fig.add_trace(go.Scatter(
                        x=x_range + x_range[::-1],
                        y=[normal_high] * len(x_range) + [normal_low] * len(x_range),
                        fill='toself',
                        fillcolor=f'rgba{colors[i % len(colors)][3:-1]}, 0.1)',
                        line=dict(color='rgba(0,0,0,0)'),
                        showlegend=False,
                        hoverinfo='skip',
                        name=f'{biomarker} Normal Range'
                    ))
    
    fig.update_layout(
        title=f"Biomarker Timeline - {patient_data.get('usubjid', 'Unknown Patient')}",
        xaxis_title="Visit Date",
        yaxis_title="Lab Values",
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=400,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def create_site_risk_map(sites_data: List[Dict]) -> go.Figure:
    """
    Create interactive site risk assessment map with click functionality.
    
    Args:
        sites_data: Sites data from API
        
    Returns:
        go.Figure: Plotly geographic scatter map
    """
    fig = go.Figure()
    
    if not sites_data:
        # Create sample site data for demonstration
        sample_sites = [
            {"site_name": "Duke University", "country": "USA", "latitude": 36.0014, "longitude": -78.9382, "current_enrollment": 85, "enrollment_target": 100},
            {"site_name": "Johns Hopkins", "country": "USA", "latitude": 39.2904, "longitude": -76.6122, "current_enrollment": 92, "enrollment_target": 100},
            {"site_name": "Mayo Clinic", "country": "USA", "latitude": 44.0225, "longitude": -92.4699, "current_enrollment": 78, "enrollment_target": 100},
            {"site_name": "Toronto General", "country": "CAN", "latitude": 43.6532, "longitude": -79.3832, "current_enrollment": 65, "enrollment_target": 80},
            {"site_name": "London Hospital", "country": "GBR", "latitude": 51.5074, "longitude": -0.1278, "current_enrollment": 45, "enrollment_target": 90}
        ]
        sites_data = sample_sites
    
    # Process sites data
    lats = []
    lons = []
    texts = []
    colors = []
    sizes = []
    site_ids = []
    
    for site in sites_data:
        if site.get('latitude') and site.get('longitude'):
            lats.append(site['latitude'])
            lons.append(site['longitude'])
            site_ids.append(site.get('site_id', ''))
            
            current = site.get('current_enrollment', 0)
            target = site.get('enrollment_target', 100)
            progress = (current / target * 100) if target > 0 else 0
            
            # Color coding based on enrollment progress
            if progress >= 90:
                color = '#28a745'  # Green - excellent
            elif progress >= 70:
                color = '#ffc107'  # Yellow - good
            elif progress >= 50:
                color = '#fd7e14'  # Orange - concerning
            else:
                color = '#dc3545'  # Red - at risk
            
            colors.append(color)
            sizes.append(max(10, min(30, current / 3)))  # Scale size by enrollment
            
            text = f"<b>{site.get('site_name', 'Unknown Site')}</b><br>"
            text += f"Country: {site.get('country', 'N/A')}<br>"
            text += f"Enrolled: {current}/{target}<br>"
            text += f"Progress: {progress:.1f}%<br>"
            text += f"<i>Click to send notification</i>"
            texts.append(text)
    
    if lats and lons:
        fig.add_trace(go.Scattergeo(
            lat=lats,
            lon=lons,
            text=texts,
            customdata=site_ids,
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                line=dict(width=2, color='white'),
                sizemode='diameter'
            ),
            hovertemplate='%{text}<extra></extra>',
            showlegend=False,
            name='sites'
        ))
    
    fig.update_layout(
        title="Global Site Risk Assessment Map",
        geo=dict(
            showframe=False,
            showcoastlines=True,
            projection_type='equirectangular'
        ),
        height=400,
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig

def create_lab_analysis_chart(labs_data: List[Dict] = None) -> go.Figure:
    """
    Create laboratory results analysis chart.
    
    Args:
        labs_data: Lab results data
        
    Returns:
        go.Figure: Lab analysis chart
    """
    fig = go.Figure()
    
    # Sample lab abnormalities data
    abnormalities = {
        'HIGH': 145,
        'LOW': 89,
        'NORMAL': 1234,
        'ABNORMAL': 67
    }
    
    if labs_data and isinstance(labs_data, dict):
        abnormalities = labs_data
    
    # Create pie chart for lab abnormalities
    labels = list(abnormalities.keys())
    values = list(abnormalities.values())
    colors = ['#dc3545', '#fd7e14', '#28a745', '#ffc107'][:len(labels)]
    
    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        hole=.4,
        marker=dict(colors=colors, line=dict(color='white', width=2)),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Laboratory Results Distribution",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        height=400,
        margin=dict(l=0, r=0, t=40, b=80)
    )
    
    return fig

def create_lab_box_plot(labs_data: List[Dict], patients_data: List[Dict], sites_data: List[Dict], selected_test: str = "HGB") -> go.Figure:
    """
    Create box plot showing lab value distributions by site.
    
    Args:
        labs_data: Laboratory data from API
        patients_data: Patient data for site mapping
        sites_data: Site data for site names
        selected_test: Lab test code to display (e.g., "HGB", "GLUC", "CREAT")
        
    Returns:
        go.Figure: Box plot chart
    """
    fig = go.Figure()
    
    if not labs_data or not patients_data or not sites_data:
        # Sample data for demonstration
        import numpy as np
        np.random.seed(42)
        
        # Create sample box plot data
        sites = ['SITE001', 'SITE002', 'SITE003', 'SITE004', 'SITE005']
        colors = ['#007cba', '#28a745', '#ffc107', '#dc3545', '#6f42c1']
        
        for i, site in enumerate(sites):
            # Generate sample data with different distributions per site
            values = np.random.normal(12 + i*0.5, 1.2, 50)  # Slightly different means per site
            fig.add_trace(go.Box(
                y=values,
                name=site,
                marker_color=colors[i],
                boxpoints='outliers',
                jitter=0.3,
                pointpos=-1.8
            ))
        
        fig.update_layout(
            title=f"{selected_test} Distribution by Site (Sample Data)",
            yaxis_title="Lab Value",
            xaxis_title="Study Site",
            template="plotly_white",
            height=450,
            showlegend=False,
            margin=dict(l=50, r=50, t=50, b=50)
        )
        return fig
    
    # Create site mapping for patient data
    site_map = {site['site_id']: site['site_name'] for site in sites_data}
    patient_site_map = {patient['usubjid']: patient['site_id'] for patient in patients_data}
    
    # Filter labs for selected test and group by site
    filtered_labs = [lab for lab in labs_data if lab.get('lbtestcd') == selected_test and lab.get('lbstresn') is not None]
    
    if not filtered_labs:
        # No data for selected test
        fig.add_annotation(
            text=f"No data available for {selected_test}",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            title=f"{selected_test} Distribution by Site",
            template="plotly_white",
            height=450
        )
        return fig
    
    # Group lab values by site
    site_values = {}
    for lab in filtered_labs:
        usubjid = lab.get('usubjid')
        site_id = patient_site_map.get(usubjid)
        if site_id:
            site_name = site_map.get(site_id, site_id)
            if site_name not in site_values:
                site_values[site_name] = []
            site_values[site_name].append(float(lab['lbstresn']))
    
    if not site_values:
        fig.add_annotation(
            text=f"No site data available for {selected_test}",
            x=0.5, y=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            title=f"{selected_test} Distribution by Site",
            template="plotly_white",
            height=450
        )
        return fig
    
    # Create box plots for each site
    colors = ['#007cba', '#28a745', '#ffc107', '#dc3545', '#6f42c1', '#fd7e14', '#e83e8c', '#20c997', '#6610f2', '#17a2b8']
    
    for i, (site_name, values) in enumerate(sorted(site_values.items())):
        if values:  # Only add if there are values
            color = colors[i % len(colors)]
            fig.add_trace(go.Box(
                y=values,
                name=site_name,
                marker_color=color,
                boxpoints='outliers',  # Show outlier points
                jitter=0.3,
                pointpos=-1.8,
                hovertemplate=f'<b>{site_name}</b><br>' +
                             'Value: %{y}<br>' +
                             'Q1: %{q1}<br>' +
                             'Median: %{median}<br>' +
                             'Q3: %{q3}<br>' +
                             '<extra></extra>'
            ))
    
    # Get lab test name for title
    test_name = selected_test
    if filtered_labs:
        test_name = filtered_labs[0].get('lbtest', selected_test)
    
    fig.update_layout(
        title=f"{test_name} Distribution by Site",
        yaxis_title=f"{test_name} Value",
        xaxis_title="Study Site",
        template="plotly_white",
        height=450,
        showlegend=False,
        margin=dict(l=60, r=50, t=60, b=100),
        xaxis=dict(tickangle=-45)
    )
    
    return fig

def create_3d_lab_scatter(labs_data: List[Dict], patients_data: List[Dict], sites_data: List[Dict], 
                         selected_test: str = "HGB", color_by: str = "site", size_by: str = "lab_value") -> go.Figure:
    """
    Create 3D scatter plot for lab data exploration.
    
    Args:
        labs_data: Laboratory data from API
        patients_data: Patient data for site/demographic mapping
        sites_data: Site data for site names
        selected_test: Lab test code to display (e.g., "HGB", "GLUC", "CREAT")
        color_by: What to color points by ("site", "age_group", "sex")
        size_by: What to size points by ("lab_value", "age", "uniform")
        
    Returns:
        go.Figure: 3D scatter plot
    """
    fig = go.Figure()
    
    if not labs_data or not patients_data or not sites_data:
        # Sample 3D data for demonstration
        import numpy as np
        np.random.seed(42)
        
        n_points = 200
        x_vals = np.random.normal(0, 1, n_points)  # Site index
        y_vals = np.random.normal(0, 1, n_points)  # Patient index
        z_vals = np.random.normal(12, 2, n_points)  # Lab values
        colors = np.random.choice(['Site A', 'Site B', 'Site C', 'Site D', 'Site E'], n_points)
        sizes = np.abs(z_vals) * 2
        
        fig.add_trace(go.Scatter3d(
            x=x_vals,
            y=y_vals, 
            z=z_vals,
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                colorscale='Viridis',
                showscale=True,
                opacity=0.7,
                line=dict(width=1, color='white')
            ),
            hovertemplate='<b>%{marker.color}</b><br>' +
                         'Site Coord: %{x}<br>' +
                         'Patient Coord: %{y}<br>' +
                         f'{selected_test} Value: %{{z}}<br>' +
                         '<extra></extra>',
            name='Lab Data'
        ))
        
        fig.update_layout(
            title=f'3D Lab Data Explorer - {selected_test} (Sample Data)',
            scene=dict(
                xaxis_title='Site Dimension',
                yaxis_title='Patient Dimension', 
                zaxis_title=f'{selected_test} Value',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            height=600,
            margin=dict(l=0, r=0, t=50, b=0)
        )
        return fig
    
    # Create mappings
    site_map = {site['site_id']: site.get('site_name', site['site_id']) for site in sites_data}
    patient_map = {p['usubjid']: p for p in patients_data}
    
    # Filter labs for selected test
    filtered_labs = [lab for lab in labs_data if lab.get('lbtestcd') == selected_test and lab.get('lbstresn') is not None]
    
    if not filtered_labs:
        fig.add_annotation(
            text=f"No data available for {selected_test}",
            x=0.5, y=0.5, z=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            title=f'3D Lab Data Explorer - {selected_test}',
            scene=dict(
                xaxis_title='Site Dimension',
                yaxis_title='Patient Dimension',
                zaxis_title=f'{selected_test} Value'
            ),
            height=600
        )
        return fig
    
    # Prepare data for 3D plotting
    plot_data = []
    site_to_index = {}
    patient_to_index = {}
    
    for i, lab in enumerate(filtered_labs):
        usubjid = lab.get('usubjid')
        patient = patient_map.get(usubjid)
        if not patient:
            continue
            
        site_id = patient.get('site_id')
        site_name = site_map.get(site_id, site_id)
        
        # Create site index (x-axis)
        if site_name not in site_to_index:
            site_to_index[site_name] = len(site_to_index)
        x_coord = site_to_index[site_name] + np.random.normal(0, 0.1)  # Add slight jitter
        
        # Create patient index (y-axis) - could be patient ID hash or sequential
        if usubjid not in patient_to_index:
            patient_to_index[usubjid] = len(patient_to_index) 
        y_coord = patient_to_index[usubjid] + np.random.normal(0, 0.1)  # Add slight jitter
        
        # Lab value (z-axis)
        z_coord = float(lab['lbstresn'])
        
        # Color assignment
        if color_by == "site":
            color_val = site_name
        elif color_by == "age_group":
            age = patient.get('age', 0)
            if age < 30:
                color_val = "Young (< 30)"
            elif age < 50:
                color_val = "Middle (30-50)"
            elif age < 70:
                color_val = "Senior (50-70)" 
            else:
                color_val = "Elderly (70+)"
        elif color_by == "sex":
            color_val = patient.get('sex', 'Unknown')
        else:
            color_val = site_name
        
        # Size assignment
        if size_by == "lab_value":
            size_val = max(5, min(20, abs(z_coord) / 2))
        elif size_by == "age":
            size_val = max(5, min(20, patient.get('age', 30) / 4))
        else:
            size_val = 8
        
        plot_data.append({
            'x': x_coord,
            'y': y_coord,
            'z': z_coord,
            'color': color_val,
            'size': size_val,
            'site': site_name,
            'patient': usubjid,
            'age': patient.get('age', 'N/A'),
            'sex': patient.get('sex', 'N/A')
        })
    
    if not plot_data:
        fig.add_annotation(
            text=f"No valid data for {selected_test}",
            x=0.5, y=0.5, z=0.5,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            title=f'3D Lab Data Explorer - {selected_test}',
            scene=dict(
                xaxis_title='Site Dimension',
                yaxis_title='Patient Dimension',
                zaxis_title=f'{selected_test} Value'
            ),
            height=600
        )
        return fig
    
    # Convert to arrays for plotting
    x_vals = [d['x'] for d in plot_data]
    y_vals = [d['y'] for d in plot_data]
    z_vals = [d['z'] for d in plot_data]
    colors = [d['color'] for d in plot_data]
    sizes = [d['size'] for d in plot_data]
    
    # Create hover text
    hover_text = []
    for d in plot_data:
        text = f"<b>Patient: {d['patient']}</b><br>"
        text += f"Site: {d['site']}<br>"
        text += f"Age: {d['age']}<br>"
        text += f"Sex: {d['sex']}<br>"
        text += f"{selected_test}: {d['z']:.2f}"
        hover_text.append(text)
    
    fig.add_trace(go.Scatter3d(
        x=x_vals,
        y=y_vals,
        z=z_vals,
        mode='markers',
        marker=dict(
            size=sizes,
            color=colors,
            colorscale='Viridis' if color_by == "site" else 'Plasma',
            showscale=True,
            opacity=0.7,
            line=dict(width=1, color='white'),
            colorbar=dict(title=color_by.replace('_', ' ').title())
        ),
        text=hover_text,
        hovertemplate='%{text}<extra></extra>',
        name='Lab Data'
    ))
    
    # Get lab test name for title
    test_name = selected_test
    if filtered_labs:
        test_name = filtered_labs[0].get('lbtest', selected_test)
    
    fig.update_layout(
        title=f'3D Lab Data Explorer - {test_name}',
        scene=dict(
            xaxis_title='Site Index',
            yaxis_title='Patient Index',
            zaxis_title=f'{test_name} Value',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            ),
            aspectmode='cube'
        ),
        height=600,
        margin=dict(l=0, r=0, t=50, b=0),
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left", 
            x=0.01
        )
    )
    
    return fig

def create_patient_disposition_sankey(patients_data: List[Dict], sites_data: List[Dict], 
                                     view_mode: str = "overall", numbers_mode: str = "absolute") -> go.Figure:
    """
    Create Sankey diagram showing patient disposition flow.
    
    Args:
        patients_data: Patient data from API (with status field)
        sites_data: Site data for grouping
        view_mode: "overall", "by_site", "by_country"  
        numbers_mode: "absolute", "percentage", "both"
        
    Returns:
        go.Figure: Sankey diagram
    """
    fig = go.Figure()
    
    if not patients_data:
        # Sample Sankey data for demonstration
        sample_data = {
            'Screened': 1250,
            'Enrolled': 1000,
            'Completed': 850,
            'Withdrawn': 150
        }
        
        # Create sample Sankey flows
        fig.add_trace(go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=["Screened", "Enrolled", "Completed", "Withdrawn", "Screen Failed"],
                color=["lightblue", "lightgreen", "darkgreen", "orange", "lightcoral"]
            ),
            link=dict(
                source=[0, 1, 1, 0],  # Screened -> Enrolled, Enrolled -> Completed, Enrolled -> Withdrawn, Screened -> Screen Failed
                target=[1, 2, 3, 4],  # 
                value=[1000, 850, 150, 250],
                color=["rgba(0,255,0,0.3)", "rgba(0,150,0,0.3)", "rgba(255,165,0,0.3)", "rgba(255,99,71,0.3)"]
            )
        ))
        
        fig.update_layout(
            title_text=f"Patient Disposition Flow (Sample Data) - {view_mode.replace('_', ' ').title()}",
            font_size=10,
            height=500
        )
        return fig
    
    # Create site mapping if needed
    site_map = {site['site_id']: site for site in sites_data} if sites_data else {}
    
    # Process patient data and assign statuses if not present
    processed_patients = []
    for patient in patients_data:
        # If no status field, infer from other data or assign randomly for demo
        status = patient.get('status')
        if not status:
            # Assign realistic status distribution for demo
            import random
            random.seed(hash(patient.get('usubjid', '')) % 1000)  # Deterministic random based on ID
            rand = random.random()
            if rand < 0.05:  # 5% screen failed
                status = "Screen Failed"
            elif rand < 0.85:  # 80% enrolled
                if rand < 0.75:  # 70% completed
                    status = "Completed"
                else:  # 10% active
                    status = "Active"
            else:  # 15% withdrawn
                status = "Withdrawn"
        
        processed_patients.append({
            **patient,
            'status': status
        })
    
    if view_mode == "overall":
        # Create overall flow
        status_counts = {}
        for patient in processed_patients:
            status = patient['status']
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Define typical clinical trial flow
        total_screened = len(processed_patients) + status_counts.get('Screen Failed', 0)
        total_enrolled = status_counts.get('Enrolled', 0) + status_counts.get('Active', 0) + status_counts.get('Completed', 0) + status_counts.get('Withdrawn', 0)
        
        # Node labels and colors
        node_labels = ["Screened", "Enrolled", "Active", "Completed", "Withdrawn", "Screen Failed"]
        node_colors = ["lightblue", "lightgreen", "yellow", "darkgreen", "orange", "lightcoral"]
        
        # Link sources, targets, and values
        source_indices = []
        target_indices = []
        values = []
        link_colors = []
        
        # Screened -> Enrolled
        if total_enrolled > 0:
            source_indices.append(0)  # Screened
            target_indices.append(1)  # Enrolled
            values.append(total_enrolled)
            link_colors.append("rgba(0,255,0,0.3)")
        
        # Screened -> Screen Failed  
        screen_failed = status_counts.get('Screen Failed', 0)
        if screen_failed > 0:
            source_indices.append(0)  # Screened
            target_indices.append(5)  # Screen Failed
            values.append(screen_failed)
            link_colors.append("rgba(255,99,71,0.3)")
        
        # Enrolled -> Active
        active = status_counts.get('Active', 0)
        if active > 0:
            source_indices.append(1)  # Enrolled
            target_indices.append(2)  # Active
            values.append(active)
            link_colors.append("rgba(255,255,0,0.3)")
        
        # Enrolled -> Completed
        completed = status_counts.get('Completed', 0)
        if completed > 0:
            source_indices.append(1)  # Enrolled
            target_indices.append(3)  # Completed
            values.append(completed)
            link_colors.append("rgba(0,150,0,0.3)")
        
        # Enrolled -> Withdrawn
        withdrawn = status_counts.get('Withdrawn', 0)
        if withdrawn > 0:
            source_indices.append(1)  # Enrolled
            target_indices.append(4)  # Withdrawn
            values.append(withdrawn)
            link_colors.append("rgba(255,165,0,0.3)")
        
        # Format labels with numbers if requested
        if numbers_mode == "absolute":
            formatted_labels = [f"{label}<br>({total_screened if i==0 else status_counts.get(status_mapping.get(i, ''), 0)})" 
                             for i, label in enumerate(node_labels)]
        elif numbers_mode == "percentage":
            formatted_labels = [f"{label}<br>({(total_screened if i==0 else status_counts.get(status_mapping.get(i, ''), 0))/total_screened*100:.1f}%)" 
                             for i, label in enumerate(node_labels)]
        else:  # both
            formatted_labels = [f"{label}<br>({total_screened if i==0 else status_counts.get(status_mapping.get(i, ''), 0)}) - {(total_screened if i==0 else status_counts.get(status_mapping.get(i, ''), 0))/total_screened*100:.1f}%" 
                             for i, label in enumerate(node_labels)]
        
        status_mapping = {0: 'Screened', 1: 'Enrolled', 2: 'Active', 3: 'Completed', 4: 'Withdrawn', 5: 'Screen Failed'}
        
        fig.add_trace(go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=formatted_labels if numbers_mode != "absolute" else node_labels,
                color=node_colors
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
                color=link_colors
            )
        ))
        
        fig.update_layout(
            title_text=f"Patient Disposition Flow - Overall Study",
            font_size=10,
            height=500
        )
        
    elif view_mode == "by_site":
        # Group by site and create multi-level Sankey
        site_status = {}
        for patient in processed_patients:
            site_id = patient.get('site_id', 'Unknown')
            status = patient.get('status', 'Unknown')
            site_name = site_map.get(site_id, {}).get('site_name', site_id)
            
            if site_name not in site_status:
                site_status[site_name] = {}
            site_status[site_name][status] = site_status[site_name].get(status, 0) + 1
        
        # Create nodes: Sites -> Status
        node_labels = []
        node_colors = []
        
        # Add site nodes
        site_colors = ['lightblue', 'lightcyan', 'palegreen', 'wheat', 'lavender']
        for i, site in enumerate(sorted(site_status.keys())):
            node_labels.append(f"Site: {site}")
            node_colors.append(site_colors[i % len(site_colors)])
        
        # Add status nodes
        all_statuses = set()
        for site_data in site_status.values():
            all_statuses.update(site_data.keys())
        
        status_colors_map = {
            'Completed': 'darkgreen',
            'Active': 'yellow', 
            'Withdrawn': 'orange',
            'Screen Failed': 'lightcoral',
            'Enrolled': 'lightgreen'
        }
        
        for status in sorted(all_statuses):
            node_labels.append(status)
            node_colors.append(status_colors_map.get(status, 'lightgray'))
        
        # Create links
        source_indices = []
        target_indices = []
        values = []
        link_colors = []
        
        site_names = sorted(site_status.keys())
        status_names = sorted(all_statuses)
        
        for site_idx, site in enumerate(site_names):
            for status in site_status[site]:
                if site_status[site][status] > 0:
                    status_idx = len(site_names) + status_names.index(status)
                    source_indices.append(site_idx)
                    target_indices.append(status_idx)
                    values.append(site_status[site][status])
                    link_colors.append("rgba(0,100,200,0.3)")
        
        fig.add_trace(go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=node_labels,
                color=node_colors
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
                color=link_colors
            )
        ))
        
        fig.update_layout(
            title_text=f"Patient Disposition Flow - By Site",
            font_size=10,
            height=500
        )
    
    else:  # by_country
        # Group by country 
        country_status = {}
        for patient in processed_patients:
            site_id = patient.get('site_id', 'Unknown')
            status = patient.get('status', 'Unknown')
            site_info = site_map.get(site_id, {})
            country = site_info.get('country', 'Unknown')
            
            if country not in country_status:
                country_status[country] = {}
            country_status[country][status] = country_status[country].get(status, 0) + 1
        
        # Similar structure as by_site but for countries
        node_labels = []
        node_colors = []
        
        # Add country nodes
        country_colors = ['lightsteelblue', 'lightpink', 'lightgoldenrodyellow', 'lightseagreen', 'plum']
        for i, country in enumerate(sorted(country_status.keys())):
            node_labels.append(f"Country: {country}")
            node_colors.append(country_colors[i % len(country_colors)])
        
        # Add status nodes
        all_statuses = set()
        for country_data in country_status.values():
            all_statuses.update(country_data.keys())
        
        status_colors_map = {
            'Completed': 'darkgreen',
            'Active': 'yellow', 
            'Withdrawn': 'orange',
            'Screen Failed': 'lightcoral',
            'Enrolled': 'lightgreen'
        }
        
        for status in sorted(all_statuses):
            node_labels.append(status)
            node_colors.append(status_colors_map.get(status, 'lightgray'))
        
        # Create links
        source_indices = []
        target_indices = []
        values = []
        link_colors = []
        
        country_names = sorted(country_status.keys())
        status_names = sorted(all_statuses)
        
        for country_idx, country in enumerate(country_names):
            for status in country_status[country]:
                if country_status[country][status] > 0:
                    status_idx = len(country_names) + status_names.index(status)
                    source_indices.append(country_idx)
                    target_indices.append(status_idx)
                    values.append(country_status[country][status])
                    link_colors.append("rgba(100,0,200,0.3)")
        
        fig.add_trace(go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=node_labels,
                color=node_colors
            ),
            link=dict(
                source=source_indices,
                target=target_indices,
                value=values,
                color=link_colors
            )
        ))
        
        fig.update_layout(
            title_text=f"Patient Disposition Flow - By Country", 
            font_size=10,
            height=500
        )
    
    return fig

def generate_dashboard_pdf(api_data: Dict, report_type: str = "executive", 
                          sections: List[str] = None, filters: Dict = None) -> bytes:
    """
    Generate PDF report from dashboard data.
    
    Args:
        api_data: Complete dashboard data
        report_type: Type of report ("executive", "detailed", "site_performance", "data_quality")
        sections: List of sections to include in report
        filters: Applied filters for data context
        
    Returns:
        bytes: PDF content
    """
    try:
        from fpdf import FPDF
        
        # Create PDF instance
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        
        # Add title
        title_map = {
            "executive": "Clinical Trial Executive Summary",
            "detailed": "Detailed Clinical Trial Analysis", 
            "site_performance": "Site Performance Report",
            "data_quality": "Data Quality Assessment Report"
        }
        
        title = title_map.get(report_type, "Clinical Trial Dashboard Report")
        pdf.cell(0, 10, title, 0, 1, 'C')
        pdf.ln(5)
        
        # Add generation timestamp
        pdf.set_font('Arial', '', 10)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        pdf.cell(0, 10, f'Generated on: {timestamp}', 0, 1, 'C')
        pdf.ln(10)
        
        # Add filter information if applicable
        if filters and any(filters.values()):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Applied Filters:', 0, 1, 'L')
            pdf.set_font('Arial', '', 10)
            
            if filters.get('site_filter'):
                sites = ', '.join(filters['site_filter']) if isinstance(filters['site_filter'], list) else str(filters['site_filter'])
                pdf.cell(0, 8, f'Selected Sites: {sites}', 0, 1, 'L')
            
            if filters.get('country_filter'):
                countries = ', '.join(filters['country_filter']) if isinstance(filters['country_filter'], list) else str(filters['country_filter'])
                pdf.cell(0, 8, f'Selected Countries: {countries}', 0, 1, 'L')
            
            pdf.ln(10)
        
        # Add summary statistics
        stats = api_data.get('stats', {})
        sites_data = api_data.get('sites', [])
        patients_data = api_data.get('patients', [])
        
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, 'Study Overview', 0, 1, 'L')
        pdf.set_font('Arial', '', 10)
        
        # Key metrics
        total_sites = len(sites_data)
        total_patients = len(patients_data)
        
        pdf.cell(0, 8, f'Total Sites: {total_sites}', 0, 1, 'L')
        pdf.cell(0, 8, f'Total Patients: {total_patients}', 0, 1, 'L')
        pdf.cell(0, 8, f'Total Visits: {stats.get("total_visits", "N/A")}', 0, 1, 'L')
        pdf.cell(0, 8, f'Lab Results: {stats.get("total_labs", "N/A")}', 0, 1, 'L')
        pdf.ln(10)
        
        # Enrollment summary
        if "enrollment" in (sections or []):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Enrollment Summary', 0, 1, 'L')
            pdf.set_font('Arial', '', 10)
            
            # Calculate enrollment rate
            if sites_data:
                total_target = sum(site.get('enrollment_target', 0) for site in sites_data)
                total_current = sum(site.get('current_enrollment', 0) for site in sites_data)
                enrollment_rate = (total_current / total_target * 100) if total_target > 0 else 0
                
                pdf.cell(0, 8, f'Overall Enrollment Rate: {enrollment_rate:.1f}%', 0, 1, 'L')
                pdf.cell(0, 8, f'Target Enrollment: {total_target}', 0, 1, 'L')
                pdf.cell(0, 8, f'Current Enrollment: {total_current}', 0, 1, 'L')
            
            pdf.ln(10)
        
        # Site performance section
        if "site_map" in (sections or []) and sites_data:
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Site Performance', 0, 1, 'L')
            pdf.set_font('Arial', '', 10)
            
            # Top performing sites
            sites_sorted = sorted(sites_data, 
                                key=lambda x: (x.get('current_enrollment', 0) / max(x.get('enrollment_target', 1), 1)), 
                                reverse=True)
            
            pdf.cell(0, 8, 'Top Performing Sites:', 0, 1, 'L')
            for i, site in enumerate(sites_sorted[:5]):
                site_name = site.get('site_name', 'Unknown')[:30]  # Truncate long names
                current = site.get('current_enrollment', 0)
                target = site.get('enrollment_target', 1)
                rate = (current / target * 100) if target > 0 else 0
                pdf.cell(0, 6, f'{i+1}. {site_name}: {current}/{target} ({rate:.1f}%)', 0, 1, 'L')
            
            pdf.ln(10)
        
        # Data quality section
        if "data_quality" in (sections or []):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Data Quality Assessment', 0, 1, 'L')
            pdf.set_font('Arial', '', 10)
            
            # Detect quality issues
            quality_issues = detect_data_quality_issues(
                patients_data, 
                api_data.get('labs', []), 
                api_data.get('visits', []), 
                sites_data
            )
            
            if quality_issues:
                severity_counts = {}
                for issue in quality_issues:
                    severity = issue.get('severity', 'Unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                pdf.cell(0, 8, f'Total Quality Issues: {len(quality_issues)}', 0, 1, 'L')
                for severity, count in sorted(severity_counts.items()):
                    pdf.cell(0, 6, f'  - {severity}: {count}', 0, 1, 'L')
            else:
                pdf.cell(0, 8, 'No data quality issues detected.', 0, 1, 'L')
            
            pdf.ln(10)
        
        # Laboratory analysis section
        if "lab_analysis" in (sections or []):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Laboratory Analysis', 0, 1, 'L')
            pdf.set_font('Arial', '', 10)
            
            lab_abnormalities = stats.get('lab_abnormalities', [])
            if lab_abnormalities:
                pdf.cell(0, 8, 'Lab Result Distribution:', 0, 1, 'L')
                for abnorm in lab_abnormalities:
                    status = abnorm.get('status', 'Unknown')
                    count = abnorm.get('count', 0)
                    pdf.cell(0, 6, f'  - {status}: {count}', 0, 1, 'L')
            else:
                pdf.cell(0, 8, 'No lab analysis data available.', 0, 1, 'L')
            
            pdf.ln(10)
        
        # Patient disposition section
        if "disposition" in (sections or []):
            pdf.set_font('Arial', 'B', 12)
            pdf.cell(0, 10, 'Patient Disposition', 0, 1, 'L')
            pdf.set_font('Arial', '', 10)
            
            # Calculate disposition statistics
            status_counts = {}
            for patient in patients_data:
                # Assign status if not present (same logic as Sankey)
                status = patient.get('status')
                if not status:
                    import random
                    random.seed(hash(patient.get('usubjid', '')) % 1000)
                    rand = random.random()
                    if rand < 0.05:
                        status = "Screen Failed"
                    elif rand < 0.85:
                        if rand < 0.75:
                            status = "Completed"
                        else:
                            status = "Active"
                    else:
                        status = "Withdrawn"
                
                status_counts[status] = status_counts.get(status, 0) + 1
            
            if status_counts:
                total = sum(status_counts.values())
                pdf.cell(0, 8, 'Patient Status Distribution:', 0, 1, 'L')
                for status, count in sorted(status_counts.items()):
                    percentage = (count / total * 100) if total > 0 else 0
                    pdf.cell(0, 6, f'  - {status}: {count} ({percentage:.1f}%)', 0, 1, 'L')
            
            pdf.ln(10)
        
        # Add footer
        pdf.ln(20)
        pdf.set_font('Arial', 'I', 8)
        pdf.cell(0, 10, 'Generated by DCRI Clinical Trial Analytics Dashboard', 0, 1, 'C')
        pdf.cell(0, 10, 'This report contains confidential clinical trial data', 0, 1, 'C')
        
        return pdf.output(dest='S').encode('latin-1')
        
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        # Return a simple error PDF
        from fpdf import FPDF
        error_pdf = FPDF()
        error_pdf.add_page()
        error_pdf.set_font('Arial', 'B', 16)
        error_pdf.cell(0, 10, 'PDF Generation Error', 0, 1, 'C')
        error_pdf.set_font('Arial', '', 12)
        error_pdf.cell(0, 10, f'Error: {str(e)}', 0, 1, 'L')
        return error_pdf.output(dest='S').encode('latin-1')

def detect_data_quality_issues(patients_data: List[Dict], labs_data: List[Dict], visits_data: List[Dict], sites_data: List[Dict]) -> List[Dict]:
    """
    Detect data quality issues in clinical trial data.
    
    Args:
        patients_data: Patient data from API
        labs_data: Laboratory data from API
        visits_data: Visit data from API
        sites_data: Site data for site names
        
    Returns:
        List[Dict]: Data quality issues with details
    """
    issues = []
    
    if not patients_data or not labs_data:
        return issues
    
    # Create mappings
    site_map = {site['site_id']: site.get('site_name', site['site_id']) for site in sites_data} if sites_data else {}
    patient_map = {p['usubjid']: p for p in patients_data}
    
    # Track patients with visits and labs
    patients_with_visits = set()
    patients_with_labs = set()
    
    if visits_data:
        for visit in visits_data:
            patients_with_visits.add(visit.get('usubjid'))
    
    for lab in labs_data:
        patients_with_labs.add(lab.get('usubjid'))
    
    # Check for missing visit data
    for patient in patients_data:
        usubjid = patient.get('usubjid')
        site_id = patient.get('site_id')
        site_name = site_map.get(site_id, site_id)
        
        # Missing visit data
        if usubjid not in patients_with_visits:
            issues.append({
                'issue_type': 'Missing Visit Data',
                'severity': 'High',
                'patient_id': usubjid,
                'site_id': site_id,
                'site_name': site_name,
                'description': 'Patient has no recorded visits',
                'field': 'visits',
                'value': 'N/A'
            })
        
        # Missing lab data
        if usubjid not in patients_with_labs:
            issues.append({
                'issue_type': 'Missing Lab Data',
                'severity': 'High',
                'patient_id': usubjid,
                'site_id': site_id,
                'site_name': site_name,
                'description': 'Patient has no recorded lab results',
                'field': 'labs',
                'value': 'N/A'
            })
        
        # Missing critical patient fields
        if not patient.get('date_of_enrollment'):
            issues.append({
                'issue_type': 'Missing Enrollment Date',
                'severity': 'Critical',
                'patient_id': usubjid,
                'site_id': site_id,
                'site_name': site_name,
                'description': 'Patient missing enrollment date',
                'field': 'date_of_enrollment',
                'value': 'NULL'
            })
        
        if not patient.get('age') or patient.get('age') == 0:
            issues.append({
                'issue_type': 'Missing Age',
                'severity': 'Medium',
                'patient_id': usubjid,
                'site_id': site_id,
                'site_name': site_name,
                'description': 'Patient age is missing or invalid',
                'field': 'age',
                'value': patient.get('age', 'NULL')
            })
    
    # Check lab values for out-of-range issues
    for lab in labs_data:
        usubjid = lab.get('usubjid')
        patient = patient_map.get(usubjid)
        if not patient:
            continue
            
        site_id = patient.get('site_id')
        site_name = site_map.get(site_id, site_id)
        lbstresn = lab.get('lbstresn')
        lbtestcd = lab.get('lbtestcd')
        lbtest = lab.get('lbtest', lbtestcd)
        
        # Missing lab result value
        if lbstresn is None or lbstresn == '':
            issues.append({
                'issue_type': 'Missing Lab Value',
                'severity': 'High',
                'patient_id': usubjid,
                'site_id': site_id,
                'site_name': site_name,
                'description': f'Missing {lbtest} result value',
                'field': f'{lbtestcd}_result',
                'value': 'NULL'
            })
            continue
        
        # Check for extreme outliers (basic range checks)
        try:
            value = float(lbstresn)
            is_outlier = False
            outlier_description = ""
            
            # Define basic acceptable ranges for common labs
            ranges = {
                'HGB': (5.0, 20.0),      # Hemoglobin: 5-20 g/dL
                'GLUC': (20.0, 500.0),   # Glucose: 20-500 mg/dL
                'CREAT': (0.1, 15.0),    # Creatinine: 0.1-15.0 mg/dL
                'WBC': (0.5, 50.0),      # WBC: 0.5-50 K/uL
                'ALT': (1.0, 500.0),     # ALT: 1-500 U/L
                'CHOL': (50.0, 500.0),   # Cholesterol: 50-500 mg/dL
                'HDL': (10.0, 150.0),    # HDL: 10-150 mg/dL
                'LDL': (10.0, 300.0),    # LDL: 10-300 mg/dL
                'TRIG': (20.0, 1000.0),  # Triglycerides: 20-1000 mg/dL
                'HBA1C': (2.0, 20.0)     # HbA1c: 2-20 %
            }
            
            if lbtestcd in ranges:
                min_val, max_val = ranges[lbtestcd]
                if value < min_val:
                    is_outlier = True
                    outlier_description = f'{lbtest} value {value} is extremely low (< {min_val})'
                elif value > max_val:
                    is_outlier = True
                    outlier_description = f'{lbtest} value {value} is extremely high (> {max_val})'
            
            if is_outlier:
                issues.append({
                    'issue_type': 'Extreme Lab Value',
                    'severity': 'High',
                    'patient_id': usubjid,
                    'site_id': site_id,
                    'site_name': site_name,
                    'description': outlier_description,
                    'field': f'{lbtestcd}_value',
                    'value': str(value)
                })
        except (ValueError, TypeError):
            # Invalid numeric value
            issues.append({
                'issue_type': 'Invalid Lab Value',
                'severity': 'High',
                'patient_id': usubjid,
                'site_id': site_id,
                'site_name': site_name,
                'description': f'{lbtest} has invalid numeric value',
                'field': f'{lbtestcd}_value',
                'value': str(lbstresn)
            })
    
    return issues

def create_data_quality_table(quality_issues: List[Dict]) -> dash_table.DataTable:
    """
    Create data quality issues table.
    
    Args:
        quality_issues: List of data quality issues
        
    Returns:
        dash_table.DataTable: Data quality table
    """
    if not quality_issues:
        # Show message when no issues
        return html.Div([
            html.I(className="fas fa-check-circle text-success me-2", style={"fontSize": "24px"}),
            html.Span("No data quality issues detected!", className="h5 text-success")
        ], className="text-center p-4")
    
    # Create DataFrame for the table
    df = pd.DataFrame(quality_issues)
    
    # Define severity colors
    severity_colors = {
        'Critical': '#dc3545',  # Red
        'High': '#fd7e14',      # Orange  
        'Medium': '#ffc107',    # Yellow
        'Low': '#28a745'        # Green
    }
    
    # Create severity style conditions
    style_conditions = []
    for severity, color in severity_colors.items():
        style_conditions.append({
            'if': {'filter_query': f'{{severity}} = {severity}'},
            'backgroundColor': f'{color}20',  # 20% opacity
            'border': f'1px solid {color}40'
        })
    
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=[
            {"name": "Severity", "id": "severity", "type": "text"},
            {"name": "Issue Type", "id": "issue_type", "type": "text"},
            {"name": "Patient ID", "id": "patient_id", "type": "text"},
            {"name": "Site", "id": "site_name", "type": "text"},
            {"name": "Field", "id": "field", "type": "text"},
            {"name": "Value", "id": "value", "type": "text"},
            {"name": "Description", "id": "description", "type": "text"}
        ],
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '14px',
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'border': '1px solid #dee2e6'
        },
        style_data_conditional=style_conditions,
        style_table={'overflowX': 'auto'},
        sort_action="native",
        filter_action="native",
        page_action="native",
        page_current=0,
        page_size=10,
        export_format="csv",
        export_headers="display"
    )

def create_data_table(patients_data: List[Dict]) -> dash_table.DataTable:
    """
    Create interactive data table for patients.
    
    Args:
        patients_data: Patient data from API
        
    Returns:
        dash_table.DataTable: Interactive data table
    """
    if not patients_data:
        # Sample data for demonstration
        sample_data = [
            {"usubjid": "SUBJ001", "site_id": "SITE001", "age": 45, "sex": "F", "race": "WHITE", "date_of_enrollment": "2024-01-15"},
            {"usubjid": "SUBJ002", "site_id": "SITE001", "age": 62, "sex": "M", "race": "BLACK OR AFRICAN AMERICAN", "date_of_enrollment": "2024-01-18"},
            {"usubjid": "SUBJ003", "site_id": "SITE002", "age": 38, "sex": "F", "race": "ASIAN", "date_of_enrollment": "2024-01-22"},
            {"usubjid": "SUBJ004", "site_id": "SITE001", "age": 71, "sex": "M", "race": "WHITE", "date_of_enrollment": "2024-01-25"},
            {"usubjid": "SUBJ005", "site_id": "SITE003", "age": 29, "sex": "F", "race": "HISPANIC OR LATINO", "date_of_enrollment": "2024-01-28"}
        ]
        patients_data = sample_data
    
    # Convert to DataFrame and limit to recent entries
    df = pd.DataFrame(patients_data)
    if len(df) > 100:
        df = df.head(100)
    
    # Make patient IDs appear clickable
    if 'usubjid' in df.columns:
        df['usubjid'] = df['usubjid'].apply(lambda x: f"**{x}**")
    
    columns = [
        {"name": "Subject ID", "id": "usubjid", "type": "text", "presentation": "markdown"},
        {"name": "Site ID", "id": "site_id", "type": "text"},
        {"name": "Age", "id": "age", "type": "numeric"},
        {"name": "Sex", "id": "sex", "type": "text"},
        {"name": "Race", "id": "race", "type": "text"},
        {"name": "Enrollment Date", "id": "date_of_enrollment", "type": "datetime"}
    ]
    
    return dash_table.DataTable(
        id="patients-table",
        columns=columns,
        data=df.to_dict('records'),
        page_size=20,
        sort_action="native",
        filter_action="native",
        style_cell={
            'textAlign': 'left',
            'padding': '12px',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '14px'
        },
        style_header={
            'backgroundColor': '#007cba',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {'column_id': 'usubjid'},
                'color': '#007cba',
                'cursor': 'pointer',
                'textDecoration': 'underline',
                'fontWeight': 'bold'
            }
        ],
        export_format='csv',
        export_headers='display'
    )

def register_callbacks(app: dash.Dash) -> None:
    """
    Register all dashboard callbacks for interactivity.
    
    Args:
        app: Dash application instance
    """
    
    # Main data loading callback
    @app.callback(
        [Output('api-data-store', 'children'),
         Output('site-filter', 'options'),
         Output('country-filter', 'options')],
        [Input('interval-component', 'n_intervals'),
         Input('demo-mode-toggle', 'value')]
    )
    def load_api_data(n_intervals, demo_mode):
        """Load data from API and populate filters."""
        try:
            # If live mode (demo_mode=False), return empty data since no real uploads yet
            if not demo_mode:
                return json.dumps({
                    'stats': {},
                    'sites': [],
                    'patients': [],
                    'timestamp': datetime.now().isoformat(),
                    'demo_mode': False
                }), [], []
            
            # Demo mode - fetch all required data
            stats_data = fetch_api_data("/stats")
            sites_data = fetch_api_data("/sites", {"limit": 100})
            patients_data = fetch_api_data("/patients", {"limit": 100})
            
            # If API calls fail, provide fallback sample data
            if not stats_data:
                stats_data = {
                    "total_sites": 20,
                    "total_patients": 1845,
                    "total_visits": 13602,
                    "lab_abnormalities": [
                        {"status": "NORMAL", "count": 45230},
                        {"status": "HIGH", "count": 25467},
                        {"status": "LOW", "count": 15678},
                        {"status": "CRITICAL", "count": 4330}
                    ],
                    "enrollment_timeline": [
                        {"month": "2024-01", "enrollments": 124},
                        {"month": "2024-02", "enrollments": 145},
                        {"month": "2024-03", "enrollments": 178},
                        {"month": "2024-04", "enrollments": 203},
                        {"month": "2024-05", "enrollments": 189},
                        {"month": "2024-06", "enrollments": 167}
                    ]
                }
            
            # Fallback sample data if API calls fail
            if not sites_data:
                sites_data = [
                    {"site_id": "SITE001", "site_name": "Duke Medical Center", "country": "US", "current_enrollment": 98, "enrollment_rate": 85.3},
                    {"site_id": "SITE002", "site_name": "Toronto General Hospital", "country": "CA", "current_enrollment": 87, "enrollment_rate": 78.1},
                    {"site_id": "SITE003", "site_name": "Royal London Hospital", "country": "GB", "current_enrollment": 76, "enrollment_rate": 92.4},
                    {"site_id": "SITE004", "site_name": "Charité Berlin", "country": "DE", "current_enrollment": 89, "enrollment_rate": 81.7},
                    {"site_id": "SITE005", "site_name": "Hospital Clinic Barcelona", "country": "ES", "current_enrollment": 92, "enrollment_rate": 88.9}
                ]
            
            if not patients_data:
                patients_data = [
                    {"usubjid": "STUDY-001-001", "site_id": "SITE001", "age": 45, "sex": "F", "date_of_enrollment": "2024-01-15"},
                    {"usubjid": "STUDY-001-002", "site_id": "SITE001", "age": 52, "sex": "M", "date_of_enrollment": "2024-01-18"},
                    {"usubjid": "STUDY-002-001", "site_id": "SITE002", "age": 38, "sex": "F", "date_of_enrollment": "2024-01-22"},
                    {"usubjid": "STUDY-003-001", "site_id": "SITE003", "age": 61, "sex": "M", "date_of_enrollment": "2024-01-25"}
                ]
            
            # Create filter options
            site_options = []
            country_options = []
            
            # Country code mapping
            country_names = {
                'US': 'United States',
                'CA': 'Canada', 
                'DE': 'Germany',
                'FR': 'France',
                'ES': 'Spain',
                'KR': 'South Korea',
                'GB': 'United Kingdom',
                'GBR': 'United Kingdom'
            }
            
            if sites_data:
                sites_df = pd.DataFrame(sites_data)
                if not sites_df.empty:
                    # Truncate site names for dropdown display
                    site_options = [{"label": f"{row['site_name'][:40]}{'...' if len(row['site_name']) > 40 else ''} ({row['site_id']})", 
                                   "value": row['site_id']} 
                                  for _, row in sites_df.iterrows()]
                    
                    countries = sites_df['country'].unique()
                    country_options = [{"label": f"{country_names.get(country, country)} ({country})", 
                                      "value": country} 
                                     for country in sorted(countries)]
            
            # Store all data
            api_data = {
                'stats': stats_data,
                'sites': sites_data,
                'patients': patients_data,
                'timestamp': datetime.now().isoformat(),
                'demo_mode': demo_mode
            }
            
            return json.dumps(api_data), site_options, country_options
            
        except Exception as e:
            logger.error(f"Error loading API data: {e}")
            return "{}", [], []
    
    # Metrics cards callback
    @app.callback(
        Output('metrics-cards', 'children'),
        [Input('api-data-store', 'children'),
         Input('site-filter', 'value'),
         Input('country-filter', 'value')]
    )
    def update_metrics_cards(api_data_json, site_filter, country_filter):
        """Update metrics cards display."""
        try:
            if not api_data_json:
                return [html.Div("Loading metrics...", className="col-12 text-center")]
            
            api_data = json.loads(api_data_json)
            stats_data = api_data.get('stats', {})
            sites_data = api_data.get('sites', [])
            patients_data = api_data.get('patients', [])
            
            # Apply filters and calculate filtered metrics
            filtered_sites = sites_data
            filtered_patients = patients_data
            
            # Handle multi-select filters
            if site_filter:
                site_filter = site_filter if isinstance(site_filter, list) else [site_filter]
                filtered_sites = [site for site in sites_data if site.get('site_id') in site_filter]
                filtered_patients = [patient for patient in patients_data if patient.get('site_id') in site_filter]
            elif country_filter:
                country_filter = country_filter if isinstance(country_filter, list) else [country_filter]
                filtered_site_ids = [site['site_id'] for site in sites_data if site.get('country') in country_filter]
                filtered_sites = [site for site in sites_data if site.get('country') in country_filter]
                filtered_patients = [patient for patient in patients_data if patient.get('site_id') in filtered_site_ids]
            
            # Create filtered stats
            filtered_stats = {
                'total_sites': len(filtered_sites),
                'total_patients': len(filtered_patients),
                'total_visits': stats_data.get('total_visits', 0),  # Will be filtered in future
                'total_labs': stats_data.get('total_labs', 0)      # Will be filtered in future
            }
            
            # Determine if we're showing filtered data
            is_filtered = bool(site_filter or country_filter)
            
            return create_metrics_cards(filtered_stats, is_filtered)
        except Exception as e:
            logger.error(f"Error updating metrics cards: {e}")
            return [html.Div("Error loading metrics", className="col-12 text-center text-danger")]
    
    # Enrollment chart callback
    @app.callback(
        Output('enrollment-chart', 'figure'),
        [Input('api-data-store', 'children'),
         Input('site-filter', 'value'),
         Input('country-filter', 'value')]
    )
    def update_enrollment_chart(api_data_json, site_filter, country_filter):
        """Update enrollment timeline chart."""
        try:
            if not api_data_json:
                return create_enrollment_chart({})
            
            api_data = json.loads(api_data_json)
            stats_data = api_data.get('stats', {})
            sites_data = api_data.get('sites', [])
            patients_data = api_data.get('patients', [])
            demo_mode = api_data.get('demo_mode', False)
            
            # Apply filters to data - handle multi-select
            if site_filter:
                site_filter = site_filter if isinstance(site_filter, list) else [site_filter]
                sites_data = [site for site in sites_data if site.get('site_id') in site_filter]
                patients_data = [patient for patient in patients_data if patient.get('site_id') in site_filter]
            elif country_filter:
                country_filter = country_filter if isinstance(country_filter, list) else [country_filter]
                sites_data = [site for site in sites_data if site.get('country') in country_filter]
                filtered_site_ids = [site['site_id'] for site in sites_data]
                patients_data = [patient for patient in patients_data if patient.get('site_id') in filtered_site_ids]
            
            # Update stats based on filtered data 
            if site_filter or country_filter:
                stats_data = stats_data.copy()  # Don't modify original
                stats_data['total_patients'] = len(patients_data)
                # Generate filtered enrollment timeline from filtered patients
                if patients_data:
                    # Group patients by enrollment month
                    from collections import defaultdict
                    import pandas as pd
                    
                    monthly_enrollments = defaultdict(int)
                    for patient in patients_data:
                        if patient.get('date_of_enrollment'):
                            # Convert to datetime and extract year-month
                            try:
                                enroll_date = pd.to_datetime(patient['date_of_enrollment'])
                                month_key = enroll_date.strftime('%Y-%m')
                                monthly_enrollments[month_key] += 1
                            except:
                                continue
                    
                    # Create enrollment timeline data
                    timeline_data = []
                    for month, count in sorted(monthly_enrollments.items()):
                        timeline_data.append({
                            'month': month,
                            'enrollments': count
                        })
                    
                    stats_data['enrollment_timeline'] = timeline_data
            
            return create_enrollment_chart(stats_data, demo_mode)
        except Exception as e:
            logger.error(f"Error updating enrollment chart: {e}")
            return create_enrollment_chart({})
    
    # Site risk map callback
    @app.callback(
        Output('site-risk-map', 'figure'),
        [Input('api-data-store', 'children'),
         Input('site-filter', 'value'),
         Input('country-filter', 'value')]
    )
    def update_site_risk_map(api_data_json, site_filter, country_filter):
        """Update site risk assessment map."""
        try:
            if not api_data_json:
                return create_site_risk_map([])
            
            api_data = json.loads(api_data_json)
            sites_data = api_data.get('sites', [])
            
            # Apply filters - handle multi-select
            if site_filter:
                site_filter = site_filter if isinstance(site_filter, list) else [site_filter]
                sites_data = [site for site in sites_data if site.get('site_id') in site_filter]
            elif country_filter:
                country_filter = country_filter if isinstance(country_filter, list) else [country_filter]
                sites_data = [site for site in sites_data if site.get('country') in country_filter]
            
            return create_site_risk_map(sites_data)
        except Exception as e:
            logger.error(f"Error updating site risk map: {e}")
            return create_site_risk_map([])
    
    # Lab analysis chart callback
    @app.callback(
        Output('lab-analysis-chart', 'figure'),
        [Input('api-data-store', 'children'),
         Input('site-filter', 'value'),
         Input('country-filter', 'value')]
    )
    def update_lab_analysis_chart(api_data_json, site_filter, country_filter):
        """Update laboratory analysis chart."""
        try:
            if not api_data_json:
                return create_lab_analysis_chart()
            
            api_data = json.loads(api_data_json)
            stats_data = api_data.get('stats', {})
            sites_data = api_data.get('sites', [])
            patients_data = api_data.get('patients', [])
            labs_data = api_data.get('labs', [])
            lab_abnormalities = stats_data.get('lab_abnormalities', {})
            
            # Apply filters to lab data
            if site_filter or country_filter:
                # Filter sites based on selection
                filtered_site_ids = set()
                
                if isinstance(country_filter, list) and country_filter:
                    # Filter by country
                    for site in sites_data:
                        if site.get('country') in country_filter:
                            filtered_site_ids.add(site.get('site_id'))
                elif country_filter:
                    # Single country selection
                    for site in sites_data:
                        if site.get('country') == country_filter:
                            filtered_site_ids.add(site.get('site_id'))
                
                if isinstance(site_filter, list) and site_filter:
                    # Filter by site - intersect with country filter if exists
                    site_filter_ids = set(site_filter)
                    if filtered_site_ids:
                        filtered_site_ids = filtered_site_ids.intersection(site_filter_ids)
                    else:
                        filtered_site_ids = site_filter_ids
                elif site_filter:
                    # Single site selection
                    if filtered_site_ids:
                        if site_filter in filtered_site_ids:
                            filtered_site_ids = {site_filter}
                        else:
                            filtered_site_ids = set()
                    else:
                        filtered_site_ids = {site_filter}
                
                # Filter patients by the filtered sites
                filtered_patient_ids = set()
                for patient in patients_data:
                    if patient.get('site_id') in filtered_site_ids:
                        filtered_patient_ids.add(patient.get('usubjid'))
                
                # Filter lab data by filtered patients and calculate abnormalities
                filtered_lab_abnormalities = {}
                for lab in labs_data:
                    if lab.get('usubjid') in filtered_patient_ids:
                        lbnrind = lab.get('lbnrind')
                        if lbnrind:
                            filtered_lab_abnormalities[lbnrind] = filtered_lab_abnormalities.get(lbnrind, 0) + 1
            else:
                filtered_lab_abnormalities = lab_abnormalities
            
            return create_lab_analysis_chart(filtered_lab_abnormalities)
        except Exception as e:
            logger.error(f"Error updating lab analysis chart: {e}")
            return create_lab_analysis_chart()
    
    # Box plot callback
    @app.callback(
        Output('lab-box-plot', 'figure'),
        [Input('api-data-store', 'children'),
         Input('lab-test-selector', 'value'),
         Input('site-filter', 'value'),
         Input('country-filter', 'value')]
    )
    def update_lab_box_plot(api_data_json, selected_test, site_filter, country_filter):
        """Update laboratory box plot."""
        try:
            if not api_data_json:
                return create_lab_box_plot([], [], [], selected_test)
            
            api_data = json.loads(api_data_json)
            sites_data = api_data.get('sites', [])
            patients_data = api_data.get('patients', [])
            labs_data = api_data.get('labs', [])
            
            # Apply filters to data if needed
            if site_filter or country_filter:
                # Filter sites based on selection
                filtered_site_ids = set()
                
                if isinstance(country_filter, list) and country_filter:
                    # Filter by country
                    for site in sites_data:
                        if site.get('country') in country_filter:
                            filtered_site_ids.add(site.get('site_id'))
                elif country_filter:
                    # Single country selection
                    for site in sites_data:
                        if site.get('country') == country_filter:
                            filtered_site_ids.add(site.get('site_id'))
                
                if isinstance(site_filter, list) and site_filter:
                    # Filter by site - intersect with country filter if exists
                    site_filter_ids = set(site_filter)
                    if filtered_site_ids:
                        filtered_site_ids = filtered_site_ids.intersection(site_filter_ids)
                    else:
                        filtered_site_ids = site_filter_ids
                elif site_filter:
                    # Single site selection
                    if filtered_site_ids:
                        if site_filter in filtered_site_ids:
                            filtered_site_ids = {site_filter}
                        else:
                            filtered_site_ids = set()
                    else:
                        filtered_site_ids = {site_filter}
                
                # Filter patients and labs by selected sites
                if filtered_site_ids:
                    filtered_patients = [p for p in patients_data if p.get('site_id') in filtered_site_ids]
                    filtered_patient_ids = {p['usubjid'] for p in filtered_patients}
                    filtered_labs = [lab for lab in labs_data if lab.get('usubjid') in filtered_patient_ids]
                    filtered_sites = [s for s in sites_data if s.get('site_id') in filtered_site_ids]
                else:
                    filtered_patients = []
                    filtered_labs = []
                    filtered_sites = []
            else:
                filtered_patients = patients_data
                filtered_labs = labs_data
                filtered_sites = sites_data
            
            return create_lab_box_plot(filtered_labs, filtered_patients, filtered_sites, selected_test)
        except Exception as e:
            logger.error(f"Error updating lab box plot: {e}")
            return create_lab_box_plot([], [], [], selected_test)
    
    # 3D scatter plot callback
    @app.callback(
        Output('lab-3d-scatter', 'figure'),
        [Input('api-data-store', 'children'),
         Input('lab-test-3d-selector', 'value'),
         Input('color-by-selector', 'value'),
         Input('size-by-selector', 'value'),
         Input('site-filter', 'value'),
         Input('country-filter', 'value')]
    )
    def update_3d_scatter(api_data_json, selected_test, color_by, size_by, site_filter, country_filter):
        """Update 3D lab data scatter plot."""
        try:
            if not api_data_json:
                return create_3d_lab_scatter([], [], [], selected_test, color_by, size_by)
            
            api_data = json.loads(api_data_json)
            sites_data = api_data.get('sites', [])
            patients_data = api_data.get('patients', [])
            labs_data = api_data.get('labs', [])
            
            # Apply filters to data if needed
            if site_filter or country_filter:
                # Filter sites based on selection
                filtered_site_ids = set()
                
                if isinstance(country_filter, list) and country_filter:
                    # Filter by country
                    for site in sites_data:
                        if site.get('country') in country_filter:
                            filtered_site_ids.add(site.get('site_id'))
                elif country_filter:
                    # Single country selection
                    for site in sites_data:
                        if site.get('country') == country_filter:
                            filtered_site_ids.add(site.get('site_id'))
                
                if isinstance(site_filter, list) and site_filter:
                    # Filter by site - intersect with country filter if exists
                    site_filter_ids = set(site_filter)
                    if filtered_site_ids:
                        filtered_site_ids = filtered_site_ids.intersection(site_filter_ids)
                    else:
                        filtered_site_ids = site_filter_ids
                elif site_filter:
                    # Single site selection
                    if filtered_site_ids:
                        if site_filter in filtered_site_ids:
                            filtered_site_ids = {site_filter}
                        else:
                            filtered_site_ids = set()
                    else:
                        filtered_site_ids = {site_filter}
                
                # Filter data by selected sites
                if filtered_site_ids:
                    filtered_patients = [p for p in patients_data if p.get('site_id') in filtered_site_ids]
                    filtered_patient_ids = {p['usubjid'] for p in filtered_patients}
                    filtered_labs = [lab for lab in labs_data if lab.get('usubjid') in filtered_patient_ids]
                    filtered_sites = [s for s in sites_data if s.get('site_id') in filtered_site_ids]
                else:
                    filtered_patients = []
                    filtered_labs = []
                    filtered_sites = []
            else:
                filtered_patients = patients_data
                filtered_labs = labs_data
                filtered_sites = sites_data
            
            return create_3d_lab_scatter(filtered_labs, filtered_patients, filtered_sites, selected_test, color_by, size_by)
        except Exception as e:
            logger.error(f"Error updating 3D scatter plot: {e}")
            return create_3d_lab_scatter([], [], [], selected_test or "HGB", color_by or "site", size_by or "lab_value")
    
    # Sankey diagram callback
    @app.callback(
        Output('patient-disposition-sankey', 'figure'),
        [Input('api-data-store', 'children'),
         Input('sankey-view-selector', 'value'),
         Input('sankey-numbers-toggle', 'value'),
         Input('site-filter', 'value'),
         Input('country-filter', 'value')]
    )
    def update_sankey_diagram(api_data_json, view_mode, numbers_mode, site_filter, country_filter):
        """Update patient disposition Sankey diagram."""
        try:
            if not api_data_json:
                return create_patient_disposition_sankey([], [], view_mode, numbers_mode)
            
            api_data = json.loads(api_data_json)
            sites_data = api_data.get('sites', [])
            patients_data = api_data.get('patients', [])
            
            # Apply filters to data if needed
            if site_filter or country_filter:
                # Filter sites based on selection
                filtered_site_ids = set()
                
                if isinstance(country_filter, list) and country_filter:
                    # Filter by country
                    for site in sites_data:
                        if site.get('country') in country_filter:
                            filtered_site_ids.add(site.get('site_id'))
                elif country_filter:
                    # Single country selection
                    for site in sites_data:
                        if site.get('country') == country_filter:
                            filtered_site_ids.add(site.get('site_id'))
                
                if isinstance(site_filter, list) and site_filter:
                    # Filter by site - intersect with country filter if exists
                    site_filter_ids = set(site_filter)
                    if filtered_site_ids:
                        filtered_site_ids = filtered_site_ids.intersection(site_filter_ids)
                    else:
                        filtered_site_ids = site_filter_ids
                elif site_filter:
                    # Single site selection
                    if filtered_site_ids:
                        if site_filter in filtered_site_ids:
                            filtered_site_ids = {site_filter}
                        else:
                            filtered_site_ids = set()
                    else:
                        filtered_site_ids = {site_filter}
                
                # Filter data by selected sites
                if filtered_site_ids:
                    filtered_patients = [p for p in patients_data if p.get('site_id') in filtered_site_ids]
                    filtered_sites = [s for s in sites_data if s.get('site_id') in filtered_site_ids]
                else:
                    filtered_patients = []
                    filtered_sites = []
            else:
                filtered_patients = patients_data
                filtered_sites = sites_data
            
            return create_patient_disposition_sankey(filtered_patients, filtered_sites, view_mode, numbers_mode)
        except Exception as e:
            logger.error(f"Error updating Sankey diagram: {e}")
            return create_patient_disposition_sankey([], [], view_mode or "overall", numbers_mode or "absolute")
    
    # PDF generation callbacks
    @app.callback(
        [Output("download-pdf", "data"),
         Output("pdf-generation-status", "children")],
        [Input("generate-pdf-btn", "n_clicks"),
         Input("download-sample-pdf-btn", "n_clicks")],
        [State('api-data-store', 'children'),
         State("pdf-report-type", "value"),
         State("pdf-sections-checklist", "value"),
         State('site-filter', 'value'),
         State('country-filter', 'value')],
        prevent_initial_call=True
    )
    def generate_pdf_report(n_clicks_generate, n_clicks_sample, api_data_json, 
                           report_type, sections, site_filter, country_filter):
        """Generate and download PDF report."""
        ctx = dash.callback_context
        if not ctx.triggered:
            return None, ""
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            if button_id == "generate-pdf-btn" and n_clicks_generate:
                if not api_data_json:
                    return None, html.Div([
                        html.I(className="fas fa-exclamation-triangle text-warning me-2"),
                        "No data available for PDF generation"
                    ], className="text-warning")
                
                api_data = json.loads(api_data_json)
                
                # Prepare filter context
                filters = {
                    'site_filter': site_filter,
                    'country_filter': country_filter
                }
                
                # Generate PDF
                pdf_content = generate_dashboard_pdf(
                    api_data=api_data,
                    report_type=report_type or "executive",
                    sections=sections or ["enrollment", "site_map", "data_quality"],
                    filters=filters
                )
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"clinical_trial_report_{report_type}_{timestamp}.pdf"
                
                return dcc.send_bytes(pdf_content, filename), html.Div([
                    html.I(className="fas fa-check-circle text-success me-2"),
                    f"PDF report generated successfully: {filename}"
                ], className="text-success")
            
            elif button_id == "download-sample-pdf-btn" and n_clicks_sample:
                # Generate sample PDF with dummy data
                sample_data = {
                    'stats': {
                        'total_sites': 20,
                        'total_patients': 1845,
                        'total_visits': 13602,
                        'total_labs': 95348,
                        'lab_abnormalities': [
                            {'status': 'NORMAL', 'count': 45230},
                            {'status': 'HIGH', 'count': 25467},
                            {'status': 'LOW', 'count': 15678},
                            {'status': 'CRITICAL', 'count': 4330}
                        ]
                    },
                    'sites': [
                        {'site_id': 'SITE001', 'site_name': 'Duke Medical Center', 'current_enrollment': 98, 'enrollment_target': 100},
                        {'site_id': 'SITE002', 'site_name': 'Johns Hopkins', 'current_enrollment': 92, 'enrollment_target': 100},
                        {'site_id': 'SITE003', 'site_name': 'Mayo Clinic', 'current_enrollment': 89, 'enrollment_target': 100}
                    ],
                    'patients': [
                        {'usubjid': 'STUDY-001-001', 'site_id': 'SITE001', 'age': 45, 'sex': 'F', 'status': 'Completed'},
                        {'usubjid': 'STUDY-001-002', 'site_id': 'SITE001', 'age': 52, 'sex': 'M', 'status': 'Active'},
                        {'usubjid': 'STUDY-002-001', 'site_id': 'SITE002', 'age': 38, 'sex': 'F', 'status': 'Completed'}
                    ],
                    'labs': [],
                    'visits': []
                }
                
                pdf_content = generate_dashboard_pdf(
                    api_data=sample_data,
                    report_type="executive",
                    sections=["enrollment", "site_map", "lab_analysis", "data_quality"],
                    filters={}
                )
                
                return dcc.send_bytes(pdf_content, "sample_clinical_trial_report.pdf"), html.Div([
                    html.I(className="fas fa-download text-info me-2"),
                    "Sample PDF report downloaded"
                ], className="text-info")
            
        except Exception as e:
            logger.error(f"Error in PDF generation: {e}")
            return None, html.Div([
                html.I(className="fas fa-exclamation-circle text-danger me-2"),
                f"Error generating PDF: {str(e)}"
            ], className="text-danger")
        
        return None, ""
    
    # Data quality callback
    @app.callback(
        Output('data-quality-container', 'children'),
        [Input('api-data-store', 'children'),
         Input('site-filter', 'value'),
         Input('country-filter', 'value')]
    )
    def update_data_quality(api_data_json, site_filter, country_filter):
        """Update data quality issues table."""
        try:
            if not api_data_json:
                return create_data_quality_table([])
            
            api_data = json.loads(api_data_json)
            sites_data = api_data.get('sites', [])
            patients_data = api_data.get('patients', [])
            labs_data = api_data.get('labs', [])
            visits_data = api_data.get('visits', [])
            
            # Apply filters to data if needed
            if site_filter or country_filter:
                # Filter sites based on selection
                filtered_site_ids = set()
                
                if isinstance(country_filter, list) and country_filter:
                    # Filter by country
                    for site in sites_data:
                        if site.get('country') in country_filter:
                            filtered_site_ids.add(site.get('site_id'))
                elif country_filter:
                    # Single country selection
                    for site in sites_data:
                        if site.get('country') == country_filter:
                            filtered_site_ids.add(site.get('site_id'))
                
                if isinstance(site_filter, list) and site_filter:
                    # Filter by site - intersect with country filter if exists
                    site_filter_ids = set(site_filter)
                    if filtered_site_ids:
                        filtered_site_ids = filtered_site_ids.intersection(site_filter_ids)
                    else:
                        filtered_site_ids = site_filter_ids
                elif site_filter:
                    # Single site selection
                    if filtered_site_ids:
                        if site_filter in filtered_site_ids:
                            filtered_site_ids = {site_filter}
                        else:
                            filtered_site_ids = set()
                    else:
                        filtered_site_ids = {site_filter}
                
                # Filter data by selected sites
                if filtered_site_ids:
                    filtered_patients = [p for p in patients_data if p.get('site_id') in filtered_site_ids]
                    filtered_patient_ids = {p['usubjid'] for p in filtered_patients}
                    filtered_labs = [lab for lab in labs_data if lab.get('usubjid') in filtered_patient_ids]
                    filtered_visits = [visit for visit in visits_data if visit.get('usubjid') in filtered_patient_ids]
                    filtered_sites = [s for s in sites_data if s.get('site_id') in filtered_site_ids]
                else:
                    filtered_patients = []
                    filtered_labs = []
                    filtered_visits = []
                    filtered_sites = []
            else:
                filtered_patients = patients_data
                filtered_labs = labs_data
                filtered_visits = visits_data
                filtered_sites = sites_data
            
            # Detect data quality issues
            quality_issues = detect_data_quality_issues(
                filtered_patients, filtered_labs, filtered_visits, filtered_sites
            )
            
            return create_data_quality_table(quality_issues)
        except Exception as e:
            logger.error(f"Error updating data quality table: {e}")
            return create_data_quality_table([])
    
    # Data table callback
    @app.callback(
        Output('data-table-container', 'children'),
        [Input('api-data-store', 'children'),
         Input('site-filter', 'value'),
         Input('country-filter', 'value')]
    )
    def update_data_table(api_data_json, site_filter, country_filter):
        """Update patient data table."""
        try:
            if not api_data_json:
                return create_data_table([])
            
            api_data = json.loads(api_data_json)
            patients_data = api_data.get('patients', [])
            sites_data = api_data.get('sites', [])
            
            # Apply filters - handle multi-select
            if site_filter:
                site_filter = site_filter if isinstance(site_filter, list) else [site_filter]
                patients_data = [patient for patient in patients_data 
                               if patient.get('site_id') in site_filter]
            elif country_filter:
                country_filter = country_filter if isinstance(country_filter, list) else [country_filter]
                filtered_site_ids = [site['site_id'] for site in sites_data if site.get('country') in country_filter]
                patients_data = [patient for patient in patients_data 
                               if patient.get('site_id') in filtered_site_ids]
            
            return create_data_table(patients_data)
        except Exception as e:
            logger.error(f"Error updating data table: {e}")
            return html.Div("Error loading patient data", className="text-danger")
    
    # CSV Export callback
    @app.callback(
        Output("download-csv", "data"),
        [Input("export-btn", "n_clicks")],
        [State('api-data-store', 'children')],
        prevent_initial_call=True
    )
    def export_csv(n_clicks, api_data_json):
        """Export current patient data as CSV."""
        try:
            if not n_clicks or not api_data_json:
                return None
            
            api_data = json.loads(api_data_json)
            patients_data = api_data.get('patients', [])
            
            if not patients_data:
                return None
            
            df = pd.DataFrame(patients_data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            return dcc.send_data_frame(
                df.to_csv, 
                filename=f"clinical_trial_patients_{timestamp}.csv"
            )
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return None

    # Site notification system callbacks
    @app.callback(
        Output('selected-site-store', 'children'),
        Input('site-risk-map', 'clickData'),
        State('api-data-store', 'children')
    )
    def handle_site_map_click(clickData, api_data_json):
        """Handle clicks on the site risk map."""
        if not clickData or not api_data_json:
            return ""
            
        try:
            api_data = json.loads(api_data_json)
            sites_data = api_data.get('sites', [])
            
            # Get the clicked point data
            point_index = clickData['points'][0]['pointIndex']
            
            if point_index < len(sites_data):
                selected_site = sites_data[point_index]
                return json.dumps(selected_site)
                
        except Exception as e:
            logger.error(f"Error handling site map click: {e}")
            
        return ""

    @app.callback(
        [Output('notification-content', 'children'),
         Output('email-subject', 'value'),
         Output('email-body', 'value')],
        [Input('selected-site-store', 'children'),
         Input('notification-type', 'value')]
    )
    def update_notification_modal(selected_site_json, notification_type):
        """Update notification modal content based on selected site."""
        if not selected_site_json:
            return "", "", ""
            
        try:
            site_data = json.loads(selected_site_json)
            
            # Generate site summary
            site_name = site_data.get('site_name', 'Unknown Site')
            current_enrollment = site_data.get('current_enrollment', 0)
            target_enrollment = site_data.get('enrollment_target', 100)
            progress = (current_enrollment / target_enrollment * 100) if target_enrollment > 0 else 0
            country = site_data.get('country', 'N/A')
            
            # Create site info card
            site_info = html.Div([
                html.H6(f"Selected Site: {site_name}", className="text-primary"),
                html.P([
                    html.Strong("Country: "), country, html.Br(),
                    html.Strong("Enrollment: "), f"{current_enrollment}/{target_enrollment} ({progress:.1f}%)", html.Br(),
                    html.Strong("Status: "), 
                    html.Span(
                        "Behind Target" if progress < 80 else "On Track",
                        className="badge bg-danger" if progress < 80 else "badge bg-success"
                    )
                ])
            ], className="alert alert-info")
            
            # Generate email template
            email_template = generate_email_template(site_data, notification_type or "follow_up")
            
            return site_info, email_template['subject'], email_template['body']
            
        except Exception as e:
            logger.error(f"Error updating notification modal: {e}")
            return "", "", ""

    @app.callback(
        Output('send-email-btn', 'children'),
        Input('send-email-btn', 'n_clicks'),
        [State('email-subject', 'value'),
         State('email-body', 'value'),
         State('selected-site-store', 'children')]
    )
    def handle_send_email(n_clicks, subject, body, selected_site_json):
        """Handle send email button click."""
        if not n_clicks:
            return "Send Email"
            
        if not subject or not body:
            return "Please fill in subject and body"
            
        try:
            site_data = json.loads(selected_site_json) if selected_site_json else {}
            site_name = site_data.get('site_name', 'Unknown Site')
            
            # In a real implementation, this would integrate with email service
            # For now, we'll just provide feedback
            logger.info(f"Email notification sent to {site_name}")
            return "✓ Email Prepared"
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return "Error sending email"

    # Clientside callback to show modal when site is selected
    app.clientside_callback(
        """
        function(selectedSiteJson) {
            if (selectedSiteJson) {
                // Show the modal using Bootstrap's JavaScript API
                var modal = new bootstrap.Modal(document.getElementById('site-notification-modal'));
                modal.show();
                return 1;
            }
            return 0;
        }
        """,
        Output('selected-site-store', 'data-trigger-modal'),
        Input('selected-site-store', 'children')
    )

    # Patient profile system callbacks
    @app.callback(
        Output('selected-patient-store', 'children'),
        Input('patients-table', 'active_cell'),
        State('api-data-store', 'children')
    )
    def handle_patient_selection(active_cell, api_data_json):
        """Handle patient table cell clicks for patient ID column."""
        if not active_cell or not api_data_json or active_cell.get('column_id') != 'usubjid':
            return ""
            
        try:
            api_data = json.loads(api_data_json)
            patients_data = api_data.get('patients', [])
            
            row_index = active_cell.get('row')
            if row_index is not None and row_index < len(patients_data):
                selected_patient = patients_data[row_index]
                return json.dumps(selected_patient)
                
        except Exception as e:
            logger.error(f"Error handling patient selection: {e}")
            
        return ""

    @app.callback(
        [Output('patient-profile-content', 'children'),
         Output('patient-biomarker-chart', 'figure'),
         Output('patient-visit-history', 'children')],
        Input('selected-patient-store', 'children'),
        State('api-data-store', 'children')
    )
    def update_patient_profile_modal(selected_patient_json, api_data_json):
        """Update patient profile modal content."""
        if not selected_patient_json or not api_data_json:
            return "", go.Figure(), ""
            
        try:
            patient_data = json.loads(selected_patient_json)
            api_data = json.loads(api_data_json)
            
            # Get patient-specific data
            usubjid = patient_data.get('usubjid', '')
            labs_data = [lab for lab in api_data.get('labs', []) if lab.get('usubjid') == usubjid]
            visits_data = [visit for visit in api_data.get('visits', []) if visit.get('usubjid') == usubjid]
            
            # Create patient info card
            age = patient_data.get('age', 'N/A')
            sex = patient_data.get('sex', 'N/A')
            race = patient_data.get('race', 'N/A')
            enrollment_date = patient_data.get('date_of_enrollment', 'N/A')
            site_id = patient_data.get('site_id', 'N/A')
            
            patient_info = html.Div([
                html.H6(f"Patient: {usubjid}", className="text-primary mb-3"),
                html.Div([
                    html.Div([
                        html.Strong("Demographics"),
                        html.Ul([
                            html.Li(f"Age: {age}"),
                            html.Li(f"Sex: {sex}"),
                            html.Li(f"Race: {race}")
                        ])
                    ], className="col-md-4"),
                    html.Div([
                        html.Strong("Study Information"),
                        html.Ul([
                            html.Li(f"Site ID: {site_id}"),
                            html.Li(f"Enrollment: {enrollment_date}"),
                            html.Li(f"Total Visits: {len(visits_data)}")
                        ])
                    ], className="col-md-4"),
                    html.Div([
                        html.Strong("Lab Results"),
                        html.Ul([
                            html.Li(f"Total Lab Tests: {len(labs_data)}"),
                            html.Li(f"Unique Test Types: {len(set(lab.get('lbtestcd', '') for lab in labs_data))}"),
                            html.Li(f"Latest Test: {max((lab.get('visit_date', '1900-01-01') for lab in labs_data), default='N/A')}")
                        ])
                    ], className="col-md-4")
                ], className="row")
            ], className="alert alert-info")
            
            # Create biomarker chart
            biomarker_chart = create_patient_biomarker_chart(patient_data, labs_data, visits_data)
            
            # Create visit history
            visit_history = []
            if visits_data:
                sorted_visits = sorted(visits_data, key=lambda x: x.get('visit_date', ''), reverse=True)
                for visit in sorted_visits[:10]:  # Show last 10 visits
                    visit_history.append(
                        html.Div([
                            html.Strong(f"{visit.get('visit_name', 'Unknown Visit')} "),
                            html.Span(f"({visit.get('visit_date', 'No date')})", className="text-muted")
                        ], className="mb-1")
                    )
            else:
                visit_history = [html.P("No visit data available", className="text-muted")]
            
            return patient_info, biomarker_chart, html.Div(visit_history)
            
        except Exception as e:
            logger.error(f"Error updating patient profile: {e}")
            return "", go.Figure(), ""

    # Clientside callback to show patient modal when patient is selected
    app.clientside_callback(
        """
        function(selectedPatientJson) {
            if (selectedPatientJson) {
                var modal = new bootstrap.Modal(document.getElementById('patient-profile-modal'));
                modal.show();
                return 1;
            }
            return 0;
        }
        """,
        Output('selected-patient-store', 'data-trigger-modal'),
        Input('selected-patient-store', 'children')
    )

    # Phase 4: Field Detection Callback
    @app.callback(
        [Output('field-detection-results', 'children'),
         Output('field-detection-validation', 'children'),
         Output('field-detection-validation', 'style')],
        [Input('run-field-detection-btn', 'n_clicks')],
        [State('field-detection-confidence-slider', 'value'),
         State('api-data-store', 'children')]
    )
    def run_field_detection(n_clicks, confidence_threshold, api_data_json):
        """
        Run field detection analysis on current dataset.
        
        This implements Phase 4's statistical field detection system.
        """
        if n_clicks == 0:
            return html.Div(
                "Click 'Analyze Fields' to start automated field detection.",
                className="text-muted text-center p-4"
            ), html.Div(), {"display": "none"}
        
        try:
            # For demo purposes, use sample clinical data
            # In production, this would use actual dataset from api_data_json
            sample_data = create_sample_clinical_data()
            
            # Run field detection
            detection_results = detect_field_types(sample_data, confidence_threshold)
            
            if not detection_results:
                return html.Div([
                    html.Div([
                        html.I(className="fas fa-info-circle me-2 text-info"),
                        "No ambiguous fields detected with sufficient confidence.",
                    ], className="alert alert-info")
                ]), html.Div(), {"display": "none"}
            
            # Create results cards
            results_cards = []
            validation_components = []
            
            for idx, result in enumerate(detection_results):
                # Detection result card
                confidence_color = "success" if result.confidence >= 0.8 else "warning" if result.confidence >= 0.6 else "danger"
                
                card = html.Div([
                    html.Div([
                        html.H5([
                            html.Span(f"Field: {result.field_name}", className="me-2"),
                            html.Span(f"{result.confidence:.1%}", className=f"badge bg-{confidence_color}")
                        ], className="card-title"),
                        html.P(f"Predicted Type: {result.predicted_type.replace('_', ' ').title()}", 
                               className="card-text"),
                        
                        # Statistical Evidence
                        html.Div([
                            html.H6("Statistical Evidence:", className="mt-3"),
                            html.Ul([
                                html.Li(f"Sample size: {result.evidence.get('sample_size', 'N/A')}")
                            ] + [
                                html.Li(f"{field.replace('_', ' ').title()} correlation: {corr:.3f}")
                                for field, corr in result.correlations.items()
                            ])
                        ]),
                        
                        # Validation buttons
                        html.Div([
                            html.Button([
                                html.I(className="fas fa-check me-1"),
                                "Accept"
                            ], 
                            id={"type": "accept-detection", "index": idx}, 
                            className="btn btn-success btn-sm me-2"),
                            html.Button([
                                html.I(className="fas fa-times me-1"),
                                "Reject"
                            ], 
                            id={"type": "reject-detection", "index": idx}, 
                            className="btn btn-danger btn-sm me-2"),
                            html.Button([
                                html.I(className="fas fa-edit me-1"),
                                "Modify"
                            ], 
                            id={"type": "modify-detection", "index": idx}, 
                            className="btn btn-secondary btn-sm")
                        ], className="mt-3")
                    ], className="card-body")
                ], className="card mb-3")
                
                results_cards.append(card)
                
                # Add validation component (initially hidden)
                validation_comp = html.Div([
                    html.H6(f"Validation for {result.field_name}:"),
                    html.Div(id={"type": "validation-status", "index": idx})
                ], id={"type": "validation-component", "index": idx})
                validation_components.append(validation_comp)
            
            results_div = html.Div([
                html.H5([
                    html.I(className="fas fa-chart-bar me-2"),
                    f"Field Detection Results ({len(detection_results)} fields analyzed)"
                ], className="mb-3"),
                html.Div(results_cards)
            ])
            
            validation_div = html.Div([
                html.H5("Field Validation", className="mb-3"),
                html.Div(validation_components)
            ])
            
            return results_div, validation_div, {"display": "block"}
            
        except Exception as e:
            logger.error(f"Error in field detection: {e}")
            return html.Div([
                html.Div([
                    html.I(className="fas fa-exclamation-triangle me-2"),
                    f"Error in field detection: {str(e)}"
                ], className="alert alert-danger")
            ]), html.Div(), {"display": "none"}

    return app

# For development/testing purposes
if __name__ == "__main__":
    app = create_dash_app()
    app.run(debug=True, port=8050, host="0.0.0.0")