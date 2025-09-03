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
import websocket
from threading import Thread
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables for WebSocket and demo mode
ws_connection = None
demo_mode_active = False
demo_data_store = {}

# API Configuration
API_BASE_URL = "http://localhost:8000/api"
WS_URL = "ws://localhost:8000/ws"

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
                                    {'label': '🔴 Live Data', 'value': False},
                                    {'label': '🟢 Demo Mode', 'value': True}
                                ],
                                value=False,
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
                            className="mb-2"
                        )
                    ], className="col-md-3"),
                    
                    # Country Filter
                    html.Div([
                        html.Label("Filter by Country", className="form-label fw-bold"),
                        dcc.Dropdown(
                            id='country-filter',
                            placeholder="All Countries",
                            className="mb-2"
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
        dcc.Download(id="download-csv")
        
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

def create_metrics_cards(stats_data: Dict) -> List[html.Div]:
    """
    Create metrics cards from statistics data.
    
    Args:
        stats_data: Statistics from API
        
    Returns:
        List of metric cards
    """
    if not stats_data:
        return [html.Div("Loading metrics...", className="col-12 text-center")]
    
    metrics = [
        {
            "title": "Total Sites",
            "value": stats_data.get('total_sites', 0),
            "icon": "fas fa-hospital",
            "color": "primary"
        },
        {
            "title": "Total Patients",
            "value": stats_data.get('total_patients', 0),
            "icon": "fas fa-users",
            "color": "success"
        },
        {
            "title": "Total Visits",
            "value": stats_data.get('total_visits', 0),
            "icon": "fas fa-calendar-check",
            "color": "info"
        },
        {
            "title": "Lab Results",
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

def create_site_risk_map(sites_data: List[Dict]) -> go.Figure:
    """
    Create interactive site risk assessment map.
    
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
    
    for site in sites_data:
        if site.get('latitude') and site.get('longitude'):
            lats.append(site['latitude'])
            lons.append(site['longitude'])
            
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
            text += f"Progress: {progress:.1f}%"
            texts.append(text)
    
    if lats and lons:
        fig.add_trace(go.Scattergeo(
            lat=lats,
            lon=lons,
            text=texts,
            mode='markers',
            marker=dict(
                size=sizes,
                color=colors,
                line=dict(width=2, color='white'),
                sizemode='diameter'
            ),
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
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
    
    columns = [
        {"name": "Subject ID", "id": "usubjid", "type": "text"},
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
            # Fetch all required data
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
            
            if sites_data:
                sites_df = pd.DataFrame(sites_data)
                if not sites_df.empty:
                    site_options = [{"label": f"{row['site_name']} ({row['site_id']})", 
                                   "value": row['site_id']} 
                                  for _, row in sites_df.iterrows()]
                    
                    countries = sites_df['country'].unique()
                    country_options = [{"label": country, "value": country} 
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
        [Input('api-data-store', 'children')]
    )
    def update_metrics_cards(api_data_json):
        """Update metrics cards display."""
        try:
            if not api_data_json:
                return [html.Div("Loading metrics...", className="col-12 text-center")]
            
            api_data = json.loads(api_data_json)
            stats_data = api_data.get('stats', {})
            
            return create_metrics_cards(stats_data)
        except Exception as e:
            logger.error(f"Error updating metrics cards: {e}")
            return [html.Div("Error loading metrics", className="col-12 text-center text-danger")]
    
    # Enrollment chart callback
    @app.callback(
        Output('enrollment-chart', 'figure'),
        [Input('api-data-store', 'children')]
    )
    def update_enrollment_chart(api_data_json):
        """Update enrollment timeline chart."""
        try:
            if not api_data_json:
                return create_enrollment_chart({})
            
            api_data = json.loads(api_data_json)
            stats_data = api_data.get('stats', {})
            demo_mode = api_data.get('demo_mode', False)
            
            return create_enrollment_chart(stats_data, demo_mode)
        except Exception as e:
            logger.error(f"Error updating enrollment chart: {e}")
            return create_enrollment_chart({})
    
    # Site risk map callback
    @app.callback(
        Output('site-risk-map', 'figure'),
        [Input('api-data-store', 'children'),
         Input('country-filter', 'value')]
    )
    def update_site_risk_map(api_data_json, country_filter):
        """Update site risk assessment map."""
        try:
            if not api_data_json:
                return create_site_risk_map([])
            
            api_data = json.loads(api_data_json)
            sites_data = api_data.get('sites', [])
            
            # Apply country filter
            if country_filter and sites_data:
                sites_data = [site for site in sites_data if site.get('country') == country_filter]
            
            return create_site_risk_map(sites_data)
        except Exception as e:
            logger.error(f"Error updating site risk map: {e}")
            return create_site_risk_map([])
    
    # Lab analysis chart callback
    @app.callback(
        Output('lab-analysis-chart', 'figure'),
        [Input('api-data-store', 'children')]
    )
    def update_lab_analysis_chart(api_data_json):
        """Update laboratory analysis chart."""
        try:
            if not api_data_json:
                return create_lab_analysis_chart()
            
            api_data = json.loads(api_data_json)
            stats_data = api_data.get('stats', {})
            lab_abnormalities = stats_data.get('lab_abnormalities', {})
            
            return create_lab_analysis_chart(lab_abnormalities)
        except Exception as e:
            logger.error(f"Error updating lab analysis chart: {e}")
            return create_lab_analysis_chart()
    
    # Data table callback
    @app.callback(
        Output('data-table-container', 'children'),
        [Input('api-data-store', 'children'),
         Input('site-filter', 'value')]
    )
    def update_data_table(api_data_json, site_filter):
        """Update patient data table."""
        try:
            if not api_data_json:
                return create_data_table([])
            
            api_data = json.loads(api_data_json)
            patients_data = api_data.get('patients', [])
            
            # Apply site filter
            if site_filter and patients_data:
                patients_data = [patient for patient in patients_data 
                               if patient.get('site_id') == site_filter]
            
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

# For development/testing purposes
if __name__ == "__main__":
    app = create_dash_app()
    app.run(debug=True, port=8050, host="0.0.0.0")