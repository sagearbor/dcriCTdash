"""
Phase 6: Clinical Formats Dashboard Integration
Dashboard components for REDCap, OMOP CDM, and FHIR data management
"""

import dash
from dash import html, dcc, dash_table, Input, Output, State, callback, ctx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Optional, Union, Any
import json
from datetime import datetime
import base64
import io

from .clinical_formats import ClinicalFormatIntegrator, REDCapParser, OMOPParser, FHIRParser
from .data_dictionary import DataDictionary


class ClinicalFormatsDashboard:
    """Dashboard integration for clinical data formats"""
    
    def __init__(self):
        self.integrator = ClinicalFormatIntegrator()
        self.current_dictionary = None
        self.current_format = None
        
    def create_clinical_formats_layout(self) -> html.Div:
        """Create the main clinical formats management layout"""
        return html.Div([
            # Header
            html.Div([
                html.H3("Clinical Data Formats Manager", className="text-primary mb-3"),
                html.P("Import and manage REDCap, OMOP CDM, and FHIR data dictionaries", 
                       className="text-muted mb-4")
            ]),
            
            # Format Selection and Upload
            html.Div([
                html.H4("Import Clinical Dictionary", className="mb-3"),
                
                # Format selection
                html.Div([
                    html.Label("Data Format:", className="form-label"),
                    dcc.Dropdown(
                        id='clinical-format-selector',
                        options=[
                            {'label': '🏥 REDCap Data Dictionary', 'value': 'redcap'},
                            {'label': '🔬 OMOP Common Data Model', 'value': 'omop'},
                            {'label': '🔄 FHIR Bundle/Resources', 'value': 'fhir'},
                            {'label': '📋 Generic CSV/JSON', 'value': 'generic'},
                            {'label': '🔍 Auto-Detect Format', 'value': 'auto'}
                        ],
                        value='auto',
                        className="mb-3"
                    )
                ], className="col-md-6"),
                
                # File upload
                html.Div([
                    html.Label("Upload Dictionary File:", className="form-label"),
                    dcc.Upload(
                        id='clinical-dictionary-upload',
                        children=html.Div([
                            html.I(className="fas fa-cloud-upload-alt fa-2x mb-2"),
                            html.P("Drag and Drop or Click to Upload", className="mb-1"),
                            html.Small("Supports CSV, JSON, XML formats", className="text-muted")
                        ]),
                        className="upload-area text-center p-4 border border-dashed rounded",
                        multiple=False
                    )
                ], className="col-md-6")
            ], className="row mb-4"),
            
            # Dictionary Summary
            html.Div(id='clinical-dictionary-summary', className="mb-4"),
            
            # Tabs for different views
            dcc.Tabs(
                id='clinical-formats-tabs',
                value='dictionary-view',
                children=[
                    dcc.Tab(label='📋 Dictionary Overview', value='dictionary-view'),
                    dcc.Tab(label='🔍 Field Analysis', value='field-analysis'),
                    dcc.Tab(label='📊 Mock Data Preview', value='mock-data'),
                    dcc.Tab(label='🔄 Format Conversion', value='format-conversion'),
                    dcc.Tab(label='📈 Clinical Insights', value='clinical-insights')
                ]
            ),
            
            # Tab content
            html.Div(id='clinical-formats-tab-content', className="mt-3"),
            
            # Hidden storage components
            dcc.Store(id='clinical-dictionary-store'),
            dcc.Store(id='clinical-format-store'),
            dcc.Store(id='mock-data-store')
            
        ], className="clinical-formats-container")
    
    def create_dictionary_overview_tab(self, dictionary: DataDictionary) -> html.Div:
        """Create dictionary overview tab content"""
        if not dictionary:
            return html.Div("No dictionary loaded", className="alert alert-info")
        
        # Summary statistics
        total_fields = len(dictionary.fields)
        required_fields = sum(1 for f in dictionary.fields if f.required)
        field_types = {}
        for field in dictionary.fields:
            field_types[field.data_type] = field_types.get(field.data_type, 0) + 1
        
        return html.Div([
            # Dictionary metadata
            html.Div([
                html.H5("Dictionary Information"),
                html.Table([
                    html.Tr([html.Td("Name:"), html.Td(dictionary.name)]),
                    html.Tr([html.Td("Version:"), html.Td(dictionary.version)]),
                    html.Tr([html.Td("Description:"), html.Td(dictionary.description)]),
                    html.Tr([html.Td("Total Fields:"), html.Td(str(total_fields))]),
                    html.Tr([html.Td("Required Fields:"), html.Td(str(required_fields))]),
                    html.Tr([html.Td("Source Type:"), html.Td(dictionary.metadata.get('source_type', 'Unknown'))])
                ], className="table table-sm")
            ], className="col-md-6"),
            
            # Field type distribution
            html.Div([
                html.H5("Field Type Distribution"),
                dcc.Graph(
                    figure=px.pie(
                        values=list(field_types.values()),
                        names=list(field_types.keys()),
                        title="Distribution of Field Types"
                    )
                )
            ], className="col-md-6")
        ], className="row mb-4")
    
    def create_field_analysis_tab(self, dictionary: DataDictionary) -> html.Div:
        """Create field analysis tab content"""
        if not dictionary:
            return html.Div("No dictionary loaded", className="alert alert-info")
        
        # Prepare field data for table
        field_data = []
        for field in dictionary.fields:
            field_data.append({
                'Field Name': field.name,
                'Label': field.label,
                'Data Type': field.data_type,
                'Required': 'Yes' if field.required else 'No',
                'Has Choices': 'Yes' if field.choices else 'No',
                'Description': field.description[:100] + '...' if len(field.description) > 100 else field.description
            })
        
        return html.Div([
            html.H5("Field Definitions"),
            html.Div([
                # Search and filter controls
                html.Div([
                    dcc.Input(
                        id='field-search',
                        type='text',
                        placeholder='Search fields...',
                        className="form-control mb-3"
                    ),
                    dcc.Dropdown(
                        id='field-type-filter',
                        options=[{'label': f'Type: {t}', 'value': t} 
                                for t in sorted(set(f.data_type for f in dictionary.fields))],
                        placeholder='Filter by type...',
                        multi=True,
                        className="mb-3"
                    )
                ], className="row"),
                
                # Field table
                dash_table.DataTable(
                    id='field-analysis-table',
                    data=field_data,
                    columns=[
                        {'name': col, 'id': col, 'type': 'text'}
                        for col in field_data[0].keys() if field_data
                    ],
                    filter_action='native',
                    sort_action='native',
                    page_size=20,
                    style_table={'overflowX': 'auto'},
                    style_cell={'textAlign': 'left', 'padding': '10px'},
                    style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
                    style_data_conditional=[
                        {
                            'if': {'filter_query': '{Required} = Yes'},
                            'backgroundColor': '#fff3cd'
                        }
                    ]
                )
            ])
        ])
    
    def create_mock_data_tab(self, dictionary: DataDictionary, format_type: str) -> html.Div:
        """Create mock data preview tab"""
        if not dictionary:
            return html.Div("No dictionary loaded", className="alert alert-info")
        
        return html.Div([
            html.H5("Mock Data Generation"),
            
            # Generation controls
            html.Div([
                html.Div([
                    html.Label("Number of Records:", className="form-label"),
                    dcc.Input(
                        id='mock-records-input',
                        type='number',
                        value=10,
                        min=1,
                        max=1000,
                        className="form-control"
                    )
                ], className="col-md-3"),
                
                html.Div([
                    html.Label("Output Format:", className="form-label"),
                    dcc.Dropdown(
                        id='mock-format-selector',
                        options=[
                            {'label': 'DataFrame (CSV)', 'value': 'dataframe'},
                            {'label': 'REDCap Export', 'value': 'redcap'},
                            {'label': 'OMOP Tables', 'value': 'omop'},
                            {'label': 'FHIR Bundle', 'value': 'fhir'}
                        ],
                        value=format_type if format_type in ['redcap', 'omop', 'fhir'] else 'dataframe',
                        className="form-control"
                    )
                ], className="col-md-3"),
                
                html.Div([
                    html.Label(" ", className="form-label"),
                    html.Button(
                        "Generate Mock Data",
                        id='generate-mock-data-btn',
                        className="btn btn-primary d-block"
                    )
                ], className="col-md-3")
            ], className="row mb-4"),
            
            # Mock data display
            html.Div(id='mock-data-display'),
            
            # Download options
            html.Div([
                html.Button(
                    "Download as CSV",
                    id='download-mock-csv-btn',
                    className="btn btn-outline-primary me-2"
                ),
                html.Button(
                    "Download as JSON",
                    id='download-mock-json-btn',
                    className="btn btn-outline-secondary"
                ),
                dcc.Download(id='download-mock-data')
            ], id='mock-download-options', style={'display': 'none'}, className="mt-3")
        ])
    
    def create_format_conversion_tab(self, dictionary: DataDictionary) -> html.Div:
        """Create format conversion tab"""
        if not dictionary:
            return html.Div("No dictionary loaded", className="alert alert-info")
        
        return html.Div([
            html.H5("Format Conversion"),
            html.P("Convert your dictionary to different clinical data formats", className="text-muted"),
            
            # Conversion options
            html.Div([
                html.Div([
                    html.H6("Export Dictionary As:"),
                    html.Div([
                        html.Button(
                            "📋 REDCap Data Dictionary",
                            id='export-redcap-btn',
                            className="btn btn-outline-primary mb-2 d-block w-100"
                        ),
                        html.Button(
                            "🔬 OMOP CDM Specification",
                            id='export-omop-btn',
                            className="btn btn-outline-success mb-2 d-block w-100"
                        ),
                        html.Button(
                            "🔄 FHIR StructureDefinition",
                            id='export-fhir-btn',
                            className="btn btn-outline-info mb-2 d-block w-100"
                        ),
                        html.Button(
                            "📄 Generic CSV",
                            id='export-generic-btn',
                            className="btn btn-outline-secondary mb-2 d-block w-100"
                        )
                    ])
                ], className="col-md-6"),
                
                html.Div([
                    html.H6("Mapping Configuration:"),
                    html.Div(id='mapping-config-display')
                ], className="col-md-6")
            ], className="row"),
            
            # Conversion preview
            html.Div(id='conversion-preview'),
            
            # Download conversion
            dcc.Download(id='download-conversion')
        ])
    
    def create_clinical_insights_tab(self, dictionary: DataDictionary) -> html.Div:
        """Create clinical insights tab"""
        if not dictionary:
            return html.Div("No dictionary loaded", className="alert alert-info")
        
        # Analyze clinical relevance
        clinical_fields = []
        demographic_fields = []
        outcome_fields = []
        
        for field in dictionary.fields:
            name_lower = field.name.lower()
            label_lower = field.label.lower()
            
            if any(term in name_lower or term in label_lower 
                   for term in ['age', 'gender', 'sex', 'race', 'ethnicity', 'birth']):
                demographic_fields.append(field)
            elif any(term in name_lower or term in label_lower 
                     for term in ['outcome', 'death', 'survival', 'response', 'adverse']):
                outcome_fields.append(field)
            elif any(term in name_lower or term in label_lower 
                     for term in ['lab', 'test', 'measure', 'vital', 'diagnosis', 'condition']):
                clinical_fields.append(field)
        
        return html.Div([
            html.H5("Clinical Data Insights"),
            
            # Clinical field categories
            html.Div([
                html.Div([
                    html.H6(f"👥 Demographics ({len(demographic_fields)})"),
                    html.Ul([
                        html.Li(f"{field.name} - {field.label}")
                        for field in demographic_fields[:10]  # Show first 10
                    ]) if demographic_fields else html.P("No demographic fields identified")
                ], className="col-md-4"),
                
                html.Div([
                    html.H6(f"🔬 Clinical Measures ({len(clinical_fields)})"),
                    html.Ul([
                        html.Li(f"{field.name} - {field.label}")
                        for field in clinical_fields[:10]  # Show first 10
                    ]) if clinical_fields else html.P("No clinical fields identified")
                ], className="col-md-4"),
                
                html.Div([
                    html.H6(f"📊 Outcomes ({len(outcome_fields)})"),
                    html.Ul([
                        html.Li(f"{field.name} - {field.label}")
                        for field in outcome_fields[:10]  # Show first 10
                    ]) if outcome_fields else html.P("No outcome fields identified")
                ], className="col-md-4")
            ], className="row mb-4"),
            
            # Data completeness recommendations
            html.Div([
                html.H6("📋 Data Quality Recommendations"),
                html.Div(id='quality-recommendations')
            ])
        ])
    
    def register_callbacks(self, app):
        """Register all callbacks for clinical formats dashboard"""
        
        @app.callback(
            [Output('clinical-dictionary-store', 'data'),
             Output('clinical-format-store', 'data'),
             Output('clinical-dictionary-summary', 'children')],
            [Input('clinical-dictionary-upload', 'contents')],
            [State('clinical-dictionary-upload', 'filename'),
             State('clinical-format-selector', 'value')]
        )
        def handle_dictionary_upload(contents, filename, format_selection):
            if not contents:
                return None, None, ""
            
            try:
                # Parse uploaded file
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                
                # Save to temporary file
                import tempfile
                import os
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp_file:
                    tmp_file.write(decoded)
                    tmp_path = tmp_file.name
                
                # Parse dictionary
                format_hint = format_selection if format_selection != 'auto' else None
                dictionary = self.integrator.parse_clinical_dictionary(tmp_path, format_hint)
                
                # Clean up temp file
                os.unlink(tmp_path)
                
                # Store dictionary and format
                self.current_dictionary = dictionary
                detected_format = dictionary.metadata.get('source_type', 'generic')
                
                # Create summary
                summary = html.Div([
                    html.Div([
                        html.H5("✅ Dictionary Loaded Successfully", className="text-success"),
                        html.Table([
                            html.Tr([html.Td("File:"), html.Td(filename)]),
                            html.Tr([html.Td("Format:"), html.Td(detected_format.upper())]),
                            html.Tr([html.Td("Fields:"), html.Td(str(len(dictionary.fields)))]),
                            html.Tr([html.Td("Required:"), html.Td(str(sum(1 for f in dictionary.fields if f.required)))])
                        ], className="table table-sm")
                    ], className="alert alert-success")
                ])
                
                return dictionary.to_dict(), detected_format, summary
                
            except Exception as e:
                error_summary = html.Div([
                    html.H5("❌ Error Loading Dictionary", className="text-danger"),
                    html.P(f"Error: {str(e)}", className="text-muted")
                ], className="alert alert-danger")
                
                return None, None, error_summary
        
        @app.callback(
            Output('clinical-formats-tab-content', 'children'),
            [Input('clinical-formats-tabs', 'value')],
            [State('clinical-dictionary-store', 'data'),
             State('clinical-format-store', 'data')]
        )
        def update_tab_content(active_tab, dictionary_data, format_type):
            if not dictionary_data:
                return html.Div("Please upload a dictionary first", className="alert alert-info")
            
            dictionary = DataDictionary.from_dict(dictionary_data)
            
            if active_tab == 'dictionary-view':
                return self.create_dictionary_overview_tab(dictionary)
            elif active_tab == 'field-analysis':
                return self.create_field_analysis_tab(dictionary)
            elif active_tab == 'mock-data':
                return self.create_mock_data_tab(dictionary, format_type)
            elif active_tab == 'format-conversion':
                return self.create_format_conversion_tab(dictionary)
            elif active_tab == 'clinical-insights':
                return self.create_clinical_insights_tab(dictionary)
            
            return html.Div()
        
        @app.callback(
            [Output('mock-data-display', 'children'),
             Output('mock-data-store', 'data'),
             Output('mock-download-options', 'style')],
            [Input('generate-mock-data-btn', 'n_clicks')],
            [State('clinical-dictionary-store', 'data'),
             State('mock-records-input', 'value'),
             State('mock-format-selector', 'value')]
        )
        def generate_mock_data(n_clicks, dictionary_data, num_records, output_format):
            if not n_clicks or not dictionary_data:
                return "", None, {'display': 'none'}
            
            try:
                dictionary = DataDictionary.from_dict(dictionary_data)
                mock_data = self.integrator.generate_mock_clinical_data(
                    dictionary, output_format, num_records or 10
                )
                
                # Display based on format
                if output_format == 'omop':
                    # OMOP returns dict of DataFrames
                    display_components = []
                    for table_name, df in mock_data.items():
                        display_components.extend([
                            html.H6(f"Table: {table_name}"),
                            dash_table.DataTable(
                                data=df.head(10).to_dict('records'),
                                columns=[{'name': col, 'id': col} for col in df.columns],
                                style_table={'overflowX': 'auto'},
                                style_cell={'textAlign': 'left'}
                            ),
                            html.Hr()
                        ])
                    display = html.Div(display_components)
                    
                elif output_format == 'fhir':
                    # FHIR returns JSON bundle
                    display = html.Div([
                        html.Pre(json.dumps(mock_data, indent=2)[:2000] + "...")
                    ])
                    
                else:
                    # DataFrame format
                    display = dash_table.DataTable(
                        data=mock_data.head(20).to_dict('records'),
                        columns=[{'name': col, 'id': col} for col in mock_data.columns],
                        style_table={'overflowX': 'auto'},
                        style_cell={'textAlign': 'left'}
                    )
                
                return display, mock_data.to_dict() if hasattr(mock_data, 'to_dict') else mock_data, {'display': 'block'}
                
            except Exception as e:
                return html.Div(f"Error generating mock data: {str(e)}", className="alert alert-danger"), None, {'display': 'none'}


def test_phase6_clinical_formats():
    """Test Phase 6 clinical formats implementation"""
    print("=== Testing Phase 6: Clinical Data Format Support ===")
    
    # Test the clinical formats module
    from app.core.clinical_formats import test_clinical_formats
    test_clinical_formats()
    
    print("✅ Phase 6 clinical formats test completed successfully")


if __name__ == "__main__":
    test_phase6_clinical_formats()