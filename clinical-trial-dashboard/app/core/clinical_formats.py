"""
Phase 6: Clinical Data Format Support
Specialized parsers for REDCap, OMOP CDM, and FHIR formats
Built on top of the generic data dictionary engine from Phase 5
"""

import json
import xml.etree.ElementTree as ET
import pandas as pd
from typing import Dict, List, Optional, Union, Any, Tuple
from datetime import datetime
import requests
from pathlib import Path
import zipfile
import logging
from dataclasses import dataclass, field

from .data_dictionary import DataDictionary, FieldDefinition, GenericDictionaryParser, FieldType


@dataclass
class ClinicalStandard:
    """Base class for clinical data standards"""
    name: str
    version: str
    description: str
    field_mappings: Dict[str, str] = field(default_factory=dict)
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)


class REDCapParser:
    """REDCap Data Dictionary and Export Parser"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.standard = ClinicalStandard(
            name="REDCap",
            version="14.0+",
            description="Research Electronic Data Capture data dictionary format",
            required_fields=["Variable / Field Name", "Field Type", "Field Label"],
            optional_fields=["Choices, Calculations, OR Slider Labels", "Field Note", "Text Validation Type OR Show Slider Number"]
        )
    
    def parse_data_dictionary(self, file_path: str) -> DataDictionary:
        """Parse REDCap data dictionary CSV export"""
        try:
            df = pd.read_csv(file_path)
            
            # Standard REDCap column mappings
            column_mappings = {
                "Variable / Field Name": "field_name",
                "Form Name": "form_name", 
                "Section Header": "section",
                "Field Type": "field_type",
                "Field Label": "field_label",
                "Choices, Calculations, OR Slider Labels": "choices",
                "Field Note": "field_note",
                "Text Validation Type OR Show Slider Number": "validation",
                "Text Validation Min": "validation_min",
                "Text Validation Max": "validation_max",
                "Identifier?": "identifier",
                "Branching Logic (Show field only if...)": "branching_logic",
                "Required Field?": "required",
                "Custom Alignment": "alignment",
                "Question Number (surveys only)": "question_number",
                "Matrix Group Name": "matrix_group",
                "Matrix Ranking?": "matrix_ranking"
            }
            
            # Rename columns to standard format
            available_columns = df.columns.tolist()
            rename_dict = {col: column_mappings.get(col, col.lower().replace(' ', '_')) 
                          for col in available_columns if col in column_mappings}
            df = df.rename(columns=rename_dict)
            
            fields = []
            for _, row in df.iterrows():
                field_def = self._create_field_definition_from_redcap(row)
                fields.append(field_def)
            
            dictionary = DataDictionary(
                name=f"REDCap_Dictionary_{datetime.now().strftime('%Y%m%d')}",
                version="1.0",
                description="Imported from REDCap data dictionary",
                fields=fields,
                metadata={
                    "source_type": "redcap",
                    "imported_at": datetime.now().isoformat(),
                    "total_fields": len(fields),
                    "forms": list(df.get('form_name', pd.Series()).dropna().unique()) if 'form_name' in df.columns else []
                }
            )
            
            return dictionary
            
        except Exception as e:
            self.logger.error(f"Error parsing REDCap dictionary: {str(e)}")
            raise
    
    def _create_field_definition_from_redcap(self, row) -> FieldDefinition:
        """Convert REDCap row to standardized field definition"""
        field_type = self._map_redcap_field_type(row.get('field_type', 'text'))
        
        # Parse choices for categorical fields
        choices = []
        if row.get('choices') and pd.notna(row.get('choices')):
            choices = self._parse_redcap_choices(row['choices'])
        
        # Parse validation rules
        validation_rules = self._parse_redcap_validation(row)
        
        return FieldDefinition(
            name=row.get('field_name', ''),
            label=row.get('field_label', ''),
            data_type=field_type,
            description=row.get('field_note', ''),
            required=row.get('required') == 'y',
            choices=choices,
            validation_rules=validation_rules,
            metadata={
                "redcap_type": row.get('field_type'),
                "form_name": row.get('form_name'),
                "section": row.get('section'),
                "branching_logic": row.get('branching_logic'),
                "identifier": row.get('identifier') == 'y',
                "matrix_group": row.get('matrix_group')
            }
        )
    
    def _map_redcap_field_type(self, redcap_type: str) -> str:
        """Map REDCap field types to standard types"""
        mapping = {
            'text': 'string',
            'notes': 'text',
            'dropdown': 'categorical',
            'radio': 'categorical', 
            'checkbox': 'multi_select',
            'yesno': 'boolean',
            'truefalse': 'boolean',
            'file': 'file',
            'slider': 'numeric',
            'calc': 'calculated',
            'descriptive': 'info'
        }
        return mapping.get(redcap_type.lower(), 'string')
    
    def _parse_redcap_choices(self, choices_str: str) -> List[Dict]:
        """Parse REDCap choices format: '1, Option 1 | 2, Option 2'"""
        choices = []
        if not choices_str:
            return choices
            
        try:
            for choice in choices_str.split('|'):
                choice = choice.strip()
                if ',' in choice:
                    value, label = choice.split(',', 1)
                    choices.append({
                        'value': value.strip(),
                        'label': label.strip()
                    })
        except Exception:
            # Fallback for malformed choices
            pass
        
        return choices
    
    def _parse_redcap_validation(self, row) -> Dict:
        """Parse REDCap validation rules"""
        validation = {}
        
        if row.get('validation'):
            validation['type'] = row['validation']
        
        if row.get('validation_min') and pd.notna(row.get('validation_min')):
            validation['min'] = row['validation_min']
            
        if row.get('validation_max') and pd.notna(row.get('validation_max')):
            validation['max'] = row['validation_max']
        
        return validation
    
    def generate_mock_data(self, dictionary: DataDictionary, num_records: int = 100) -> pd.DataFrame:
        """Generate mock REDCap data based on dictionary"""
        import random
        import numpy as np
        from datetime import date, timedelta
        
        data = {}
        
        for field in dictionary.fields:
            if field.field_type == FieldType.CATEGORICAL and field.choices:
                data[field.name] = [random.choice([c['value'] for c in field.choices]) 
                                  for _ in range(num_records)]
            elif field.field_type == FieldType.BOOLEAN:
                data[field.name] = [random.choice([0, 1]) for _ in range(num_records)]
            elif field.field_type in [FieldType.NUMBER, FieldType.DECIMAL]:
                min_val = field.validation_rules.get('min', 0)
                max_val = field.validation_rules.get('max', 100)
                data[field.name] = [random.uniform(float(min_val), float(max_val)) 
                                  for _ in range(num_records)]
            elif field.field_type == FieldType.DATE:
                start_date = date(2020, 1, 1)
                end_date = date(2024, 12, 31)
                data[field.name] = [(start_date + timedelta(days=random.randint(0, (end_date - start_date).days))).isoformat()
                                  for _ in range(num_records)]
            else:  # text/string
                data[field.name] = [f"Sample_{field.name}_{i}" for i in range(num_records)]
        
        return pd.DataFrame(data)


class OMOPParser:
    """OMOP Common Data Model Parser"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.standard = ClinicalStandard(
            name="OMOP CDM",
            version="6.0",
            description="Observational Medical Outcomes Partnership Common Data Model",
            required_fields=["table_name", "column_name", "data_type"],
            optional_fields=["is_nullable", "description", "vocabulary_id"]
        )
        
        # Core OMOP tables with key fields
        self.omop_tables = {
            'person': ['person_id', 'gender_concept_id', 'year_of_birth', 'month_of_birth', 'day_of_birth', 'birth_datetime', 'race_concept_id', 'ethnicity_concept_id'],
            'observation_period': ['observation_period_id', 'person_id', 'observation_period_start_date', 'observation_period_end_date'],
            'visit_occurrence': ['visit_occurrence_id', 'person_id', 'visit_concept_id', 'visit_start_date', 'visit_end_date'],
            'condition_occurrence': ['condition_occurrence_id', 'person_id', 'condition_concept_id', 'condition_start_date', 'condition_end_date'],
            'drug_exposure': ['drug_exposure_id', 'person_id', 'drug_concept_id', 'drug_exposure_start_date', 'drug_exposure_end_date'],
            'measurement': ['measurement_id', 'person_id', 'measurement_concept_id', 'measurement_date', 'value_as_number', 'value_as_concept_id'],
            'observation': ['observation_id', 'person_id', 'observation_concept_id', 'observation_date', 'value_as_string', 'value_as_number']
        }
    
    def parse_data_dictionary(self, file_path: str) -> DataDictionary:
        """Parse OMOP CDM specification from CSV"""
        try:
            df = pd.read_csv(file_path)
            
            fields = []
            for _, row in df.iterrows():
                field_def = self._create_field_definition_from_omop(row)
                fields.append(field_def)
            
            dictionary = DataDictionary(
                name=f"OMOP_CDM_{datetime.now().strftime('%Y%m%d')}",
                version="6.0",
                description="OMOP Common Data Model dictionary",
                fields=fields,
                metadata={
                    "source_type": "omop_cdm",
                    "imported_at": datetime.now().isoformat(),
                    "total_fields": len(fields),
                    "tables": list(df.get('table_name', pd.Series()).dropna().unique()) if 'table_name' in df.columns else []
                }
            )
            
            return dictionary
            
        except Exception as e:
            self.logger.error(f"Error parsing OMOP dictionary: {str(e)}")
            raise
    
    def _create_field_definition_from_omop(self, row) -> FieldDefinition:
        """Convert OMOP row to standardized field definition"""
        field_type = self._map_omop_data_type(row.get('data_type', 'varchar'))
        
        # OMOP concept fields are typically categorical
        is_concept_field = '_concept_id' in str(row.get('column_name', ''))
        if is_concept_field:
            field_type = 'categorical'
        
        return FieldDefinition(
            name=row.get('column_name', ''),
            label=row.get('column_name', '').replace('_', ' ').title(),
            data_type=field_type,
            description=row.get('description', ''),
            required=row.get('is_nullable', 'Yes') == 'No',
            choices=[],  # Would need concept vocabulary for actual choices
            validation_rules=self._parse_omop_validation(row),
            metadata={
                "omop_table": row.get('table_name'),
                "omop_data_type": row.get('data_type'),
                "is_nullable": row.get('is_nullable'),
                "vocabulary_id": row.get('vocabulary_id'),
                "is_concept_field": is_concept_field
            }
        )
    
    def _map_omop_data_type(self, omop_type: str) -> str:
        """Map OMOP data types to standard types"""
        mapping = {
            'varchar': 'string',
            'integer': 'integer', 
            'bigint': 'integer',
            'numeric': 'numeric',
            'float': 'numeric',
            'date': 'date',
            'datetime': 'datetime',
            'timestamp': 'datetime',
            'text': 'text'
        }
        return mapping.get(omop_type.lower(), 'string')
    
    def _parse_omop_validation(self, row) -> Dict:
        """Parse OMOP validation rules from data type"""
        validation = {}
        
        data_type = row.get('data_type', '').lower()
        column_name = row.get('column_name', '').lower()
        
        # Common OMOP validation patterns
        if '_id' in column_name and data_type in ['integer', 'bigint']:
            validation['min'] = 1  # IDs are typically positive
        
        if 'year' in column_name:
            validation['min'] = 1900
            validation['max'] = 2100
            
        if 'month' in column_name:
            validation['min'] = 1 
            validation['max'] = 12
            
        if 'day' in column_name:
            validation['min'] = 1
            validation['max'] = 31
        
        return validation
    
    def generate_mock_data(self, dictionary: DataDictionary, num_records: int = 100) -> Dict[str, pd.DataFrame]:
        """Generate mock OMOP data organized by table"""
        import random
        from datetime import date, timedelta
        
        # Group fields by table
        tables = {}
        for field in dictionary.fields:
            table_name = field.metadata.get('omop_table', 'unknown')
            if table_name not in tables:
                tables[table_name] = []
            tables[table_name].append(field)
        
        mock_data = {}
        person_ids = list(range(1, num_records + 1))
        
        for table_name, fields in tables.items():
            data = {}
            
            # Generate person_id for all tables (core linking field)
            if any(f.name == 'person_id' for f in fields):
                data['person_id'] = person_ids
            
            for field in fields:
                if field.name == 'person_id':
                    continue  # Already handled
                    
                if field.name.endswith('_id') and field.field_type == FieldType.INTEGER:
                    # Generate sequential IDs
                    data[field.name] = list(range(1, num_records + 1))
                elif field.name.endswith('_concept_id'):
                    # Mock concept IDs (would normally come from vocabulary)
                    data[field.name] = [random.randint(1000, 9999) for _ in range(num_records)]
                elif field.field_type == FieldType.DATE:
                    start_date = date(2020, 1, 1)
                    end_date = date(2024, 12, 31)
                    data[field.name] = [(start_date + timedelta(days=random.randint(0, (end_date - start_date).days))).isoformat()
                                      for _ in range(num_records)]
                elif field.field_type in [FieldType.NUMBER, FieldType.DECIMAL]:
                    min_val = field.validation_rules.get('min', 0)
                    max_val = field.validation_rules.get('max', 100)
                    data[field.name] = [random.uniform(float(min_val), float(max_val)) 
                                      for _ in range(num_records)]
                else:
                    data[field.name] = [f"Sample_{field.name}_{i}" for i in range(num_records)]
            
            mock_data[table_name] = pd.DataFrame(data)
        
        return mock_data


class FHIRParser:
    """FHIR (Fast Healthcare Interoperability Resources) Parser"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.standard = ClinicalStandard(
            name="FHIR",
            version="R4",
            description="Fast Healthcare Interoperability Resources",
            required_fields=["resourceType", "id"],
            optional_fields=["meta", "text", "extension"]
        )
        
        # Common FHIR resource types with key elements
        self.fhir_resources = {
            'Patient': ['id', 'identifier', 'name', 'gender', 'birthDate', 'address', 'telecom'],
            'Observation': ['id', 'status', 'code', 'subject', 'effectiveDateTime', 'valueQuantity', 'valueString'],
            'Condition': ['id', 'clinicalStatus', 'verificationStatus', 'code', 'subject', 'onsetDateTime'],
            'MedicationRequest': ['id', 'status', 'medicationCodeableConcept', 'subject', 'authoredOn', 'dosageInstruction'],
            'Encounter': ['id', 'status', 'class', 'subject', 'period'],
            'DiagnosticReport': ['id', 'status', 'code', 'subject', 'effectiveDateTime', 'result']
        }
    
    def parse_fhir_bundle(self, file_path: str) -> DataDictionary:
        """Parse FHIR Bundle JSON file"""
        try:
            with open(file_path, 'r') as f:
                bundle = json.load(f)
            
            fields = []
            resource_types = set()
            
            # Extract field definitions from bundle entries
            if 'entry' in bundle:
                for entry in bundle['entry']:
                    resource = entry.get('resource', {})
                    resource_type = resource.get('resourceType')
                    
                    if resource_type:
                        resource_types.add(resource_type)
                        resource_fields = self._extract_fhir_fields(resource, resource_type)
                        fields.extend(resource_fields)
            
            # Remove duplicates based on field name and resource type
            unique_fields = []
            seen = set()
            for field in fields:
                key = (field.name, field.metadata.get('fhir_resource_type'))
                if key not in seen:
                    unique_fields.append(field)
                    seen.add(key)
            
            dictionary = DataDictionary(
                name=f"FHIR_Bundle_{datetime.now().strftime('%Y%m%d')}",
                version="R4",
                description="Imported from FHIR Bundle",
                fields=unique_fields,
                metadata={
                    "source_type": "fhir_r4",
                    "imported_at": datetime.now().isoformat(),
                    "total_fields": len(unique_fields),
                    "resource_types": list(resource_types)
                }
            )
            
            return dictionary
            
        except Exception as e:
            self.logger.error(f"Error parsing FHIR bundle: {str(e)}")
            raise
    
    def _extract_fhir_fields(self, resource: Dict, resource_type: str) -> List[FieldDefinition]:
        """Extract field definitions from FHIR resource"""
        fields = []
        
        def extract_recursive(obj, prefix="", level=0):
            if level > 3:  # Prevent infinite recursion
                return
                
            if isinstance(obj, dict):
                for key, value in obj.items():
                    field_name = f"{prefix}.{key}" if prefix else key
                    
                    if isinstance(value, (str, int, float, bool)):
                        field_type = self._infer_fhir_type(value, key)
                        fields.append(FieldDefinition(
                            name=field_name,
                            label=key.replace('_', ' ').title(),
                            data_type=field_type,
                            description=f"FHIR {resource_type} field: {key}",
                            required=key in ['id', 'resourceType'],
                            choices=[],
                            validation_rules={},
                            metadata={
                                "fhir_resource_type": resource_type,
                                "fhir_element": key,
                                "fhir_path": field_name
                            }
                        ))
                    elif isinstance(value, list) and value:
                        # Handle arrays - analyze first element
                        extract_recursive(value[0], field_name, level + 1)
                    elif isinstance(value, dict):
                        extract_recursive(value, field_name, level + 1)
            
        extract_recursive(resource)
        return fields
    
    def _infer_fhir_type(self, value: Any, field_name: str) -> str:
        """Infer data type from FHIR field value and name"""
        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'numeric'
        elif isinstance(value, str):
            if 'date' in field_name.lower():
                return 'date'
            elif 'time' in field_name.lower():
                return 'datetime'
            elif field_name.lower() in ['status', 'gender', 'class']:
                return 'categorical'
            else:
                return 'string'
        else:
            return 'string'
    
    def generate_mock_fhir_bundle(self, dictionary: DataDictionary, num_patients: int = 10) -> Dict:
        """Generate mock FHIR Bundle"""
        import uuid
        from datetime import datetime, timedelta
        import random
        
        bundle = {
            "resourceType": "Bundle",
            "id": str(uuid.uuid4()),
            "type": "collection",
            "entry": []
        }
        
        # Generate patients first
        patients = []
        for i in range(num_patients):
            patient_id = str(uuid.uuid4())
            patients.append(patient_id)
            
            patient_resource = {
                "resourceType": "Patient",
                "id": patient_id,
                "identifier": [{
                    "system": "http://example.org/patients",
                    "value": f"PT-{i+1:04d}"
                }],
                "name": [{
                    "family": f"TestFamily{i+1}",
                    "given": [f"TestGiven{i+1}"]
                }],
                "gender": random.choice(["male", "female", "other"]),
                "birthDate": (datetime.now() - timedelta(days=random.randint(365*20, 365*80))).strftime("%Y-%m-%d")
            }
            
            bundle["entry"].append({"resource": patient_resource})
        
        # Generate observations for patients
        for patient_id in patients:
            for obs_type in ["vital-signs", "laboratory"]:
                obs_resource = {
                    "resourceType": "Observation",
                    "id": str(uuid.uuid4()),
                    "status": "final",
                    "code": {
                        "coding": [{
                            "system": "http://loinc.org",
                            "code": random.choice(["8480-6", "8462-4", "33747-0"]),
                            "display": random.choice(["Systolic BP", "Diastolic BP", "Hemoglobin"])
                        }]
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "effectiveDateTime": (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                    "valueQuantity": {
                        "value": random.uniform(10, 200),
                        "unit": "mmHg"
                    }
                }
                bundle["entry"].append({"resource": obs_resource})
        
        return bundle


class ClinicalFormatIntegrator:
    """Integration layer for all clinical formats"""
    
    def __init__(self):
        self.redcap_parser = REDCapParser()
        self.omop_parser = OMOPParser()
        self.fhir_parser = FHIRParser()
        self.generic_parser = GenericDictionaryParser()
        self.logger = logging.getLogger(__name__)
    
    def detect_format(self, file_path: str) -> str:
        """Auto-detect clinical data format"""
        try:
            file_extension = Path(file_path).suffix.lower()
            
            if file_extension == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if 'resourceType' in data and data.get('resourceType') == 'Bundle':
                        return 'fhir'
                    elif isinstance(data, list) and len(data) > 0 and 'resourceType' in data[0]:
                        return 'fhir'
            
            elif file_extension == '.csv':
                df = pd.read_csv(file_path, nrows=5)  # Read first few rows
                columns = [col.lower() for col in df.columns]
                
                # REDCap detection
                redcap_indicators = ['variable / field name', 'field type', 'field label']
                if any(indicator in ' '.join(columns) for indicator in redcap_indicators):
                    return 'redcap'
                
                # OMOP detection
                omop_indicators = ['table_name', 'column_name', 'data_type']
                if all(indicator in columns for indicator in omop_indicators):
                    return 'omop'
            
            # Default to generic
            return 'generic'
            
        except Exception as e:
            self.logger.warning(f"Error detecting format for {file_path}: {str(e)}")
            return 'generic'
    
    def parse_clinical_dictionary(self, file_path: str, format_hint: Optional[str] = None) -> DataDictionary:
        """Parse clinical data dictionary with auto-detection"""
        detected_format = format_hint or self.detect_format(file_path)
        
        try:
            if detected_format == 'redcap':
                return self.redcap_parser.parse_data_dictionary(file_path)
            elif detected_format == 'omop':
                return self.omop_parser.parse_data_dictionary(file_path)
            elif detected_format == 'fhir':
                return self.fhir_parser.parse_fhir_bundle(file_path)
            else:
                return self.generic_parser.parse_dictionary(file_path)
                
        except Exception as e:
            self.logger.error(f"Error parsing {detected_format} format: {str(e)}")
            # Fallback to generic parser
            return self.generic_parser.parse_dictionary(file_path)
    
    def generate_mock_clinical_data(self, dictionary: DataDictionary, format_type: str, num_records: int = 100) -> Union[pd.DataFrame, Dict]:
        """Generate mock data in specified clinical format"""
        try:
            if format_type == 'redcap':
                return self.redcap_parser.generate_mock_data(dictionary, num_records)
            elif format_type == 'omop':
                return self.omop_parser.generate_mock_data(dictionary, num_records)
            elif format_type == 'fhir':
                return self.fhir_parser.generate_mock_fhir_bundle(dictionary, num_records)
            else:
                # Generic DataFrame
                from .data_dictionary import MockDataGenerator
                generator = MockDataGenerator()
                return generator.generate_mock_data(dictionary, num_records)
                
        except Exception as e:
            self.logger.error(f"Error generating mock {format_type} data: {str(e)}")
            raise


def test_clinical_formats():
    """Test function for Phase 6 clinical format support"""
    integrator = ClinicalFormatIntegrator()
    
    # Test 1: Create mock REDCap dictionary
    print("=== Testing REDCap Format ===")
    redcap_data = {
        'Variable / Field Name': ['patient_id', 'age', 'gender', 'treatment_arm'],
        'Field Type': ['text', 'text', 'dropdown', 'radio'],
        'Field Label': ['Patient ID', 'Age at enrollment', 'Gender', 'Treatment Arm'],
        'Choices, Calculations, OR Slider Labels': ['', '', '1, Male | 2, Female', '1, Treatment | 2, Control'],
        'Text Validation Type OR Show Slider Number': ['', 'integer', '', ''],
        'Required Field?': ['y', 'y', 'y', 'y']
    }
    
    redcap_df = pd.DataFrame(redcap_data)
    redcap_file = '/tmp/test_redcap_dict.csv'
    redcap_df.to_csv(redcap_file, index=False)
    
    try:
        redcap_dict = integrator.parse_clinical_dictionary(redcap_file, 'redcap')
        print(f"✅ REDCap dictionary parsed: {len(redcap_dict.fields)} fields")
        
        # Generate mock data
        mock_redcap = integrator.generate_mock_clinical_data(redcap_dict, 'redcap', 10)
        print(f"✅ REDCap mock data generated: {mock_redcap.shape}")
        
    except Exception as e:
        print(f"❌ REDCap test failed: {str(e)}")
    
    # Test 2: Create mock OMOP dictionary
    print("\n=== Testing OMOP Format ===")
    omop_data = {
        'table_name': ['person', 'person', 'observation_period', 'measurement'],
        'column_name': ['person_id', 'gender_concept_id', 'observation_period_id', 'measurement_id'],
        'data_type': ['bigint', 'integer', 'bigint', 'bigint'],
        'is_nullable': ['No', 'No', 'No', 'No'],
        'description': ['Unique person identifier', 'Gender concept', 'Period identifier', 'Measurement identifier']
    }
    
    omop_df = pd.DataFrame(omop_data)
    omop_file = '/tmp/test_omop_dict.csv'
    omop_df.to_csv(omop_file, index=False)
    
    try:
        omop_dict = integrator.parse_clinical_dictionary(omop_file, 'omop')
        print(f"✅ OMOP dictionary parsed: {len(omop_dict.fields)} fields")
        
        # Generate mock data
        mock_omop = integrator.generate_mock_clinical_data(omop_dict, 'omop', 10)
        print(f"✅ OMOP mock data generated: {len(mock_omop)} tables")
        
    except Exception as e:
        print(f"❌ OMOP test failed: {str(e)}")
    
    # Test 3: Create mock FHIR bundle
    print("\n=== Testing FHIR Format ===")
    fhir_bundle = {
        "resourceType": "Bundle",
        "entry": [
            {
                "resource": {
                    "resourceType": "Patient",
                    "id": "patient-1",
                    "gender": "male",
                    "birthDate": "1980-01-01"
                }
            },
            {
                "resource": {
                    "resourceType": "Observation", 
                    "id": "obs-1",
                    "status": "final",
                    "code": {"text": "Blood Pressure"},
                    "valueQuantity": {"value": 120, "unit": "mmHg"}
                }
            }
        ]
    }
    
    fhir_file = '/tmp/test_fhir_bundle.json'
    with open(fhir_file, 'w') as f:
        json.dump(fhir_bundle, f)
    
    try:
        fhir_dict = integrator.parse_clinical_dictionary(fhir_file, 'fhir')
        print(f"✅ FHIR dictionary parsed: {len(fhir_dict.fields)} fields")
        
        # Generate mock bundle
        mock_fhir = integrator.generate_mock_clinical_data(fhir_dict, 'fhir', 5)
        print(f"✅ FHIR mock bundle generated: {len(mock_fhir['entry'])} entries")
        
    except Exception as e:
        print(f"❌ FHIR test failed: {str(e)}")
    
    print("\n=== Phase 6 Clinical Format Tests Complete ===")


if __name__ == "__main__":
    test_clinical_formats()