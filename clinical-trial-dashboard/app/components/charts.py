"""
Chart Components for DCRI Clinical Trial Dashboard

Specialized chart creation functions for clinical trial data visualization.
Includes enrollment charts, risk maps, and laboratory analysis visualizations.
"""

import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import numpy as np

def create_advanced_enrollment_chart(stats_data: Dict, demo_mode: bool = False) -> go.Figure:
    """
    Create an advanced enrollment timeline chart with projections and targets.
    
    Args:
        stats_data: Statistics data from API
        demo_mode: Whether demo mode is active
        
    Returns:
        go.Figure: Advanced Plotly enrollment chart
    """
    fig = go.Figure()
    
    # Get enrollment timeline data
    timeline_data = stats_data.get('enrollment_timeline', [])
    
    if not timeline_data or len(timeline_data) == 0:
        # Create realistic sample data for demonstration
        start_date = datetime(2024, 1, 1)
        dates = [start_date + timedelta(days=30*i) for i in range(12)]
        enrollments = [8, 15, 22, 35, 48, 65, 78, 95, 110, 128, 145, 162]
        cumulative = np.cumsum(enrollments).tolist()
        
        # Add actual enrollment line
        fig.add_trace(go.Scatter(
            x=dates,
            y=cumulative,
            mode='lines+markers',
            name='Actual Enrollment',
            line=dict(color='#007cba', width=3),
            marker=dict(size=8, color='#007cba'),
            hovertemplate='<b>%{x}</b><br>Total Patients: %{y}<br><extra></extra>'
        ))
        
        # Add target projection
        target_total = 200
        target_dates = dates + [dates[-1] + timedelta(days=30*i) for i in range(1, 4)]
        target_values = cumulative + [target_total * (i/3) for i in range(1, 4)]
        
        fig.add_trace(go.Scatter(
            x=target_dates,
            y=target_values,
            mode='lines',
            name='Target Projection',
            line=dict(color='#28a745', width=2, dash='dash'),
            hovertemplate='<b>%{x}</b><br>Target: %{y}<br><extra></extra>'
        ))
        
    else:
        # Process real data
        df = pd.DataFrame(timeline_data)
        df['month'] = pd.to_datetime(df['month'], errors='coerce')
        df = df.dropna().sort_values('month')
        df['cumulative'] = df['enrollments'].cumsum()
        
        # Actual enrollment
        fig.add_trace(go.Scatter(
            x=df['month'],
            y=df['cumulative'],
            mode='lines+markers',
            name='Actual Enrollment',
            line=dict(color='#007cba', width=3),
            marker=dict(size=8, color='#007cba'),
            hovertemplate='<b>%{x}</b><br>Total: %{y}<br>Monthly: %{text}<extra></extra>',
            text=df['enrollments']
        ))
    
    # Add enrollment rate indicator
    if demo_mode:
        fig.add_annotation(
            x=0.02, y=0.98,
            xref="paper", yref="paper",
            text="🟢 DEMO MODE",
            showarrow=False,
            font=dict(size=12, color="white"),
            bgcolor="green",
            bordercolor="white",
            borderwidth=1
        )
    
    fig.update_layout(
        title={
            'text': "Patient Enrollment Timeline & Projections",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        xaxis_title="Date",
        yaxis_title="Cumulative Patients",
        hovermode='x unified',
        template="plotly_white",
        height=400,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
    )
    
    return fig

def create_interactive_site_map(sites_data: List[Dict], selected_country: str = None) -> go.Figure:
    """
    Create an interactive geographic map showing site performance and risk levels.
    
    Args:
        sites_data: Sites data from API
        selected_country: Optional country filter
        
    Returns:
        go.Figure: Interactive site risk map
    """
    fig = go.Figure()
    
    if not sites_data:
        # Create sample data with realistic clinical trial sites
        sample_sites = [
            {"site_name": "Duke Clinical Research Institute", "country": "USA", "latitude": 36.0014, "longitude": -78.9382, 
             "current_enrollment": 85, "enrollment_target": 100, "site_id": "SITE001"},
            {"site_name": "Johns Hopkins Hospital", "country": "USA", "latitude": 39.2904, "longitude": -76.6122, 
             "current_enrollment": 92, "enrollment_target": 100, "site_id": "SITE002"},
            {"site_name": "Mayo Clinic Rochester", "country": "USA", "latitude": 44.0225, "longitude": -92.4699, 
             "current_enrollment": 78, "enrollment_target": 100, "site_id": "SITE003"},
            {"site_name": "Toronto General Hospital", "country": "CAN", "latitude": 43.6532, "longitude": -79.3832, 
             "current_enrollment": 65, "enrollment_target": 80, "site_id": "SITE004"},
            {"site_name": "London Health Sciences", "country": "CAN", "latitude": 43.0389, "longitude": -81.2739, 
             "current_enrollment": 55, "enrollment_target": 90, "site_id": "SITE005"},
            {"site_name": "Royal London Hospital", "country": "GBR", "latitude": 51.5074, "longitude": -0.1278, 
             "current_enrollment": 45, "enrollment_target": 90, "site_id": "SITE006"},
            {"site_name": "Charité Berlin", "country": "DEU", "latitude": 52.5200, "longitude": 13.4050, 
             "current_enrollment": 67, "enrollment_target": 85, "site_id": "SITE007"},
            {"site_name": "Hospital Universitario Madrid", "country": "ESP", "latitude": 40.4168, "longitude": -3.7038, 
             "current_enrollment": 38, "enrollment_target": 75, "site_id": "SITE008"}
        ]
        sites_data = sample_sites
    
    # Filter by country if specified
    if selected_country:
        sites_data = [site for site in sites_data if site.get('country') == selected_country]
    
    # Process sites data for visualization
    lats, lons, texts, colors, sizes = [], [], [], [], []
    
    for site in sites_data:
        if site.get('latitude') and site.get('longitude'):
            lats.append(site['latitude'])
            lons.append(site['longitude'])
            
            current = site.get('current_enrollment', 0)
            target = site.get('enrollment_target', 100)
            progress = (current / target * 100) if target > 0 else 0
            
            # Risk-based color coding
            if progress >= 90:
                color = '#28a745'  # Green - excellent performance
                risk_level = "Low Risk"
            elif progress >= 70:
                color = '#ffc107'  # Yellow - good performance
                risk_level = "Medium Risk"
            elif progress >= 50:
                color = '#fd7e14'  # Orange - concerning
                risk_level = "High Risk"
            else:
                color = '#dc3545'  # Red - critical risk
                risk_level = "Critical Risk"
            
            colors.append(color)
            sizes.append(max(12, min(35, current / 2.5)))  # Scale size by enrollment
            
            # Rich hover text
            text = f"<b>{site.get('site_name', 'Unknown Site')}</b><br>"
            text += f"Site ID: {site.get('site_id', 'N/A')}<br>"
            text += f"Country: {site.get('country', 'N/A')}<br>"
            text += f"Enrolled: {current}/{target} patients<br>"
            text += f"Progress: {progress:.1f}%<br>"
            text += f"Risk Level: {risk_level}"
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
                sizemode='diameter',
                opacity=0.8
            ),
            hovertemplate='%{text}<extra></extra>',
            showlegend=False
        ))
    
    # Add legend for risk levels
    risk_colors = ['#28a745', '#ffc107', '#fd7e14', '#dc3545']
    risk_labels = ['Low Risk (≥90%)', 'Medium Risk (70-89%)', 'High Risk (50-69%)', 'Critical Risk (<50%)']
    
    for i, (color, label) in enumerate(zip(risk_colors, risk_labels)):
        fig.add_trace(go.Scatter(
            x=[None], y=[None],
            mode='markers',
            marker=dict(color=color, size=10),
            name=label,
            showlegend=True
        ))
    
    fig.update_layout(
        title={
            'text': "Global Site Risk Assessment Map",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        geo=dict(
            showframe=False,
            showcoastlines=True,
            showland=True,
            landcolor="rgb(243, 243, 243)",
            coastlinecolor="rgb(204, 204, 204)",
            projection_type='natural earth'
        ),
        height=450,
        margin=dict(l=0, r=0, t=50, b=0),
        legend=dict(
            orientation="v",
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)"
        )
    )
    
    return fig

def create_lab_distribution_analysis(lab_data: Dict) -> go.Figure:
    """
    Create comprehensive laboratory results analysis with multiple chart types.
    
    Args:
        lab_data: Laboratory abnormalities data
        
    Returns:
        go.Figure: Comprehensive lab analysis figure
    """
    fig = go.Figure()
    
    # Default lab data if none provided
    if not lab_data:
        lab_data = {
            'NORMAL': 1234,
            'HIGH': 145,
            'LOW': 89,
            'ABNORMAL': 67,
            'CRITICAL': 12
        }
    
    # Create donut chart
    labels = list(lab_data.keys())
    values = list(lab_data.values())
    
    # Define colors for different categories
    color_map = {
        'NORMAL': '#28a745',
        'HIGH': '#ffc107',
        'LOW': '#17a2b8',
        'ABNORMAL': '#fd7e14',
        'CRITICAL': '#dc3545'
    }
    
    colors = [color_map.get(label, '#6c757d') for label in labels]
    
    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(
            colors=colors, 
            line=dict(color='white', width=2)
        ),
        hovertemplate='<b>%{label}</b><br>' +
                     'Count: %{value}<br>' +
                     'Percentage: %{percent}<br>' +
                     '<extra></extra>',
        textinfo='label+percent',
        textposition='outside'
    ))
    
    # Add center text showing total
    total_labs = sum(values)
    fig.add_annotation(
        text=f"Total<br>{total_labs:,}",
        x=0.5, y=0.5,
        font_size=16,
        showarrow=False
    )
    
    fig.update_layout(
        title={
            'text': "Laboratory Results Distribution",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 16}
        },
        showlegend=True,
        legend=dict(
            orientation="h", 
            yanchor="bottom", 
            y=-0.2,
            xanchor="center",
            x=0.5
        ),
        height=450,
        margin=dict(l=20, r=20, t=60, b=100)
    )
    
    return fig

def create_enrollment_velocity_chart(stats_data: Dict) -> go.Figure:
    """
    Create enrollment velocity analysis showing enrollment rate trends.
    
    Args:
        stats_data: Statistics data from API
        
    Returns:
        go.Figure: Enrollment velocity chart
    """
    fig = go.Figure()
    
    # Sample velocity data
    months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    enrollments_per_month = [8, 15, 22, 35, 48, 65, 78, 95, 110, 128, 145, 162]
    velocity = [0] + [enrollments_per_month[i] - enrollments_per_month[i-1] for i in range(1, len(enrollments_per_month))]
    
    # Bar chart for monthly enrollments
    fig.add_trace(go.Bar(
        x=months,
        y=enrollments_per_month,
        name='Monthly Enrollments',
        marker_color='#007cba',
        opacity=0.7,
        yaxis='y1'
    ))
    
    # Line chart for velocity
    fig.add_trace(go.Scatter(
        x=months,
        y=velocity,
        mode='lines+markers',
        name='Enrollment Velocity',
        line=dict(color='#dc3545', width=3),
        marker=dict(size=8),
        yaxis='y2'
    ))
    
    fig.update_layout(
        title={
            'text': "Enrollment Velocity Analysis",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Month",
        yaxis=dict(
            title="Monthly Enrollments",
            side="left"
        ),
        yaxis2=dict(
            title="Velocity (Change)",
            side="right",
            overlaying="y"
        ),
        hovermode='x unified',
        template="plotly_white",
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2)
    )
    
    return fig