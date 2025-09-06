"""
Data Dictionary Dashboard Integration - Phase 5
Dashboard components for generic data dictionary management

Provides interactive interface for dictionary upload, parsing, validation,
and field mapping with the existing dashboard.
"""

from dash import html, dcc, dash_table, callback, Input, Output, State, ALL
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import Dict, List, Any, Optional
import base64
import io
import json
import logging
from pathlib import Path

from .data_dictionary import (
    GenericDictionaryParser, DataDictionary, FieldDefinition, FieldType,
    IntelligentFieldMapper, generate_mock_data_dictionary
)
from .data_normalization import DataNormalizer, DataQualityReport

logger = logging.getLogger(__name__)

class DictionaryDashboard:
    """Dashboard components for data dictionary management"""
    
    def __init__(self):
        self.parser = GenericDictionaryParser()
        self.mapper = IntelligentFieldMapper()
        self.normalizer = DataNormalizer()
        self.current_dictionary = None
        self.current_mappings = None
    
    def create_dictionary_upload_section(self) -> html.Div:
        """Create the dictionary upload and management section"""
        return html.Div([
            html.H3([
                html.I(className="fas fa-file-import me-2"),
                "Data Dictionary Management"
            ], className="mb-3"),
            
            html.P([
                "Upload your data dictionary in CSV, JSON, XML, or YAML format. ",
                "The system will automatically detect the format and parse field definitions."
            ], className="text-muted mb-4"),
            
            # Upload area
            html.Div([
                html.Div([
                    dcc.Upload(
                        id='dictionary-upload',
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-3x mb-3", style={"color": "#6c757d"}),
                            html.H5("Drag and Drop or Click to Upload", className="mb-2"),
                            html.P("Supported formats: CSV, JSON, XML, YAML", className="text-muted")
                        ], className="text-center py-4"),
                        style={
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '10px',
                            'borderColor': '#dee2e6',
                            'backgroundColor': '#f8f9fa',
                            'cursor': 'pointer'
                        },
                        multiple=False
                    )
                ], className="col-md-8"),
                
                # Quick actions
                html.Div([
                    html.H6("Quick Start", className="mb-3"),
                    html.Button([
                        html.I(className="fas fa-magic me-2"),
                        "Generate Sample CSV"
                    ], id="generate-sample-csv-btn", className="btn btn-outline-primary btn-sm mb-2 w-100"),
                    
                    html.Button([
                        html.I(className="fas fa-cog me-2"),
                        "Generate Sample JSON"
                    ], id="generate-sample-json-btn", className="btn btn-outline-info btn-sm mb-2 w-100"),
                    
                    html.Button([
                        html.I(className="fas fa-question-circle me-2"),
                        "View Examples"
                    ], id="show-examples-btn", className="btn btn-outline-secondary btn-sm w-100"),
                ], className="col-md-4")
            ], className="row mb-4"),
            
            # Upload status and results
            html.Div(id="dictionary-upload-status"),
            html.Div(id="dictionary-info-display"),
            
            # Field mapping section
            html.Div(id="field-mapping-section", style={"display": "none"}),
            
            # Data validation section
            html.Div(id="data-validation-section", style={"display": "none"}),
            
        ], className="card-body")
    
    def create_field_mapping_display(self, dictionary: DataDictionary, mappings: Dict[str, List]) -> html.Div:
        """Create interactive field mapping display"""
        return html.Div([
            html.Hr(className="my-4"),
            html.H4([
                html.I(className="fas fa-exchange-alt me-2"),
                "Intelligent Field Mapping"
            ], className="mb-3"),
            
            html.P([
                f"Found {len(dictionary.fields)} fields in your dictionary. ",
                "Below are suggested mappings to standard clinical field types."
            ], className="text-muted mb-4"),
            
            # Mapping confidence summary
            html.Div([
                html.Div([
                    html.Div([
                        html.H5(f"{len([f for f in dictionary.fields.values() if f.confidence_score > 0.8])}", className="mb-0 text-success"),
                        html.P("High Confidence", className="text-muted mb-0 small")
                    ], className="text-center")
                ], className="col-md-3"),
                html.Div([
                    html.Div([
                        html.H5(f"{len([f for f in dictionary.fields.values() if 0.5 < f.confidence_score <= 0.8])}", className="mb-0 text-warning"),
                        html.P("Medium Confidence", className="text-muted mb-0 small")
                    ], className="text-center")
                ], className="col-md-3"),
                html.Div([
                    html.Div([
                        html.H5(f"{len([f for f in dictionary.fields.values() if f.confidence_score <= 0.5])}", className="mb-0 text-danger"),
                        html.P("Low Confidence", className="text-muted mb-0 small")
                    ], className="text-center")
                ], className="col-md-3"),
                html.Div([
                    html.Div([
                        html.H5(f"{len(dictionary.fields)}", className="mb-0 text-info"),
                        html.P("Total Fields", className="text-muted mb-0 small")
                    ], className="text-center")
                ], className="col-md-3"),
            ], className="row mb-4 text-center"),
            
            # Field details table
            html.Div([
                self._create_field_mapping_table(dictionary, mappings)
            ]),
            
            # Action buttons
            html.Div([
                html.Button([
                    html.I(className="fas fa-check me-2"),
                    "Apply Mappings"
                ], id="apply-mappings-btn", className="btn btn-success me-2"),
                
                html.Button([
                    html.I(className="fas fa-download me-2"),
                    "Export Mappings"
                ], id="export-mappings-btn", className="btn btn-outline-primary me-2"),
                
                html.Button([
                    html.I(className="fas fa-upload me-2"),
                    "Load Custom Mappings"
                ], id="load-mappings-btn", className="btn btn-outline-secondary"),
            ], className="mt-4"),
            
        ], id="field-mapping-section", style={"display": "block"})
    
    def _create_field_mapping_table(self, dictionary: DataDictionary, mappings: Dict[str, List]) -> dash_table.DataTable:
        """Create interactive field mapping table"""
        # Prepare data for table
        table_data = []
        
        for field_name, field_def in dictionary.fields.items():
            # Find best mapping suggestion
            best_mapping = ""
            mapping_score = 0.0
            
            for std_field, candidates in mappings.items():
                for candidate_name, score in candidates:
                    if candidate_name == field_name and score > mapping_score:
                        best_mapping = std_field
                        mapping_score = score
            
            # Confidence indicator
            if field_def.confidence_score > 0.8:
                confidence_icon = "🟢"
            elif field_def.confidence_score > 0.5:
                confidence_icon = "🟡"
            else:
                confidence_icon = "🔴"
            
            # Field type icon
            type_icons = {
                FieldType.TEXT: "📝", FieldType.INTEGER: "🔢", FieldType.DECIMAL: "🔢",
                FieldType.DATE: "📅", FieldType.CATEGORICAL: "📋", FieldType.BINARY: "✅",
                FieldType.BOOLEAN: "✅", FieldType.EMAIL: "📧", FieldType.PHONE: "📞",
                FieldType.IDENTIFIER: "🆔", FieldType.UNKNOWN: "❓"
            }
            type_icon = type_icons.get(field_def.field_type, "❓")
            
            table_data.append({
                'confidence': confidence_icon,
                'field_name': field_name,
                'field_label': field_def.label or field_name,
                'field_type': f"{type_icon} {field_def.field_type.value}",
                'suggested_mapping': best_mapping,
                'mapping_score': f"{mapping_score:.1%}" if mapping_score > 0 else "",
                'description': field_def.description[:100] + "..." if len(field_def.description) > 100 else field_def.description,
                'choices': len(field_def.choices) if field_def.choices else 0,
                'required': "✅" if field_def.required else "",
            })
        
        return dash_table.DataTable(
            id='field-mapping-table',
            data=table_data,
            columns=[
                {'name': '', 'id': 'confidence', 'presentation': 'markdown'},
                {'name': 'Field Name', 'id': 'field_name'},
                {'name': 'Label', 'id': 'field_label'},
                {'name': 'Type', 'id': 'field_type'},
                {'name': 'Suggested Mapping', 'id': 'suggested_mapping', 'editable': True, 'presentation': 'dropdown'},
                {'name': 'Score', 'id': 'mapping_score'},
                {'name': 'Description', 'id': 'description'},
                {'name': 'Choices', 'id': 'choices', 'type': 'numeric'},
                {'name': 'Req', 'id': 'required'},
            ],
            editable=True,
            sort_action="native",
            filter_action="native",
            page_size=15,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'fontSize': '14px',
                'padding': '8px',
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'filter_query': '{confidence} = 🟢'},
                    'backgroundColor': '#d4edda',
                },
                {
                    'if': {'filter_query': '{confidence} = 🟡'},
                    'backgroundColor': '#fff3cd',
                },
                {
                    'if': {'filter_query': '{confidence} = 🔴'},
                    'backgroundColor': '#f8d7da',
                },
            ]
        )
    
    def create_data_validation_display(self, report: DataQualityReport) -> html.Div:
        """Create data validation results display"""
        severity_counts = {}
        for issue in report.issues:
            severity = issue.severity.value
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        return html.Div([
            html.Hr(className="my-4"),
            html.H4([
                html.I(className="fas fa-clipboard-check me-2"),
                "Data Quality Validation"
            ], className="mb-3"),
            
            # Quality scores
            html.Div([
                html.Div([
                    html.Div([
                        html.H5(f"{report.overall_score:.1%}", className="mb-0 text-primary"),
                        html.P("Overall Quality", className="text-muted mb-0 small")
                    ], className="text-center")
                ], className="col-md-3"),
                html.Div([
                    html.Div([
                        html.H5(f"{report.completeness_score:.1%}", className="mb-0 text-success"),
                        html.P("Completeness", className="text-muted mb-0 small")
                    ], className="text-center")
                ], className="col-md-3"),
                html.Div([
                    html.Div([
                        html.H5(f"{report.consistency_score:.1%}", className="mb-0 text-info"),
                        html.P("Consistency", className="text-muted mb-0 small")
                    ], className="text-center")
                ], className="col-md-3"),
                html.Div([
                    html.Div([
                        html.H5(f"{report.validity_score:.1%}", className="mb-0 text-warning"),
                        html.P("Validity", className="text-muted mb-0 small")
                    ], className="text-center")
                ], className="col-md-3"),
            ], className="row mb-4 text-center"),
            
            # Issue summary
            if report.issues:
                html.Div([
                    html.H5("Validation Issues Found", className="mb-3"),
                    html.Div([
                        html.Span(f"Critical: {severity_counts.get('critical', 0)}", className="badge bg-danger me-2"),
                        html.Span(f"Errors: {severity_counts.get('error', 0)}", className="badge bg-warning me-2"),
                        html.Span(f"Warnings: {severity_counts.get('warning', 0)}", className="badge bg-info me-2"),
                        html.Span(f"Info: {severity_counts.get('info', 0)}", className="badge bg-secondary"),
                    ], className="mb-3"),
                    
                    # Issues table
                    self._create_issues_table(report.issues[:50])  # Show first 50 issues
                ])
            else:
                html.Div([
                    html.I(className="fas fa-check-circle fa-3x text-success mb-3"),
                    html.H5("No Issues Found!", className="text-success"),
                    html.P("Your data passed all validation checks.", className="text-muted")
                ], className="text-center py-4"),
            
            # Field statistics charts
            html.Div([
                html.H5("Field Statistics", className="mb-3"),
                html.Div(id="field-stats-charts")
            ]) if report.field_stats else html.Div(),
            
        ], id="data-validation-section", style={"display": "block"})
    
    def _create_issues_table(self, issues: List) -> dash_table.DataTable:
        """Create issues summary table"""
        table_data = []
        
        for i, issue in enumerate(issues):
            severity_icons = {
                'critical': '🔥', 'error': '❌', 'warning': '⚠️', 'info': 'ℹ️'
            }
            
            table_data.append({
                'severity': f"{severity_icons.get(issue.severity.value, '')} {issue.severity.value.title()}",
                'field': issue.field,
                'message': issue.message,
                'value': str(issue.value)[:50] + "..." if issue.value and len(str(issue.value)) > 50 else str(issue.value),
                'row': issue.row_index if issue.row_index is not None else "",
                'suggestion': issue.suggestion or ""
            })
        
        return dash_table.DataTable(
            data=table_data,
            columns=[
                {'name': 'Severity', 'id': 'severity'},
                {'name': 'Field', 'id': 'field'},
                {'name': 'Message', 'id': 'message'},
                {'name': 'Value', 'id': 'value'},
                {'name': 'Row', 'id': 'row', 'type': 'numeric'},
                {'name': 'Suggestion', 'id': 'suggestion'},
            ],
            sort_action="native",
            filter_action="native",
            page_size=10,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'fontSize': '12px',
                'padding': '6px',
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold',
                'fontSize': '12px'
            }
        )
    
    def create_field_stats_charts(self, field_stats: Dict[str, Dict]) -> html.Div:
        """Create field statistics visualization charts"""
        charts = []
        
        # Completeness chart
        field_names = list(field_stats.keys())
        completeness_scores = [stats.get('completeness', 0) for stats in field_stats.values()]
        
        completeness_fig = px.bar(
            x=field_names,
            y=completeness_scores,
            title="Field Completeness Scores",
            labels={'x': 'Field', 'y': 'Completeness'},
            color=completeness_scores,
            color_continuous_scale='RdYlGn'
        )
        completeness_fig.update_layout(height=400, showlegend=False)
        
        charts.append(
            html.Div([
                dcc.Graph(figure=completeness_fig)
            ], className="col-md-6")
        )
        
        # Unique values distribution for categorical fields
        categorical_fields = []
        unique_counts = []
        
        for field_name, stats in field_stats.items():
            if 'value_distribution' in stats:
                categorical_fields.append(field_name)
                unique_counts.append(stats['unique_count'])
        
        if categorical_fields:
            unique_fig = px.bar(
                x=categorical_fields,
                y=unique_counts,
                title="Categorical Fields - Unique Value Counts",
                labels={'x': 'Field', 'y': 'Unique Values'}
            )
            unique_fig.update_layout(height=400)
            
            charts.append(
                html.Div([
                    dcc.Graph(figure=unique_fig)
                ], className="col-md-6")
            )
        
        return html.Div(charts, className="row")

def register_dictionary_callbacks(app):
    """Register all data dictionary dashboard callbacks"""
    dashboard = DictionaryDashboard()
    
    @app.callback(
        Output('dictionary-upload-status', 'children'),
        Output('dictionary-info-display', 'children'),
        Input('dictionary-upload', 'contents'),
        State('dictionary-upload', 'filename'),
        prevent_initial_call=True
    )
    def handle_dictionary_upload(contents, filename):
        if contents is None:
            return "", ""
        
        try:
            # Decode uploaded file
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            
            # Save to temporary file
            temp_file = f"/tmp/{filename}"
            with open(temp_file, 'wb') as f:
                f.write(decoded)
            
            # Parse dictionary
            dictionary = dashboard.parser.parse_dictionary(temp_file)
            dashboard.current_dictionary = dictionary
            
            # Generate field mappings
            mappings = dashboard.mapper.map_fields_to_standard(dictionary)
            dashboard.current_mappings = mappings
            
            # Success status
            status = html.Div([
                html.I(className="fas fa-check-circle text-success me-2"),
                f"Successfully parsed {filename} - Found {len(dictionary.fields)} fields"
            ], className="alert alert-success")
            
            # Dictionary info display
            info_display = html.Div([
                html.H5(f"Dictionary: {dictionary.name or filename}", className="mb-3"),
                html.Div([
                    html.Div([
                        html.Strong("Format: "), dictionary.source_format
                    ], className="col-md-3"),
                    html.Div([
                        html.Strong("Fields: "), str(len(dictionary.fields))
                    ], className="col-md-3"),
                    html.Div([
                        html.Strong("Version: "), dictionary.version or "N/A"
                    ], className="col-md-3"),
                    html.Div([
                        html.Strong("Metadata: "), str(len(dictionary.metadata)) + " items"
                    ], className="col-md-3"),
                ], className="row mb-3"),
                
                # Show field mapping
                dashboard.create_field_mapping_display(dictionary, mappings)
            ])
            
            # Clean up temp file
            Path(temp_file).unlink(missing_ok=True)
            
            return status, info_display
            
        except Exception as e:
            logger.error(f"Dictionary upload error: {e}")
            error_status = html.Div([
                html.I(className="fas fa-exclamation-triangle text-danger me-2"),
                f"Error parsing {filename}: {str(e)}"
            ], className="alert alert-danger")
            
            return error_status, ""
    
    @app.callback(
        Output('dictionary-upload', 'contents'),
        Output('dictionary-upload-status', 'children'),
        Input('generate-sample-csv-btn', 'n_clicks'),
        Input('generate-sample-json-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def generate_sample_files(csv_clicks, json_clicks):
        from dash import ctx
        
        if not ctx.triggered:
            return None, ""
        
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        try:
            if button_id == 'generate-sample-csv-btn':
                # Generate CSV sample
                temp_file = generate_mock_data_dictionary("csv", 15)
                with open(temp_file, 'r') as f:
                    content = f.read()
                
                # Encode for upload
                encoded = base64.b64encode(content.encode()).decode()
                contents = f"data:text/csv;base64,{encoded}"
                
                status = html.Div([
                    html.I(className="fas fa-info-circle text-info me-2"),
                    "Generated sample CSV dictionary with 15 fields"
                ], className="alert alert-info")
                
                Path(temp_file).unlink()
                return contents, status
                
            elif button_id == 'generate-sample-json-btn':
                # Generate JSON sample
                temp_file = generate_mock_data_dictionary("json", 15)
                with open(temp_file, 'r') as f:
                    content = f.read()
                
                # Encode for upload
                encoded = base64.b64encode(content.encode()).decode()
                contents = f"data:application/json;base64,{encoded}"
                
                status = html.Div([
                    html.I(className="fas fa-info-circle text-info me-2"),
                    "Generated sample JSON dictionary with 15 fields"
                ], className="alert alert-info")
                
                Path(temp_file).unlink()
                return contents, status
            
        except Exception as e:
            error_status = html.Div([
                html.I(className="fas fa-exclamation-triangle text-danger me-2"),
                f"Error generating sample: {str(e)}"
            ], className="alert alert-danger")
            return None, error_status
        
        return None, ""

# Export the dashboard creation function
def create_phase5_dashboard_section() -> html.Div:
    """Create the Phase 5 data dictionary dashboard section"""
    dashboard = DictionaryDashboard()
    
    return html.Div([
        html.Div([
            dashboard.create_dictionary_upload_section()
        ], className="card mb-4")
    ])