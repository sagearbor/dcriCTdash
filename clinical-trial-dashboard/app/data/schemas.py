"""
Pandera Validation Schemas

Data validation schemas using Pandera for CDISC compliance and data quality assurance.
Ensures all clinical trial data meets regulatory standards and consistency requirements.
"""

import pandas as pd
import pandera as pa
from pandera import Column, Check, Index
from pandera.typing import DataFrame, Series
from datetime import datetime, date
from typing import Optional, Union, List

# CDISC-compliant validation schemas

class SiteSchema(pa.SchemaModel):
    """
    Site data validation schema.
    
    Validates clinical trial site information for consistency and completeness.
    """
    
    site_id: Series[str] = pa.Field(
        Check.str_matches(r"^[A-Z0-9]{3,20}$"),
        description="Unique site identifier (3-20 alphanumeric characters)"
    )
    site_name: Series[str] = pa.Field(
        Check.str_length(min_value=2, max_value=200),
        description="Site name (2-200 characters)"
    )
    country: Series[str] = pa.Field(
        Check.str_matches(r"^[A-Z]{2}$"),
        description="ISO 3166-1 alpha-2 country code"
    )
    latitude: Series[float] = pa.Field(
        ge=-90, le=90, nullable=True,
        description="Geographic latitude (-90 to 90 degrees)"
    )
    longitude: Series[float] = pa.Field(
        ge=-180, le=180, nullable=True,
        description="Geographic longitude (-180 to 180 degrees)"  
    )
    enrollment_target: Series[int] = pa.Field(
        gt=0, le=10000,
        description="Target patient enrollment (1-10000)"
    )
    
    class Config:
        strict = True
        coerce = True

class PatientSchema(pa.SchemaModel):
    """
    Patient/Subject data validation schema following CDISC USUBJID standards.
    
    Validates patient enrollment and demographic information.
    """
    
    usubjid: Series[str] = pa.Field(
        Check.str_matches(r"^[A-Z0-9]{5,50}$"),
        description="CDISC Unique Subject Identifier (5-50 characters)"
    )
    site_id: Series[str] = pa.Field(
        Check.str_matches(r"^[A-Z0-9]{3,20}$"),
        description="Reference to site identifier"
    )
    date_of_enrollment: Series[date] = pa.Field(
        ge=date(2020, 1, 1), le=date.today(),
        description="Patient enrollment date (2020-present)"
    )
    age: Series[int] = pa.Field(
        ge=0, le=120, nullable=True,
        description="Patient age at enrollment (0-120 years)"
    )
    sex: Series[str] = pa.Field(
        isin(["M", "F", "U", "UNDIFFERENTIATED"]), nullable=True,
        description="Patient sex (CDISC standard values)"
    )
    race: Series[str] = pa.Field(
        Check.str_length(max_value=50), nullable=True,
        description="Patient race category (max 50 characters)"
    )
    
    class Config:
        strict = True
        coerce = True

class VisitSchema(pa.SchemaModel):
    """
    Visit data validation schema following CDISC standards.
    
    Validates patient visit information and scheduling.
    """
    
    visit_id: Series[str] = pa.Field(
        Check.str_matches(r"^[A-Z0-9]{5,50}$"),
        description="Unique visit identifier"
    )
    usubjid: Series[str] = pa.Field(
        Check.str_matches(r"^[A-Z0-9]{5,50}$"),
        description="CDISC Unique Subject Identifier"
    )
    visit_name: Series[str] = pa.Field(
        Check.str_length(min_value=1, max_value=100),
        description="Visit name/description (1-100 characters)"
    )
    visit_num: Series[int] = pa.Field(
        ge=1, le=1000,
        description="Sequential visit number (1-1000)"
    )
    visit_date: Series[date] = pa.Field(
        ge=date(2020, 1, 1), le=date.today(),
        description="Actual visit date (2020-present)"
    )
    
    class Config:
        strict = True
        coerce = True

class LabSchema(pa.SchemaModel):
    """
    Laboratory results validation schema following CDISC LB Domain.
    
    Validates lab test results for regulatory compliance and data quality.
    """
    
    lab_id: Series[str] = pa.Field(
        Check.str_matches(r"^[A-Z0-9]{5,50}$"),
        description="Unique lab result identifier"
    )
    usubjid: Series[str] = pa.Field(
        Check.str_matches(r"^[A-Z0-9]{5,50}$"),
        description="CDISC Unique Subject Identifier"
    )
    visit_id: Series[str] = pa.Field(
        Check.str_matches(r"^[A-Z0-9]{5,50}$"),
        description="Reference to visit identifier"
    )
    lbtestcd: Series[str] = pa.Field(
        Check.str_matches(r"^[A-Z0-9]{2,20}$"),
        description="CDISC lab test code (2-20 characters)"
    )
    lbtest: Series[str] = pa.Field(
        Check.str_length(min_value=2, max_value=100),
        description="Lab test name (2-100 characters)"
    )
    lborres: Series[str] = pa.Field(
        Check.str_length(max_value=100), nullable=True,
        description="Original result as collected"
    )
    lbstresn: Series[float] = pa.Field(
        nullable=True,
        description="Standardized numeric result"
    )
    lbstresu: Series[str] = pa.Field(
        Check.str_length(max_value=20), nullable=True,
        description="Standardized result units"
    )
    lbnrind: Series[str] = pa.Field(
        isin(["NORMAL", "ABNORMAL", "HIGH", "LOW", "UNKNOWN"]), nullable=True,
        description="Reference range indicator"
    )
    collection_date: Series[date] = pa.Field(
        ge=date(2020, 1, 1), le=date.today(),
        description="Lab specimen collection date"
    )
    
    class Config:
        strict = True
        coerce = True

# Custom validation functions
def validate_cdisc_usubjid(usubjid: str) -> bool:
    """
    Validate USUBJID follows CDISC conventions.
    
    Args:
        usubjid: Unique Subject Identifier to validate
        
    Returns:
        bool: True if valid CDISC USUBJID format
    """
    import re
    # CDISC USUBJID pattern: Study-Site-Subject format
    pattern = r"^[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+$"
    return bool(re.match(pattern, usubjid))

def validate_date_range(date_col: Series, start_date: date, end_date: date) -> Series[bool]:
    """
    Validate dates fall within acceptable range.
    
    Args:
        date_col: Pandas Series of dates
        start_date: Minimum acceptable date
        end_date: Maximum acceptable date
        
    Returns:
        Series[bool]: Boolean mask of valid dates
    """
    return (date_col >= start_date) & (date_col <= end_date)

def validate_lab_reference_ranges(df: DataFrame) -> DataFrame:
    """
    Validate laboratory values against reference ranges.
    
    Args:
        df: DataFrame with lab results
        
    Returns:
        DataFrame: Validated lab results with reference range flags
    """
    # Placeholder for reference range validation logic
    # Will implement specific reference ranges for common lab tests
    return df

def validate_enrollment_timeline(patient_df: DataFrame, visit_df: DataFrame) -> List[str]:
    """
    Validate patient enrollment and visit timeline consistency.
    
    Args:
        patient_df: Patient enrollment data
        visit_df: Visit data
        
    Returns:
        List[str]: List of validation error messages
    """
    errors = []
    
    # Check that visit dates are after enrollment dates
    merged = visit_df.merge(patient_df, on="usubjid", how="left")
    invalid_visits = merged[merged["visit_date"] < merged["date_of_enrollment"]]
    
    if not invalid_visits.empty:
        errors.append(f"Found {len(invalid_visits)} visits before enrollment date")
    
    return errors

# Data quality metrics calculations
def calculate_completeness(df: DataFrame, required_columns: List[str]) -> dict:
    """
    Calculate data completeness metrics.
    
    Args:
        df: DataFrame to analyze
        required_columns: List of required column names
        
    Returns:
        dict: Completeness metrics by column
    """
    completeness = {}
    for col in required_columns:
        if col in df.columns:
            non_null_count = df[col].notna().sum()
            total_count = len(df)
            completeness[col] = non_null_count / total_count if total_count > 0 else 0.0
    
    return completeness

def detect_outliers(df: DataFrame, numeric_columns: List[str]) -> DataFrame:
    """
    Detect statistical outliers in numeric columns.
    
    Args:
        df: DataFrame to analyze
        numeric_columns: List of numeric column names
        
    Returns:
        DataFrame: Outlier detection results
    """
    outliers = []
    
    for col in numeric_columns:
        if col in df.columns and df[col].dtype in ['int64', 'float64']:
            Q1 = df[col].quantile(0.25)
            Q3 = df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outlier_mask = (df[col] < lower_bound) | (df[col] > upper_bound)
            outlier_indices = df[outlier_mask].index.tolist()
            
            for idx in outlier_indices:
                outliers.append({
                    'column': col,
                    'index': idx,
                    'value': df.loc[idx, col],
                    'lower_bound': lower_bound,
                    'upper_bound': upper_bound
                })
    
    return pd.DataFrame(outliers)

# Schema validation utility functions
def validate_dataframe(df: DataFrame, schema: pa.SchemaModel, report_errors: bool = True) -> tuple:
    """
    Validate DataFrame against Pandera schema.
    
    Args:
        df: DataFrame to validate
        schema: Pandera schema model
        report_errors: Whether to return detailed error report
        
    Returns:
        tuple: (is_valid: bool, error_report: dict)
    """
    try:
        validated_df = schema.validate(df, lazy=True)
        return True, {"status": "valid", "errors": []}
    except pa.errors.SchemaErrors as e:
        if report_errors:
            return False, {"status": "invalid", "errors": e.failure_cases.to_dict('records')}
        else:
            return False, {"status": "invalid", "errors": ["Validation failed"]}

# Export validation schemas for use in other modules
__all__ = [
    "SiteSchema", 
    "PatientSchema", 
    "VisitSchema", 
    "LabSchema",
    "validate_cdisc_usubjid",
    "validate_date_range", 
    "validate_lab_reference_ranges",
    "validate_enrollment_timeline",
    "calculate_completeness",
    "detect_outliers",
    "validate_dataframe"
]