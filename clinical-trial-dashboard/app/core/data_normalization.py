"""
Data Normalization Pipeline - Phase 5
Advanced data processing and validation system for clinical trial data

This module handles value standardization, validation, and quality scoring
for any data dictionary format.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime, date
import logging
from .data_dictionary import DataDictionary, FieldDefinition, FieldType

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Validation issue severity levels"""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class ValidationIssue:
    """Single validation issue"""
    field: str
    severity: ValidationSeverity
    message: str
    value: Any = None
    row_index: Optional[int] = None
    suggestion: Optional[str] = None

@dataclass 
class DataQualityReport:
    """Comprehensive data quality assessment"""
    total_records: int = 0
    total_fields: int = 0
    completeness_score: float = 0.0
    consistency_score: float = 0.0
    validity_score: float = 0.0
    overall_score: float = 0.0
    issues: List[ValidationIssue] = None
    field_stats: Dict[str, Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.field_stats is None:
            self.field_stats = {}

class DataNormalizer:
    """Advanced data normalization and validation engine"""
    
    def __init__(self):
        self.date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
            r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
            r'\d{1,2}/\d{1,2}/\d{4}',  # M/D/YYYY
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
        ]
        
        self.standardizations = self._init_standardizations()
        
    def _init_standardizations(self) -> Dict[str, Dict[str, Any]]:
        """Initialize standard value mappings"""
        return {
            'sex': {
                'mappings': {
                    '1': 'Male', 'male': 'Male', 'm': 'Male', 'man': 'Male',
                    '2': 'Female', 'female': 'Female', 'f': 'Female', 'woman': 'Female',
                    '0': 'Unknown', 'unknown': 'Unknown', 'u': 'Unknown', '': 'Unknown'
                },
                'canonical': ['Male', 'Female', 'Unknown']
            },
            'vital_status': {
                'mappings': {
                    '0': 'Alive', 'alive': 'Alive', 'living': 'Alive', 'a': 'Alive',
                    '1': 'Deceased', 'deceased': 'Deceased', 'dead': 'Deceased', 'd': 'Deceased',
                    '': 'Unknown', 'unknown': 'Unknown', 'u': 'Unknown'
                },
                'canonical': ['Alive', 'Deceased', 'Unknown']
            },
            'race': {
                'mappings': {
                    '1': 'White', 'white': 'White', 'caucasian': 'White',
                    '2': 'Black', 'black': 'Black', 'african american': 'Black', 'aa': 'Black',
                    '3': 'Hispanic', 'hispanic': 'Hispanic', 'latino': 'Hispanic',
                    '4': 'Asian', 'asian': 'Asian', 'pacific islander': 'Asian',
                    '5': 'Other', 'other': 'Other', 'mixed': 'Other', '': 'Unknown'
                },
                'canonical': ['White', 'Black', 'Hispanic', 'Asian', 'Other', 'Unknown']
            },
            'yesno': {
                'mappings': {
                    '1': 'Yes', 'yes': 'Yes', 'y': 'Yes', 'true': 'Yes', 'positive': 'Yes',
                    '0': 'No', 'no': 'No', 'n': 'No', 'false': 'No', 'negative': 'No',
                    '': 'Unknown', 'unknown': 'Unknown', 'u': 'Unknown'
                },
                'canonical': ['Yes', 'No', 'Unknown']
            }
        }
    
    def normalize_dataset(self, data: pd.DataFrame, dictionary: DataDictionary) -> Tuple[pd.DataFrame, DataQualityReport]:
        """Normalize entire dataset according to data dictionary"""
        logger.info(f"Normalizing dataset with {len(data)} records and {len(data.columns)} fields")
        
        normalized_data = data.copy()
        report = DataQualityReport(
            total_records=len(data),
            total_fields=len(data.columns)
        )
        
        # Process each field according to dictionary
        for field_name in data.columns:
            field_def = dictionary.get_field(field_name)
            if field_def:
                normalized_data[field_name], field_issues = self.normalize_field(
                    data[field_name], field_def
                )
                report.issues.extend(field_issues)
                
                # Calculate field statistics
                report.field_stats[field_name] = self._calculate_field_stats(
                    data[field_name], normalized_data[field_name], field_def
                )
            else:
                # Unknown field - basic normalization
                normalized_data[field_name], field_issues = self.normalize_unknown_field(
                    data[field_name], field_name
                )
                report.issues.extend(field_issues)
        
        # Calculate overall quality scores
        report.completeness_score = self._calculate_completeness_score(normalized_data)
        report.consistency_score = self._calculate_consistency_score(normalized_data, dictionary)
        report.validity_score = self._calculate_validity_score(report.issues)
        report.overall_score = (report.completeness_score + report.consistency_score + report.validity_score) / 3
        
        logger.info(f"Normalization complete. Overall quality score: {report.overall_score:.2f}")
        return normalized_data, report
    
    def normalize_field(self, series: pd.Series, field_def: FieldDefinition) -> Tuple[pd.Series, List[ValidationIssue]]:
        """Normalize a single field according to its definition"""
        issues = []
        normalized_series = series.copy()
        
        # Handle missing values first
        missing_mask = series.isnull() | (series == '') | (series == ' ')
        
        if field_def.required and missing_mask.any():
            missing_indices = series[missing_mask].index.tolist()
            for idx in missing_indices:
                issues.append(ValidationIssue(
                    field=field_def.name,
                    severity=ValidationSeverity.ERROR,
                    message="Required field is missing",
                    row_index=idx
                ))
        
        # Type-specific normalization
        if field_def.field_type == FieldType.INTEGER:
            normalized_series, type_issues = self._normalize_integer_field(normalized_series, field_def)
        elif field_def.field_type == FieldType.DECIMAL:
            normalized_series, type_issues = self._normalize_decimal_field(normalized_series, field_def)
        elif field_def.field_type == FieldType.DATE:
            normalized_series, type_issues = self._normalize_date_field(normalized_series, field_def)
        elif field_def.field_type == FieldType.DATETIME:
            normalized_series, type_issues = self._normalize_datetime_field(normalized_series, field_def)
        elif field_def.field_type == FieldType.CATEGORICAL:
            normalized_series, type_issues = self._normalize_categorical_field(normalized_series, field_def)
        elif field_def.field_type == FieldType.BINARY:
            normalized_series, type_issues = self._normalize_binary_field(normalized_series, field_def)
        elif field_def.field_type == FieldType.BOOLEAN:
            normalized_series, type_issues = self._normalize_boolean_field(normalized_series, field_def)
        elif field_def.field_type == FieldType.EMAIL:
            normalized_series, type_issues = self._normalize_email_field(normalized_series, field_def)
        elif field_def.field_type == FieldType.PHONE:
            normalized_series, type_issues = self._normalize_phone_field(normalized_series, field_def)
        else:
            normalized_series, type_issues = self._normalize_text_field(normalized_series, field_def)
        
        issues.extend(type_issues)
        
        # Validation rules
        validation_issues = self._apply_validation_rules(normalized_series, field_def)
        issues.extend(validation_issues)
        
        return normalized_series, issues
    
    def normalize_unknown_field(self, series: pd.Series, field_name: str) -> Tuple[pd.Series, List[ValidationIssue]]:
        """Basic normalization for fields not in dictionary"""
        issues = []
        normalized_series = series.copy()
        
        # Try to infer type and apply basic normalization
        inferred_type = self._infer_field_type(series)
        
        if inferred_type == FieldType.INTEGER:
            try:
                normalized_series = pd.to_numeric(series, errors='coerce').astype('Int64')
                invalid_mask = series.notna() & normalized_series.isna()
                for idx in series[invalid_mask].index:
                    issues.append(ValidationIssue(
                        field=field_name,
                        severity=ValidationSeverity.WARNING,
                        message="Could not convert to integer",
                        value=series.iloc[idx],
                        row_index=idx
                    ))
            except Exception as e:
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=ValidationSeverity.ERROR,
                    message=f"Integer conversion failed: {e}"
                ))
        
        elif inferred_type == FieldType.DECIMAL:
            try:
                normalized_series = pd.to_numeric(series, errors='coerce')
                invalid_mask = series.notna() & normalized_series.isna()
                for idx in series[invalid_mask].index:
                    issues.append(ValidationIssue(
                        field=field_name,
                        severity=ValidationSeverity.WARNING,
                        message="Could not convert to number",
                        value=series.iloc[idx],
                        row_index=idx
                    ))
            except Exception as e:
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=ValidationSeverity.ERROR,
                    message=f"Numeric conversion failed: {e}"
                ))
        
        elif inferred_type == FieldType.DATE:
            try:
                normalized_series = pd.to_datetime(series, errors='coerce')
                invalid_mask = series.notna() & normalized_series.isna()
                for idx in series[invalid_mask].index:
                    issues.append(ValidationIssue(
                        field=field_name,
                        severity=ValidationSeverity.WARNING,
                        message="Could not parse date",
                        value=series.iloc[idx],
                        row_index=idx
                    ))
            except Exception as e:
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=ValidationSeverity.ERROR,
                    message=f"Date parsing failed: {e}"
                ))
        
        return normalized_series, issues
    
    def _normalize_integer_field(self, series: pd.Series, field_def: FieldDefinition) -> Tuple[pd.Series, List[ValidationIssue]]:
        """Normalize integer field"""
        issues = []
        try:
            # Convert to numeric, preserving NaN
            normalized = pd.to_numeric(series, errors='coerce')
            
            # Check for conversion failures
            invalid_mask = series.notna() & normalized.isna()
            for idx in series[invalid_mask].index:
                issues.append(ValidationIssue(
                    field=field_def.name,
                    severity=ValidationSeverity.WARNING,
                    message="Value could not be converted to integer",
                    value=series.iloc[idx],
                    row_index=idx,
                    suggestion="Check for non-numeric characters"
                ))
            
            # Round to integers and convert to nullable integer type
            normalized = normalized.round().astype('Int64')
            
        except Exception as e:
            issues.append(ValidationIssue(
                field=field_def.name,
                severity=ValidationSeverity.ERROR,
                message=f"Integer normalization failed: {e}"
            ))
            normalized = series
        
        return normalized, issues
    
    def _normalize_decimal_field(self, series: pd.Series, field_def: FieldDefinition) -> Tuple[pd.Series, List[ValidationIssue]]:
        """Normalize decimal/float field"""
        issues = []
        try:
            normalized = pd.to_numeric(series, errors='coerce')
            
            # Check for conversion failures
            invalid_mask = series.notna() & normalized.isna()
            for idx in series[invalid_mask].index:
                issues.append(ValidationIssue(
                    field=field_def.name,
                    severity=ValidationSeverity.WARNING,
                    message="Value could not be converted to number",
                    value=series.iloc[idx],
                    row_index=idx,
                    suggestion="Check for non-numeric characters or formatting"
                ))
            
        except Exception as e:
            issues.append(ValidationIssue(
                field=field_def.name,
                severity=ValidationSeverity.ERROR,
                message=f"Decimal normalization failed: {e}"
            ))
            normalized = series
        
        return normalized, issues
    
    def _normalize_date_field(self, series: pd.Series, field_def: FieldDefinition) -> Tuple[pd.Series, List[ValidationIssue]]:
        """Normalize date field"""
        issues = []
        try:
            normalized = pd.to_datetime(series, errors='coerce')
            
            # Check for conversion failures
            invalid_mask = series.notna() & normalized.isna()
            for idx in series[invalid_mask].index:
                issues.append(ValidationIssue(
                    field=field_def.name,
                    severity=ValidationSeverity.WARNING,
                    message="Value could not be parsed as date",
                    value=series.iloc[idx],
                    row_index=idx,
                    suggestion="Use format YYYY-MM-DD"
                ))
            
            # Check for unreasonable dates
            current_year = datetime.now().year
            unreasonable_mask = normalized.notna() & (
                (normalized.dt.year < 1900) | (normalized.dt.year > current_year + 10)
            )
            for idx in series[unreasonable_mask].index:
                issues.append(ValidationIssue(
                    field=field_def.name,
                    severity=ValidationSeverity.WARNING,
                    message="Date seems unreasonable",
                    value=series.iloc[idx],
                    row_index=idx,
                    suggestion=f"Check year is between 1900 and {current_year + 10}"
                ))
            
        except Exception as e:
            issues.append(ValidationIssue(
                field=field_def.name,
                severity=ValidationSeverity.ERROR,
                message=f"Date normalization failed: {e}"
            ))
            normalized = series
        
        return normalized, issues
    
    def _normalize_datetime_field(self, series: pd.Series, field_def: FieldDefinition) -> Tuple[pd.Series, List[ValidationIssue]]:
        """Normalize datetime field"""
        # Similar to date but preserve time component
        return self._normalize_date_field(series, field_def)
    
    def _normalize_categorical_field(self, series: pd.Series, field_def: FieldDefinition) -> Tuple[pd.Series, List[ValidationIssue]]:
        """Normalize categorical field using choice mappings"""
        issues = []
        normalized = series.copy()
        
        if field_def.choices:
            # Create mapping from choices
            choice_mapping = {}
            valid_values = []
            
            for choice in field_def.choices:
                value = choice.get('value', '')
                label = choice.get('label', value)
                choice_mapping[str(value).lower()] = label
                choice_mapping[str(label).lower()] = label
                valid_values.append(label)
            
            # Apply mapping
            normalized_values = []
            for idx, val in series.items():
                if pd.isna(val) or val == '':
                    normalized_values.append(val)
                else:
                    mapped_val = choice_mapping.get(str(val).lower())
                    if mapped_val:
                        normalized_values.append(mapped_val)
                    else:
                        normalized_values.append(val)
                        issues.append(ValidationIssue(
                            field=field_def.name,
                            severity=ValidationSeverity.WARNING,
                            message=f"Unknown categorical value: {val}",
                            value=val,
                            row_index=idx,
                            suggestion=f"Valid values: {', '.join(valid_values)}"
                        ))
            
            normalized = pd.Series(normalized_values, index=series.index)
        
        return normalized, issues
    
    def _normalize_binary_field(self, series: pd.Series, field_def: FieldDefinition) -> Tuple[pd.Series, List[ValidationIssue]]:
        """Normalize binary field (0/1, Yes/No, etc.)"""
        issues = []
        
        # Determine the binary mapping based on field name or choices
        field_name_lower = field_def.name.lower()
        
        if 'sex' in field_name_lower or 'gender' in field_name_lower:
            mapping = self.standardizations['sex']['mappings']
        elif 'vital' in field_name_lower or 'death' in field_name_lower:
            mapping = self.standardizations['vital_status']['mappings']
        elif field_def.choices and len(field_def.choices) == 2:
            # Use the choices provided
            choice_vals = [c.get('value', '') for c in field_def.choices]
            choice_labels = [c.get('label', '') for c in field_def.choices]
            mapping = {}
            for val, label in zip(choice_vals, choice_labels):
                mapping[str(val).lower()] = label
                mapping[str(label).lower()] = label
        else:
            # Default yes/no mapping
            mapping = self.standardizations['yesno']['mappings']
        
        # Apply mapping
        normalized_values = []
        for idx, val in series.items():
            if pd.isna(val) or val == '':
                normalized_values.append(val)
            else:
                mapped_val = mapping.get(str(val).lower())
                if mapped_val:
                    normalized_values.append(mapped_val)
                else:
                    normalized_values.append(val)
                    issues.append(ValidationIssue(
                        field=field_def.name,
                        severity=ValidationSeverity.WARNING,
                        message=f"Unknown binary value: {val}",
                        value=val,
                        row_index=idx,
                        suggestion=f"Expected values: {', '.join(mapping.keys())}"
                    ))
        
        normalized = pd.Series(normalized_values, index=series.index)
        return normalized, issues
    
    def _normalize_boolean_field(self, series: pd.Series, field_def: FieldDefinition) -> Tuple[pd.Series, List[ValidationIssue]]:
        """Normalize boolean field"""
        issues = []
        
        # Convert to boolean
        true_values = ['true', '1', 'yes', 'y', 'on', 't']
        false_values = ['false', '0', 'no', 'n', 'off', 'f']
        
        normalized_values = []
        for idx, val in series.items():
            if pd.isna(val) or val == '':
                normalized_values.append(val)
            else:
                val_lower = str(val).lower()
                if val_lower in true_values:
                    normalized_values.append(True)
                elif val_lower in false_values:
                    normalized_values.append(False)
                else:
                    normalized_values.append(val)
                    issues.append(ValidationIssue(
                        field=field_def.name,
                        severity=ValidationSeverity.WARNING,
                        message=f"Could not convert to boolean: {val}",
                        value=val,
                        row_index=idx,
                        suggestion="Use true/false, 1/0, or yes/no"
                    ))
        
        normalized = pd.Series(normalized_values, index=series.index)
        return normalized, issues
    
    def _normalize_email_field(self, series: pd.Series, field_def: FieldDefinition) -> Tuple[pd.Series, List[ValidationIssue]]:
        """Normalize and validate email field"""
        issues = []
        normalized = series.str.lower().str.strip()  # Emails are case-insensitive
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for idx, val in normalized.items():
            if pd.notna(val) and val != '' and not re.match(email_pattern, val):
                issues.append(ValidationIssue(
                    field=field_def.name,
                    severity=ValidationSeverity.WARNING,
                    message="Invalid email format",
                    value=series.iloc[idx],
                    row_index=idx,
                    suggestion="Use format: user@domain.com"
                ))
        
        return normalized, issues
    
    def _normalize_phone_field(self, series: pd.Series, field_def: FieldDefinition) -> Tuple[pd.Series, List[ValidationIssue]]:
        """Normalize phone number field"""
        issues = []
        
        # Remove common phone number formatting
        normalized = series.astype(str).str.replace(r'[^\d]', '', regex=True)
        
        for idx, val in normalized.items():
            if pd.notna(val) and val != '' and len(val) not in [10, 11]:  # US phone numbers
                issues.append(ValidationIssue(
                    field=field_def.name,
                    severity=ValidationSeverity.WARNING,
                    message=f"Unusual phone number length: {len(val)} digits",
                    value=series.iloc[idx],
                    row_index=idx,
                    suggestion="US numbers should be 10-11 digits"
                ))
        
        # Reformat for consistency (XXX-XXX-XXXX)
        formatted_values = []
        for val in normalized:
            if pd.notna(val) and val != '' and len(val) >= 10:
                if len(val) == 11 and val.startswith('1'):
                    val = val[1:]  # Remove country code
                if len(val) == 10:
                    formatted_values.append(f"{val[:3]}-{val[3:6]}-{val[6:]}")
                else:
                    formatted_values.append(val)
            else:
                formatted_values.append(val if pd.notna(val) else '')
        
        normalized = pd.Series(formatted_values, index=series.index)
        return normalized, issues
    
    def _normalize_text_field(self, series: pd.Series, field_def: FieldDefinition) -> Tuple[pd.Series, List[ValidationIssue]]:
        """Basic text field normalization"""
        issues = []
        
        # Basic text cleaning
        normalized = series.astype(str).str.strip()
        
        # Check for length constraints if specified
        if 'max_length' in field_def.validation_rules:
            max_len = field_def.validation_rules['max_length']
            too_long_mask = normalized.str.len() > max_len
            
            for idx in series[too_long_mask].index:
                issues.append(ValidationIssue(
                    field=field_def.name,
                    severity=ValidationSeverity.WARNING,
                    message=f"Text exceeds maximum length of {max_len} characters",
                    value=series.iloc[idx],
                    row_index=idx,
                    suggestion=f"Truncate to {max_len} characters"
                ))
        
        if 'min_length' in field_def.validation_rules:
            min_len = field_def.validation_rules['min_length']
            too_short_mask = (normalized.str.len() < min_len) & (normalized != '')
            
            for idx in series[too_short_mask].index:
                issues.append(ValidationIssue(
                    field=field_def.name,
                    severity=ValidationSeverity.WARNING,
                    message=f"Text is shorter than minimum length of {min_len} characters",
                    value=series.iloc[idx],
                    row_index=idx
                ))
        
        return normalized, issues
    
    def _apply_validation_rules(self, series: pd.Series, field_def: FieldDefinition) -> List[ValidationIssue]:
        """Apply validation rules to normalized field"""
        issues = []
        
        # Range validation
        if 'range' in field_def.validation_rules:
            range_rule = field_def.validation_rules['range']
            min_val = range_rule.get('min')
            max_val = range_rule.get('max')
            
            if min_val is not None:
                try:
                    numeric_series = pd.to_numeric(series, errors='coerce')
                    below_min = (numeric_series < min_val) & numeric_series.notna()
                    for idx in series[below_min].index:
                        issues.append(ValidationIssue(
                            field=field_def.name,
                            severity=ValidationSeverity.WARNING,
                            message=f"Value {series.iloc[idx]} is below minimum {min_val}",
                            value=series.iloc[idx],
                            row_index=idx
                        ))
                except:
                    pass  # Skip range validation for non-numeric data
            
            if max_val is not None:
                try:
                    numeric_series = pd.to_numeric(series, errors='coerce')
                    above_max = (numeric_series > max_val) & numeric_series.notna()
                    for idx in series[above_max].index:
                        issues.append(ValidationIssue(
                            field=field_def.name,
                            severity=ValidationSeverity.WARNING,
                            message=f"Value {series.iloc[idx]} is above maximum {max_val}",
                            value=series.iloc[idx],
                            row_index=idx
                        ))
                except:
                    pass  # Skip range validation for non-numeric data
        
        # Regex validation
        if 'regex' in field_def.validation_rules:
            pattern = field_def.validation_rules['regex']
            try:
                invalid_mask = series.notna() & ~series.astype(str).str.match(pattern)
                for idx in series[invalid_mask].index:
                    issues.append(ValidationIssue(
                        field=field_def.name,
                        severity=ValidationSeverity.WARNING,
                        message=f"Value does not match required pattern: {pattern}",
                        value=series.iloc[idx],
                        row_index=idx
                    ))
            except Exception as e:
                issues.append(ValidationIssue(
                    field=field_def.name,
                    severity=ValidationSeverity.ERROR,
                    message=f"Regex validation failed: {e}"
                ))
        
        # Unique constraint
        if field_def.validation_rules.get('unique', False):
            duplicates = series[series.duplicated() & series.notna()]
            for idx in duplicates.index:
                issues.append(ValidationIssue(
                    field=field_def.name,
                    severity=ValidationSeverity.ERROR,
                    message=f"Duplicate value found: {series.iloc[idx]}",
                    value=series.iloc[idx],
                    row_index=idx,
                    suggestion="Values in this field must be unique"
                ))
        
        return issues
    
    def _infer_field_type(self, series: pd.Series) -> FieldType:
        """Infer field type from data"""
        # Remove missing values for analysis
        clean_series = series.dropna()
        if clean_series.empty:
            return FieldType.TEXT
        
        # Try integer
        try:
            pd.to_numeric(clean_series, errors='raise')
            # Check if all values are integers
            if all(float(x).is_integer() for x in clean_series if pd.notna(x)):
                return FieldType.INTEGER
            else:
                return FieldType.DECIMAL
        except:
            pass
        
        # Try date
        try:
            pd.to_datetime(clean_series, errors='raise')
            return FieldType.DATE
        except:
            pass
        
        # Check if binary (only 2 unique values)
        unique_vals = clean_series.nunique()
        if unique_vals == 2:
            return FieldType.BINARY
        elif unique_vals <= 10:  # Small number of categories
            return FieldType.CATEGORICAL
        
        return FieldType.TEXT
    
    def _calculate_completeness_score(self, data: pd.DataFrame) -> float:
        """Calculate data completeness score"""
        total_cells = data.size
        if total_cells == 0:
            return 1.0
        
        missing_cells = data.isnull().sum().sum()
        return 1.0 - (missing_cells / total_cells)
    
    def _calculate_consistency_score(self, data: pd.DataFrame, dictionary: DataDictionary) -> float:
        """Calculate data consistency score"""
        consistency_scores = []
        
        for field_name in data.columns:
            field_def = dictionary.get_field(field_name)
            if field_def and field_def.field_type != FieldType.UNKNOWN:
                # Check type consistency
                series = data[field_name].dropna()
                if not series.empty:
                    expected_type = field_def.field_type
                    actual_type = self._infer_field_type(series)
                    
                    # Score based on type compatibility
                    if actual_type == expected_type:
                        consistency_scores.append(1.0)
                    elif self._types_compatible(actual_type, expected_type):
                        consistency_scores.append(0.7)
                    else:
                        consistency_scores.append(0.3)
        
        return np.mean(consistency_scores) if consistency_scores else 0.5
    
    def _calculate_validity_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate validity score based on validation issues"""
        if not issues:
            return 1.0
        
        # Weight by severity
        severity_weights = {
            ValidationSeverity.INFO: 0.05,
            ValidationSeverity.WARNING: 0.2,
            ValidationSeverity.ERROR: 0.5,
            ValidationSeverity.CRITICAL: 1.0
        }
        
        total_penalty = sum(severity_weights[issue.severity] for issue in issues)
        max_penalty = len(issues) * severity_weights[ValidationSeverity.CRITICAL]
        
        return 1.0 - (total_penalty / max_penalty) if max_penalty > 0 else 1.0
    
    def _calculate_field_stats(self, original: pd.Series, normalized: pd.Series, field_def: FieldDefinition) -> Dict[str, Any]:
        """Calculate detailed statistics for a field"""
        stats = {
            'total_count': len(original),
            'missing_count': original.isnull().sum(),
            'unique_count': original.nunique(),
            'completeness': 1.0 - (original.isnull().sum() / len(original)) if len(original) > 0 else 0.0
        }
        
        # Type-specific stats
        if field_def.field_type in [FieldType.INTEGER, FieldType.DECIMAL, FieldType.NUMBER]:
            numeric_data = pd.to_numeric(normalized, errors='coerce').dropna()
            if not numeric_data.empty:
                stats.update({
                    'mean': float(numeric_data.mean()),
                    'std': float(numeric_data.std()),
                    'min': float(numeric_data.min()),
                    'max': float(numeric_data.max()),
                    'median': float(numeric_data.median())
                })
        
        elif field_def.field_type == FieldType.CATEGORICAL:
            value_counts = normalized.value_counts()
            stats['value_distribution'] = value_counts.to_dict()
            stats['most_common'] = value_counts.index[0] if not value_counts.empty else None
        
        elif field_def.field_type == FieldType.TEXT:
            text_data = normalized.dropna().astype(str)
            if not text_data.empty:
                stats.update({
                    'avg_length': float(text_data.str.len().mean()),
                    'max_length': int(text_data.str.len().max()),
                    'min_length': int(text_data.str.len().min())
                })
        
        return stats
    
    def _types_compatible(self, actual: FieldType, expected: FieldType) -> bool:
        """Check if two field types are compatible"""
        compatible_groups = [
            {FieldType.INTEGER, FieldType.DECIMAL, FieldType.NUMBER},
            {FieldType.DATE, FieldType.DATETIME},
            {FieldType.BINARY, FieldType.BOOLEAN, FieldType.CATEGORICAL},
            {FieldType.TEXT, FieldType.IDENTIFIER}
        ]
        
        for group in compatible_groups:
            if actual in group and expected in group:
                return True
        
        return False

# For development/testing purposes
if __name__ == "__main__":
    # Test normalization with mock data
    from .data_dictionary import generate_mock_data_dictionary, GenericDictionaryParser
    
    # Generate test dictionary and data
    parser = GenericDictionaryParser()
    normalizer = DataNormalizer()
    
    csv_file = generate_mock_data_dictionary("csv", 10)
    dictionary = parser.parse_dictionary(csv_file)
    
    # Create some messy test data
    test_data = pd.DataFrame({
        'record_id': ['001', '002', '003', '', '005'],
        'age': ['25', '30.5', 'unknown', '45', '22'],
        'sex': ['1', 'Female', 'M', '2', 'male'],
        'weight_kg': ['70.5', '85', 'heavy', '60.2', ''],
        'enrollment_date': ['2024-01-15', '01/20/2024', 'yesterday', '2024-02-01', '']
    })
    
    normalized_data, report = normalizer.normalize_dataset(test_data, dictionary)
    print(f"Normalized data quality score: {report.overall_score:.2f}")
    print(f"Found {len(report.issues)} validation issues")