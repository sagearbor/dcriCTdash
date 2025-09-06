"""
Generic Data Dictionary Engine - Phase 5
Universal data dictionary processing and field mapping system

This module provides a catch-all MVP for parsing any data dictionary format,
including CSV, JSON, XML, and YAML configurations.
"""

import json
import csv
import yaml
import xml.etree.ElementTree as ET
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class FieldType(Enum):
    """Standard field types for clinical data"""
    TEXT = "text"
    NUMBER = "number" 
    INTEGER = "integer"
    DECIMAL = "decimal"
    DATE = "date"
    DATETIME = "datetime"
    BOOLEAN = "boolean"
    CATEGORICAL = "categorical"
    BINARY = "binary"
    IDENTIFIER = "identifier"
    EMAIL = "email"
    PHONE = "phone"
    UNKNOWN = "unknown"

class ValidationRule(Enum):
    """Common validation rules"""
    REQUIRED = "required"
    RANGE = "range"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    REGEX = "regex"
    CHOICES = "choices"
    UNIQUE = "unique"

@dataclass
class FieldDefinition:
    """Standard field definition structure"""
    name: str
    label: str = ""
    field_type: FieldType = FieldType.UNKNOWN
    description: str = ""
    required: bool = False
    choices: List[Dict[str, Any]] = field(default_factory=list)
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    units: str = ""
    section: str = ""
    branching_logic: str = ""
    field_note: str = ""
    
    # Calculated fields
    confidence_score: float = 0.0
    mapped_from: str = ""
    
class DataDictionary:
    """Container for parsed data dictionary"""
    
    def __init__(self, name: str = ""):
        self.name = name
        self.fields: Dict[str, FieldDefinition] = {}
        self.metadata: Dict[str, Any] = {}
        self.source_format: str = ""
        self.version: str = ""
        
    def add_field(self, field: FieldDefinition) -> None:
        """Add a field definition"""
        self.fields[field.name] = field
        
    def get_field(self, name: str) -> Optional[FieldDefinition]:
        """Get field definition by name"""
        return self.fields.get(name)
        
    def get_fields_by_type(self, field_type: FieldType) -> List[FieldDefinition]:
        """Get all fields of a specific type"""
        return [f for f in self.fields.values() if f.field_type == field_type]
        
    def get_required_fields(self) -> List[FieldDefinition]:
        """Get all required fields"""
        return [f for f in self.fields.values() if f.required]

class GenericDictionaryParser:
    """Universal data dictionary parser supporting multiple formats"""
    
    def __init__(self):
        self.field_type_mappings = self._init_type_mappings()
        self.standard_field_names = self._init_standard_fields()
        
    def _init_type_mappings(self) -> Dict[str, FieldType]:
        """Initialize common field type mappings"""
        return {
            # Text types
            'text': FieldType.TEXT, 'string': FieldType.TEXT, 'varchar': FieldType.TEXT,
            'char': FieldType.TEXT, 'notes': FieldType.TEXT, 'textarea': FieldType.TEXT,
            
            # Numeric types  
            'number': FieldType.NUMBER, 'numeric': FieldType.NUMBER, 'float': FieldType.DECIMAL,
            'decimal': FieldType.DECIMAL, 'double': FieldType.DECIMAL,
            'int': FieldType.INTEGER, 'integer': FieldType.INTEGER,
            
            # Date types
            'date': FieldType.DATE, 'datetime': FieldType.DATETIME, 'timestamp': FieldType.DATETIME,
            'date_mdy': FieldType.DATE, 'date_dmy': FieldType.DATE, 'date_ymd': FieldType.DATE,
            
            # Boolean types
            'boolean': FieldType.BOOLEAN, 'bool': FieldType.BOOLEAN, 'yesno': FieldType.BOOLEAN,
            'truefalse': FieldType.BOOLEAN, 'checkbox': FieldType.BOOLEAN,
            
            # Categorical types
            'dropdown': FieldType.CATEGORICAL, 'radio': FieldType.CATEGORICAL, 
            'select': FieldType.CATEGORICAL, 'enum': FieldType.CATEGORICAL,
            
            # Special types
            'email': FieldType.EMAIL, 'phone': FieldType.PHONE,
            'record_id': FieldType.IDENTIFIER, 'auto_increment': FieldType.IDENTIFIER
        }
    
    def _init_standard_fields(self) -> Dict[str, List[str]]:
        """Initialize standard clinical field name patterns"""
        return {
            'patient_id': ['patient_id', 'subject_id', 'participant_id', 'id', 'record_id', 'study_id'],
            'age': ['age', 'age_years', 'age_at_enrollment', 'baseline_age'],
            'sex': ['sex', 'gender', 'male_female', 's_01', 'demographic_sex'],
            'race': ['race', 'ethnicity', 'race_ethnicity', 'demographic_race'],
            'weight': ['weight', 'weight_kg', 'baseline_weight', 'body_weight'],
            'height': ['height', 'height_cm', 'baseline_height', 'body_height'],
            'bmi': ['bmi', 'body_mass_index', 'baseline_bmi'],
            'vital_status': ['vital_status', 'death_status', 'survival_status', 'v_02'],
            'site_id': ['site_id', 'site', 'center_id', 'institution_id'],
            'visit_date': ['visit_date', 'date_visit', 'assessment_date', 'exam_date']
        }

    def parse_csv_dictionary(self, file_path: str) -> DataDictionary:
        """Parse CSV data dictionary (REDCap style)"""
        logger.info(f"Parsing CSV dictionary: {file_path}")
        
        dictionary = DataDictionary(name=Path(file_path).stem)
        dictionary.source_format = "CSV"
        
        try:
            df = pd.read_csv(file_path)
            
            # Common CSV dictionary column mappings
            col_mappings = {
                'variable_name': ['Variable / Field Name', 'field_name', 'variable_name', 'name', 'field'],
                'field_label': ['Field Label', 'field_label', 'label', 'description'],
                'field_type': ['Field Type', 'field_type', 'type', 'data_type'],
                'choices': ['Choices, Calculations, OR Slider Labels', 'choices', 'values', 'options'],
                'field_note': ['Field Note', 'field_note', 'note', 'help_text'],
                'validation': ['Text Validation Type OR Show Slider Number', 'validation', 'validation_type'],
                'validation_min': ['Text Validation Min', 'min_value', 'minimum'],
                'validation_max': ['Text Validation Max', 'max_value', 'maximum'],
                'required': ['Required Field?', 'required', 'mandatory'],
                'branching_logic': ['Branching Logic (Show field only if...)', 'branching_logic', 'logic'],
                'section': ['Section Header', 'section', 'category', 'form']
            }
            
            # Map actual columns to standard names
            actual_columns = {}
            for standard_name, possible_names in col_mappings.items():
                for col in df.columns:
                    if col in possible_names:
                        actual_columns[standard_name] = col
                        break
            
            logger.info(f"Found columns: {actual_columns}")
            
            # Parse each row as a field
            for _, row in df.iterrows():
                if actual_columns.get('variable_name') and pd.notna(row.get(actual_columns['variable_name'])):
                    field_name = str(row[actual_columns['variable_name']]).strip()
                    
                    field = FieldDefinition(
                        name=field_name,
                        label=str(row.get(actual_columns.get('field_label', 'field_label'), field_name)),
                        description=str(row.get(actual_columns.get('field_note', 'field_note'), "")),
                        section=str(row.get(actual_columns.get('section', 'section'), ""))
                    )
                    
                    # Parse field type
                    field_type_raw = str(row.get(actual_columns.get('field_type', 'field_type'), "")).lower()
                    field.field_type = self.field_type_mappings.get(field_type_raw, FieldType.UNKNOWN)
                    
                    # Parse choices for categorical fields
                    choices_raw = row.get(actual_columns.get('choices', 'choices'))
                    if pd.notna(choices_raw) and str(choices_raw).strip():
                        field.choices = self._parse_choices(str(choices_raw))
                        if field.field_type == FieldType.UNKNOWN and field.choices:
                            field.field_type = FieldType.CATEGORICAL
                    
                    # Parse validation rules
                    validation_rules = {}
                    
                    # Required field
                    required_raw = row.get(actual_columns.get('required', 'required'))
                    if pd.notna(required_raw):
                        field.required = str(required_raw).lower() in ['y', 'yes', '1', 'true', 'required']
                    
                    # Min/Max validation
                    min_val = row.get(actual_columns.get('validation_min', 'validation_min'))
                    max_val = row.get(actual_columns.get('validation_max', 'validation_max'))
                    if pd.notna(min_val) or pd.notna(max_val):
                        validation_rules['range'] = {
                            'min': float(min_val) if pd.notna(min_val) else None,
                            'max': float(max_val) if pd.notna(max_val) else None
                        }
                    
                    field.validation_rules = validation_rules
                    
                    # Branching logic
                    branching_raw = row.get(actual_columns.get('branching_logic', 'branching_logic'))
                    if pd.notna(branching_raw):
                        field.branching_logic = str(branching_raw)
                    
                    # Calculate confidence score based on completeness
                    field.confidence_score = self._calculate_field_confidence(field)
                    
                    dictionary.add_field(field)
            
            logger.info(f"Parsed {len(dictionary.fields)} fields from CSV dictionary")
            return dictionary
            
        except Exception as e:
            logger.error(f"Error parsing CSV dictionary: {e}")
            raise
    
    def parse_json_dictionary(self, file_path: str) -> DataDictionary:
        """Parse JSON data dictionary"""
        logger.info(f"Parsing JSON dictionary: {file_path}")
        
        dictionary = DataDictionary(name=Path(file_path).stem)
        dictionary.source_format = "JSON"
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, dict):
                # Check for metadata
                if 'metadata' in data:
                    dictionary.metadata = data['metadata']
                if 'version' in data:
                    dictionary.version = data['version']
                
                # Find fields section
                fields_data = None
                for key in ['fields', 'variables', 'columns', 'schema']:
                    if key in data:
                        fields_data = data[key]
                        break
                
                if fields_data is None:
                    # Assume the entire dict is fields
                    fields_data = data
                
                # Parse fields
                if isinstance(fields_data, dict):
                    for field_name, field_def in fields_data.items():
                        field = self._parse_json_field(field_name, field_def)
                        dictionary.add_field(field)
                elif isinstance(fields_data, list):
                    for field_def in fields_data:
                        if isinstance(field_def, dict):
                            field_name = field_def.get('name', field_def.get('field', ''))
                            if field_name:
                                field = self._parse_json_field(field_name, field_def)
                                dictionary.add_field(field)
            
            logger.info(f"Parsed {len(dictionary.fields)} fields from JSON dictionary")
            return dictionary
            
        except Exception as e:
            logger.error(f"Error parsing JSON dictionary: {e}")
            raise
    
    def parse_yaml_dictionary(self, file_path: str) -> DataDictionary:
        """Parse YAML data dictionary"""
        logger.info(f"Parsing YAML dictionary: {file_path}")
        
        dictionary = DataDictionary(name=Path(file_path).stem)
        dictionary.source_format = "YAML"
        
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
            
            # Convert to JSON-like structure and use JSON parser
            json_path = file_path + ".temp.json"
            with open(json_path, 'w') as f:
                json.dump(data, f)
            
            result = self.parse_json_dictionary(json_path)
            result.source_format = "YAML"
            
            # Clean up temp file
            Path(json_path).unlink()
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing YAML dictionary: {e}")
            raise
    
    def parse_xml_dictionary(self, file_path: str) -> DataDictionary:
        """Parse XML data dictionary (define.xml style)"""
        logger.info(f"Parsing XML dictionary: {file_path}")
        
        dictionary = DataDictionary(name=Path(file_path).stem)
        dictionary.source_format = "XML"
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Handle different XML structures
            # Look for common field containers
            field_elements = []
            for tag in ['field', 'variable', 'column', 'item']:
                elements = root.findall(f".//{tag}")
                if elements:
                    field_elements = elements
                    break
            
            for elem in field_elements:
                field_name = elem.get('name') or elem.get('Name') or elem.get('OID')
                if not field_name:
                    name_elem = elem.find('.//name') or elem.find('.//Name')
                    if name_elem is not None:
                        field_name = name_elem.text
                
                if field_name:
                    field = FieldDefinition(name=field_name)
                    
                    # Extract label/description
                    for tag in ['label', 'Label', 'description', 'Description']:
                        label_elem = elem.find(f'.//{tag}')
                        if label_elem is not None:
                            field.label = label_elem.text or ""
                            break
                    
                    # Extract type
                    for tag in ['type', 'Type', 'DataType', 'datatype']:
                        type_elem = elem.find(f'.//{tag}')
                        if type_elem is not None:
                            type_text = (type_elem.text or "").lower()
                            field.field_type = self.field_type_mappings.get(type_text, FieldType.UNKNOWN)
                            break
                    
                    # Extract choices/codelist
                    choices = []
                    for codelist in elem.findall('.//CodeList') + elem.findall('.//codelist'):
                        for item in codelist.findall('.//CodeListItem') + codelist.findall('.//item'):
                            code = item.get('CodedValue') or item.get('value')
                            decode = item.find('.//Decode') or item.find('.//decode')
                            decode_text = decode.text if decode is not None else code
                            if code:
                                choices.append({'value': code, 'label': decode_text})
                    
                    field.choices = choices
                    if choices and field.field_type == FieldType.UNKNOWN:
                        field.field_type = FieldType.CATEGORICAL
                    
                    field.confidence_score = self._calculate_field_confidence(field)
                    dictionary.add_field(field)
            
            logger.info(f"Parsed {len(dictionary.fields)} fields from XML dictionary")
            return dictionary
            
        except Exception as e:
            logger.error(f"Error parsing XML dictionary: {e}")
            raise
    
    def auto_detect_format(self, file_path: str) -> str:
        """Auto-detect data dictionary format"""
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.csv':
            return 'csv'
        elif extension == '.json':
            return 'json'  
        elif extension in ['.yaml', '.yml']:
            return 'yaml'
        elif extension == '.xml':
            return 'xml'
        else:
            # Try to detect from content
            try:
                with open(file_path, 'r') as f:
                    content = f.read(1000)  # Read first 1KB
                
                if content.strip().startswith('<'):
                    return 'xml'
                elif content.strip().startswith('{') or content.strip().startswith('['):
                    return 'json'
                elif ':' in content and ('---' in content or 'fields:' in content):
                    return 'yaml'
                else:
                    return 'csv'  # Default fallback
            except:
                return 'csv'
    
    def parse_dictionary(self, file_path: str, format_hint: str = None) -> DataDictionary:
        """Parse data dictionary with automatic format detection"""
        format_type = format_hint or self.auto_detect_format(file_path)
        
        parsers = {
            'csv': self.parse_csv_dictionary,
            'json': self.parse_json_dictionary,
            'yaml': self.parse_yaml_dictionary,
            'xml': self.parse_xml_dictionary
        }
        
        parser = parsers.get(format_type)
        if not parser:
            raise ValueError(f"Unsupported format: {format_type}")
        
        return parser(file_path)
    
    def _parse_choices(self, choices_str: str) -> List[Dict[str, str]]:
        """Parse choice string into structured format"""
        choices = []
        
        # Handle different choice formats
        # Format: "1, Male | 2, Female | 3, Other"
        # Format: "1=Male | 2=Female | 3=Other"  
        # Format: "Male,Female,Other"
        
        if '|' in choices_str:
            parts = [p.strip() for p in choices_str.split('|')]
        else:
            parts = [p.strip() for p in choices_str.split(',')]
        
        for part in parts:
            if '=' in part:
                value, label = part.split('=', 1)
                choices.append({'value': value.strip(), 'label': label.strip()})
            elif ',' in part and len(part.split(',')) == 2:
                value, label = part.split(',', 1)
                choices.append({'value': value.strip(), 'label': label.strip()})
            else:
                # Use part as both value and label
                choices.append({'value': part, 'label': part})
        
        return choices
    
    def _parse_json_field(self, field_name: str, field_def: Union[Dict, str]) -> FieldDefinition:
        """Parse a single field from JSON definition"""
        if isinstance(field_def, str):
            field_def = {'type': field_def}
        
        field = FieldDefinition(name=field_name)
        
        # Map common JSON field properties
        field.label = field_def.get('label', field_def.get('title', field_name))
        field.description = field_def.get('description', field_def.get('help_text', ''))
        field.required = field_def.get('required', False)
        field.section = field_def.get('section', field_def.get('category', ''))
        field.field_note = field_def.get('note', field_def.get('field_note', ''))
        
        # Parse field type
        type_raw = field_def.get('type', field_def.get('field_type', '')).lower()
        field.field_type = self.field_type_mappings.get(type_raw, FieldType.UNKNOWN)
        
        # Parse choices
        choices_data = field_def.get('choices', field_def.get('options', field_def.get('enum', [])))
        if choices_data:
            if isinstance(choices_data, list):
                if all(isinstance(x, dict) for x in choices_data):
                    field.choices = choices_data
                else:
                    field.choices = [{'value': x, 'label': str(x)} for x in choices_data]
            elif isinstance(choices_data, dict):
                field.choices = [{'value': k, 'label': v} for k, v in choices_data.items()]
            
            if field.choices and field.field_type == FieldType.UNKNOWN:
                field.field_type = FieldType.CATEGORICAL
        
        # Parse validation rules
        validation = field_def.get('validation', field_def.get('constraints', {}))
        if validation:
            field.validation_rules = validation
        
        # Units
        field.units = field_def.get('units', field_def.get('unit', ''))
        
        field.confidence_score = self._calculate_field_confidence(field)
        
        return field
    
    def _calculate_field_confidence(self, field: FieldDefinition) -> float:
        """Calculate confidence score for field mapping (0-1)"""
        score = 0.0
        
        # Base score for having a name
        if field.name:
            score += 0.2
        
        # Label/description adds confidence
        if field.label and field.label != field.name:
            score += 0.2
        if field.description:
            score += 0.15
        
        # Field type detection
        if field.field_type != FieldType.UNKNOWN:
            score += 0.2
        
        # Choices/validation rules
        if field.choices:
            score += 0.15
        if field.validation_rules:
            score += 0.1
        
        return min(score, 1.0)

class IntelligentFieldMapper:
    """Intelligent field mapping using fuzzy matching and ML classification"""
    
    def __init__(self):
        self.parser = GenericDictionaryParser()
    
    def map_fields_to_standard(self, dictionary: DataDictionary) -> Dict[str, List[Tuple[str, float]]]:
        """Map dictionary fields to standard clinical field types"""
        mappings = {}
        
        for std_field, patterns in self.parser.standard_field_names.items():
            candidates = []
            
            for field_name, field_def in dictionary.fields.items():
                score = self._calculate_mapping_score(field_name, field_def, patterns, std_field)
                if score > 0.3:  # Minimum threshold
                    candidates.append((field_name, score))
            
            # Sort by score descending
            candidates.sort(key=lambda x: x[1], reverse=True)
            mappings[std_field] = candidates[:3]  # Top 3 candidates
        
        return mappings
    
    def _calculate_mapping_score(self, field_name: str, field_def: FieldDefinition, patterns: List[str], std_field: str) -> float:
        """Calculate mapping score for a field to standard pattern"""
        score = 0.0
        field_name_lower = field_name.lower()
        
        # Exact name match
        if field_name_lower in [p.lower() for p in patterns]:
            score += 0.9
        
        # Partial name match
        for pattern in patterns:
            if pattern.lower() in field_name_lower or field_name_lower in pattern.lower():
                score += 0.6
                break
        
        # Label/description matching
        label_text = (field_def.label + " " + field_def.description).lower()
        for pattern in patterns:
            if pattern.lower() in label_text:
                score += 0.3
                break
        
        # Field type compatibility
        type_compatibility = self._check_type_compatibility(field_def.field_type, std_field)
        score += type_compatibility * 0.3
        
        # Validation rules compatibility
        if self._check_validation_compatibility(field_def, std_field):
            score += 0.2
        
        return min(score, 1.0)
    
    def _check_type_compatibility(self, field_type: FieldType, std_field: str) -> float:
        """Check if field type is compatible with standard field"""
        expected_types = {
            'patient_id': [FieldType.IDENTIFIER, FieldType.TEXT],
            'age': [FieldType.INTEGER, FieldType.NUMBER],
            'sex': [FieldType.CATEGORICAL, FieldType.BINARY],
            'race': [FieldType.CATEGORICAL],
            'weight': [FieldType.NUMBER, FieldType.DECIMAL],
            'height': [FieldType.NUMBER, FieldType.DECIMAL], 
            'bmi': [FieldType.NUMBER, FieldType.DECIMAL],
            'vital_status': [FieldType.BINARY, FieldType.CATEGORICAL],
            'site_id': [FieldType.IDENTIFIER, FieldType.CATEGORICAL],
            'visit_date': [FieldType.DATE, FieldType.DATETIME]
        }
        
        if std_field in expected_types and field_type in expected_types[std_field]:
            return 1.0
        return 0.0
    
    def _check_validation_compatibility(self, field_def: FieldDefinition, std_field: str) -> bool:
        """Check if validation rules match expected standard field"""
        if std_field == 'age' and 'range' in field_def.validation_rules:
            range_rule = field_def.validation_rules['range']
            min_age = range_rule.get('min', 0)
            max_age = range_rule.get('max', 150)
            return 0 <= min_age <= 150 and 0 <= max_age <= 150
        
        if std_field == 'sex' and field_def.choices:
            choice_labels = [c.get('label', '').lower() for c in field_def.choices]
            sex_indicators = ['male', 'female', 'm', 'f', 'man', 'woman']
            return any(any(indicator in label for indicator in sex_indicators) for label in choice_labels)
        
        return False

def generate_mock_data_dictionary(format_type: str = "csv", num_fields: int = 20) -> str:
    """Generate a mock data dictionary file for testing"""
    import tempfile
    import random
    
    fields = []
    
    # Standard clinical fields
    standard_fields = [
        {"name": "record_id", "label": "Record ID", "type": "text", "identifier": True},
        {"name": "age", "label": "Age at enrollment", "type": "integer", "min": 18, "max": 90},
        {"name": "sex", "label": "Biological Sex", "type": "radio", "choices": "1, Male | 2, Female"},
        {"name": "race", "label": "Race/Ethnicity", "type": "dropdown", "choices": "1, White | 2, Black | 3, Hispanic | 4, Asian | 5, Other"},
        {"name": "weight_kg", "label": "Weight (kg)", "type": "number", "min": 30, "max": 200},
        {"name": "height_cm", "label": "Height (cm)", "type": "number", "min": 100, "max": 220},
        {"name": "vital_status", "label": "Vital Status", "type": "yesno", "choices": "0, Alive | 1, Deceased"},
        {"name": "enrollment_date", "label": "Date of Enrollment", "type": "date_ymd"},
        {"name": "site_id", "label": "Study Site", "type": "dropdown", "choices": "1, Site A | 2, Site B | 3, Site C"},
    ]
    
    # Add some random lab values
    lab_tests = ["hemoglobin", "glucose", "creatinine", "cholesterol", "bilirubin", "albumin"]
    for lab in lab_tests[:min(len(lab_tests), max(0, num_fields - len(standard_fields)))]:
        fields.append({
            "name": f"lab_{lab}",
            "label": f"{lab.title()} Level",
            "type": "number",
            "units": "mg/dL" if lab != "hemoglobin" else "g/dL"
        })
    
    # Fill remaining with standard fields
    fields.extend(standard_fields[:num_fields - len(fields)])
    
    # Generate file based on format
    if format_type == "csv":
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
        writer = csv.writer(temp_file)
        
        # Header
        writer.writerow([
            'Variable / Field Name', 'Field Label', 'Field Type', 
            'Choices, Calculations, OR Slider Labels', 'Field Note',
            'Text Validation Min', 'Text Validation Max', 'Required Field?'
        ])
        
        # Data rows
        for field in fields:
            writer.writerow([
                field['name'],
                field['label'],
                field['type'],
                field.get('choices', ''),
                field.get('note', ''),
                field.get('min', ''),
                field.get('max', ''),
                'y' if field.get('required', False) else ''
            ])
        
        temp_file.close()
        return temp_file.name
        
    elif format_type == "json":
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        
        json_dict = {
            "metadata": {
                "name": "Mock Clinical Trial Dictionary",
                "version": "1.0",
                "created": "2024-01-01"
            },
            "fields": {}
        }
        
        for field in fields:
            field_def = {
                "label": field['label'],
                "type": field['type']
            }
            
            if 'choices' in field:
                choices = []
                for choice in field['choices'].split('|'):
                    if ',' in choice:
                        value, label = choice.strip().split(',', 1)
                        choices.append({"value": value.strip(), "label": label.strip()})
                field_def['choices'] = choices
            
            if 'min' in field or 'max' in field:
                field_def['validation'] = {
                    'range': {
                        'min': field.get('min'),
                        'max': field.get('max')
                    }
                }
            
            if 'units' in field:
                field_def['units'] = field['units']
                
            json_dict['fields'][field['name']] = field_def
        
        json.dump(json_dict, temp_file, indent=2)
        temp_file.close()
        return temp_file.name
        
    else:
        raise ValueError(f"Unsupported mock format: {format_type}")

# For development/testing purposes
if __name__ == "__main__":
    # Test the parser with mock data
    parser = GenericDictionaryParser()
    mapper = IntelligentFieldMapper()
    
    # Generate and test CSV format
    csv_file = generate_mock_data_dictionary("csv")
    print(f"Generated mock CSV: {csv_file}")
    
    csv_dict = parser.parse_dictionary(csv_file)
    print(f"Parsed {len(csv_dict.fields)} fields from CSV")
    
    mappings = mapper.map_fields_to_standard(csv_dict)
    print("Field mappings:", mappings)
    
    # Clean up
    Path(csv_file).unlink()