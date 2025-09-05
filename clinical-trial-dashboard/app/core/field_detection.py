"""
Phase 4: Statistical Field Detection System

Implements basic statistical correlation analysis to automatically detect 
the semantic meaning of ambiguous clinical data fields by analyzing their
relationships with known fields.

Example: Detecting that binary column "s_01" represents sex/gender by analyzing 
correlations with height, weight, and lab values.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from scipy import stats
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class FieldDetectionResult:
    """Result of field detection analysis."""
    field_name: str
    predicted_type: str
    confidence: float
    evidence: Dict[str, Any]
    correlations: Dict[str, float]
    statistical_tests: Dict[str, Dict[str, float]]

class StatisticalFieldDetector:
    """
    Detects semantic field types using statistical correlation analysis.
    
    This implements the simpler approach discussed for Phase 4 - using 
    statistical relationships to infer field meaning without complex ML.
    """
    
    def __init__(self):
        """Initialize the field detector with known clinical patterns."""
        
        # Define expected patterns for common clinical fields
        self.known_patterns = {
            'sex': {
                'binary_values': True,
                'height_correlation': True,  # Males typically taller
                'weight_correlation': True,  # Males typically heavier
                'muscle_mass_correlation': True,  # Males higher muscle mass
                'hemoglobin_correlation': True,  # Males higher hemoglobin
                'expected_distribution': [0.45, 0.55]  # Roughly equal split
            },
            'vital_status': {
                'binary_values': True,
                'age_correlation': True,  # Mortality increases with age
                'lab_correlations': True,  # Multiple lab abnormalities
                'expected_distribution': [0.95, 0.05]  # Most alive
            },
            'treatment_group': {
                'binary_values': True,
                'outcome_correlation': True,  # Treatment affects outcomes
                'expected_distribution': [0.5, 0.5]  # Randomized
            },
            'disease_stage': {
                'categorical_values': True,
                'ordered': True,
                'lab_correlations': True,  # Stage affects lab values
                'survival_correlation': True
            }
        }
        
        # Clinical knowledge about expected relationships
        self.clinical_knowledge = {
            'sex_height_diff': 10.0,  # cm average difference
            'sex_weight_diff': 15.0,  # kg average difference  
            'sex_hemoglobin_diff': 2.0,  # g/dL average difference
            'minimum_correlation': 0.3,  # Minimum correlation to consider
            'significant_pvalue': 0.05  # P-value threshold
        }
    
    def analyze_dataset(self, data: pd.DataFrame) -> List[FieldDetectionResult]:
        """
        Analyze a dataset to detect field types for ambiguous columns.
        
        Args:
            data: DataFrame containing clinical data
            
        Returns:
            List of field detection results for ambiguous columns
        """
        results = []
        
        # Identify ambiguous columns (short names, coded values, etc.)
        ambiguous_columns = self._identify_ambiguous_columns(data)
        
        # Identify known/anchor columns  
        anchor_columns = self._identify_anchor_columns(data)
        
        logger.info(f"Found {len(ambiguous_columns)} ambiguous columns: {ambiguous_columns}")
        logger.info(f"Found {len(anchor_columns)} anchor columns: {list(anchor_columns.keys())}")
        
        # Analyze each ambiguous column
        for col in ambiguous_columns:
            result = self._analyze_field(data, col, anchor_columns)
            if result:
                results.append(result)
        
        return results
    
    def _identify_ambiguous_columns(self, data: pd.DataFrame) -> List[str]:
        """Identify columns that need semantic type detection."""
        ambiguous_columns = []
        
        for col in data.columns:
            # Skip obviously named columns
            obvious_patterns = ['patient', 'subject', 'site', 'date', 'age', 'height', 'weight', 
                              'sex', 'gender', 'name', 'id', 'visit', 'hemoglobin', 'glucose']
            
            if any(pattern in col.lower() for pattern in obvious_patterns):
                continue
            
            # Look for cryptic column names
            if (len(col) <= 5 or  # Short names like "s_01"
                col.isnumeric() or  # Numeric column names
                col.count('_') > col.count(' ') or  # Underscore naming
                col.isupper() or  # All caps coding
                not col.replace('_', '').replace('-', '').isalnum()):  # Contains special chars
                
                ambiguous_columns.append(col)
        
        return ambiguous_columns
    
    def _identify_anchor_columns(self, data: pd.DataFrame) -> Dict[str, str]:
        """Identify columns with known semantic types to use as anchors."""
        anchor_columns = {}
        
        # Pattern matching for common clinical fields
        patterns = {
            'height': ['height', 'ht', 'tall'],
            'weight': ['weight', 'wt', 'mass'],  
            'age': ['age', 'years'],
            'sex': ['sex', 'gender', 'male', 'female'],
            'hemoglobin': ['hgb', 'hemoglobin', 'hb'],
            'glucose': ['glucose', 'gluc', 'sugar'],
            'creatinine': ['creatinine', 'creat', 'scr'],
            'patient_id': ['patient', 'subject', 'usubjid', 'patid'],
            'site_id': ['site', 'center', 'location']
        }
        
        for col in data.columns:
            col_lower = col.lower()
            for field_type, pattern_list in patterns.items():
                if any(pattern in col_lower for pattern in pattern_list):
                    anchor_columns[col] = field_type
                    break
        
        return anchor_columns
    
    def _analyze_field(self, data: pd.DataFrame, field_name: str, 
                      anchor_columns: Dict[str, str]) -> Optional[FieldDetectionResult]:
        """
        Analyze a single field to determine its semantic type.
        
        This is the core algorithm that implements the statistical correlation
        approach described in your example.
        """
        field_data = data[field_name].dropna()
        
        if len(field_data) < 10:  # Need sufficient data
            return None
        
        # Check if field is binary (key requirement for sex detection)
        is_binary = len(field_data.unique()) == 2
        
        if is_binary:
            return self._analyze_binary_field(data, field_name, anchor_columns)
        else:
            return self._analyze_categorical_field(data, field_name, anchor_columns)
    
    def _analyze_binary_field(self, data: pd.DataFrame, field_name: str,
                             anchor_columns: Dict[str, str]) -> Optional[FieldDetectionResult]:
        """
        Analyze a binary field - prime candidate for sex detection.
        
        This implements your specific example: detecting s_01 as sex by analyzing
        correlations with height, weight, and lab values.
        """
        field_data = data[field_name].dropna()
        unique_values = sorted(field_data.unique())
        
        # Get distribution
        value_counts = field_data.value_counts(normalize=True)
        distribution = [value_counts[val] for val in unique_values]
        
        correlations = {}
        statistical_tests = {}
        evidence = {
            'unique_values': unique_values,
            'distribution': distribution,
            'sample_size': len(field_data)
        }
        
        # Test for sex pattern - the main example from your use case
        sex_evidence = self._test_sex_pattern(data, field_name, anchor_columns)
        
        if sex_evidence['confidence'] > 0.7:
            return FieldDetectionResult(
                field_name=field_name,
                predicted_type='sex',
                confidence=sex_evidence['confidence'],
                evidence=evidence,
                correlations=sex_evidence['correlations'],
                statistical_tests=sex_evidence['tests']
            )
        
        # Test for other binary patterns
        vital_status_evidence = self._test_vital_status_pattern(data, field_name, anchor_columns)
        
        if vital_status_evidence['confidence'] > 0.6:
            return FieldDetectionResult(
                field_name=field_name,
                predicted_type='vital_status',
                confidence=vital_status_evidence['confidence'],
                evidence=evidence,
                correlations=vital_status_evidence['correlations'],
                statistical_tests=vital_status_evidence['tests']
            )
        
        # Test for treatment group
        treatment_evidence = self._test_treatment_pattern(data, field_name, anchor_columns)
        
        if treatment_evidence['confidence'] > 0.5:
            return FieldDetectionResult(
                field_name=field_name,
                predicted_type='treatment_group',
                confidence=treatment_evidence['confidence'],
                evidence=evidence,
                correlations=treatment_evidence['correlations'],  
                statistical_tests=treatment_evidence['tests']
            )
        
        return None
    
    def _test_sex_pattern(self, data: pd.DataFrame, field_name: str,
                         anchor_columns: Dict[str, str]) -> Dict[str, Any]:
        """
        Test if a binary field represents sex/gender.
        
        This implements your specific example:
        - Binary 0/1 with roughly equal distribution
        - Group with 1 has higher height, lower estrogen, greater muscle mass
        - Correlates with hemoglobin levels (males higher)
        """
        field_data = data[field_name].dropna()
        unique_values = sorted(field_data.unique())
        
        correlations = {}
        tests = {}
        confidence = 0.0
        
        # Check distribution is roughly balanced (40-60% split acceptable)
        value_counts = field_data.value_counts(normalize=True)
        distribution_balance = min(value_counts) / max(value_counts)
        
        if distribution_balance < 0.3:  # Too unbalanced for sex
            return {'confidence': 0.0, 'correlations': {}, 'tests': {}}
        
        confidence += 0.2  # Base points for balanced distribution
        
        # Test height correlation (key sex indicator)
        height_cols = [col for col, field_type in anchor_columns.items() if field_type == 'height']
        if height_cols:
            height_col = height_cols[0]
            height_test = self._test_group_difference(data, field_name, height_col)
            
            correlations['height'] = height_test['correlation']
            tests['height'] = height_test
            
            # Males typically taller - expect positive correlation if 1=Male
            if (height_test['significant'] and height_test['correlation'] > 0.3 and
                height_test['group_difference'] > 5.0):  # 5cm+ difference
                confidence += 0.3
        
        # Test weight correlation
        weight_cols = [col for col, field_type in anchor_columns.items() if field_type == 'weight']
        if weight_cols:
            weight_col = weight_cols[0]
            weight_test = self._test_group_difference(data, field_name, weight_col)
            
            correlations['weight'] = weight_test['correlation']
            tests['weight'] = weight_test
            
            if (weight_test['significant'] and weight_test['correlation'] > 0.2 and
                weight_test['group_difference'] > 8.0):  # 8kg+ difference
                confidence += 0.2
        
        # Test hemoglobin correlation (males typically higher)
        hgb_cols = [col for col, field_type in anchor_columns.items() if field_type == 'hemoglobin']
        if hgb_cols:
            hgb_col = hgb_cols[0]
            hgb_test = self._test_group_difference(data, field_name, hgb_col)
            
            correlations['hemoglobin'] = hgb_test['correlation']
            tests['hemoglobin'] = hgb_test
            
            if (hgb_test['significant'] and hgb_test['correlation'] > 0.3 and
                hgb_test['group_difference'] > 1.0):  # 1+ g/dL difference
                confidence += 0.3
        
        return {
            'confidence': min(confidence, 1.0),
            'correlations': correlations,
            'tests': tests
        }
    
    def _test_vital_status_pattern(self, data: pd.DataFrame, field_name: str,
                                  anchor_columns: Dict[str, str]) -> Dict[str, Any]:
        """Test if a binary field represents vital status (alive/dead)."""
        field_data = data[field_name].dropna()
        correlations = {}
        tests = {}
        confidence = 0.0
        
        # Vital status should be very unbalanced (most patients alive)
        value_counts = field_data.value_counts(normalize=True)
        max_proportion = max(value_counts)
        
        if max_proportion > 0.9:  # 90%+ in one category suggests vital status
            confidence += 0.3
        
        # Test age correlation (older patients more likely to die)
        age_cols = [col for col, field_type in anchor_columns.items() if field_type == 'age']
        if age_cols:
            age_col = age_cols[0]
            age_test = self._test_group_difference(data, field_name, age_col)
            
            correlations['age'] = age_test['correlation']
            tests['age'] = age_test
            
            if age_test['significant'] and abs(age_test['correlation']) > 0.2:
                confidence += 0.4
        
        return {
            'confidence': min(confidence, 1.0),
            'correlations': correlations,
            'tests': tests
        }
    
    def _test_treatment_pattern(self, data: pd.DataFrame, field_name: str,
                               anchor_columns: Dict[str, str]) -> Dict[str, Any]:
        """Test if a binary field represents treatment group assignment."""
        field_data = data[field_name].dropna()
        correlations = {}
        tests = {}
        confidence = 0.0
        
        # Treatment groups should be balanced (randomized)
        value_counts = field_data.value_counts(normalize=True)
        balance = min(value_counts) / max(value_counts)
        
        if balance > 0.4:  # Well balanced suggests randomization
            confidence += 0.3
        
        # Treatment might correlate with outcomes/lab improvements
        # This would need outcome data to properly test
        
        return {
            'confidence': min(confidence, 1.0),
            'correlations': correlations,
            'tests': tests
        }
    
    def _test_group_difference(self, data: pd.DataFrame, group_col: str, 
                             value_col: str) -> Dict[str, Any]:
        """
        Test for significant differences between groups in a continuous variable.
        
        This is the core statistical test that identifies patterns like:
        - Higher height in one group vs another (suggesting sex)
        - Different lab values between groups
        """
        merged_data = data[[group_col, value_col]].dropna()
        
        if len(merged_data) < 10:
            return {'significant': False, 'correlation': 0.0, 'p_value': 1.0, 'group_difference': 0.0}
        
        groups = merged_data[group_col].unique()
        if len(groups) != 2:
            return {'significant': False, 'correlation': 0.0, 'p_value': 1.0, 'group_difference': 0.0}
        
        group1_data = merged_data[merged_data[group_col] == groups[0]][value_col]
        group2_data = merged_data[merged_data[group_col] == groups[1]][value_col]
        
        # Perform t-test
        try:
            t_stat, p_value = stats.ttest_ind(group1_data, group2_data, equal_var=False)
            
            # Calculate correlation coefficient
            correlation, _ = stats.pearsonr(merged_data[group_col], merged_data[value_col])
            
            # Calculate group difference
            group1_mean = group1_data.mean()
            group2_mean = group2_data.mean()
            group_difference = abs(group2_mean - group1_mean)
            
            return {
                'significant': p_value < self.clinical_knowledge['significant_pvalue'],
                'correlation': correlation,
                'p_value': p_value,
                't_statistic': t_stat,
                'group_difference': group_difference,
                'group1_mean': group1_mean,
                'group2_mean': group2_mean,
                'group1_size': len(group1_data),
                'group2_size': len(group2_data)
            }
            
        except Exception as e:
            logger.error(f"Error in statistical test: {e}")
            return {'significant': False, 'correlation': 0.0, 'p_value': 1.0, 'group_difference': 0.0}
    
    def _analyze_categorical_field(self, data: pd.DataFrame, field_name: str,
                                  anchor_columns: Dict[str, str]) -> Optional[FieldDetectionResult]:
        """Analyze a categorical (non-binary) field."""
        # For Phase 4, focus on binary fields - categorical analysis would be Phase 5
        return None


def detect_field_types(data: pd.DataFrame, 
                      confidence_threshold: float = 0.6) -> List[FieldDetectionResult]:
    """
    Main entry point for field type detection.
    
    Args:
        data: DataFrame with clinical data
        confidence_threshold: Minimum confidence to report results
        
    Returns:
        List of detection results above confidence threshold
    """
    detector = StatisticalFieldDetector()
    all_results = detector.analyze_dataset(data)
    
    # Filter by confidence threshold
    high_confidence_results = [r for r in all_results if r.confidence >= confidence_threshold]
    
    return high_confidence_results


# Example usage and testing functions
def create_sample_clinical_data() -> pd.DataFrame:
    """Create sample clinical data for testing field detection."""
    np.random.seed(42)
    
    n_patients = 200
    
    # Create basic patient data
    data = pd.DataFrame({
        'patient_id': [f'PAT{i:04d}' for i in range(n_patients)],
        'site_id': np.random.choice(['SITE001', 'SITE002', 'SITE003'], n_patients),
        'age': np.random.normal(55, 15, n_patients).clip(18, 85),
    })
    
    # Add sex variable with known relationships
    sex_binary = np.random.binomial(1, 0.52, n_patients)  # Slightly more males
    data['sex_actual'] = ['Male' if x == 1 else 'Female' for x in sex_binary]
    
    # Create cryptic sex column "s_01" - this is what we want to detect!
    data['s_01'] = sex_binary
    
    # Add correlated variables that reveal the meaning of s_01
    # Height: Males taller on average  
    base_height = np.random.normal(165, 10, n_patients)
    height_adjustment = sex_binary * 12 + np.random.normal(0, 3, n_patients)
    data['height_cm'] = (base_height + height_adjustment).clip(140, 200)
    
    # Weight: Males heavier on average
    base_weight = np.random.normal(70, 12, n_patients)  
    weight_adjustment = sex_binary * 15 + np.random.normal(0, 5, n_patients)
    data['weight_kg'] = (base_weight + weight_adjustment).clip(40, 120)
    
    # Hemoglobin: Males higher on average
    base_hgb = np.random.normal(13.0, 1.5, n_patients)
    hgb_adjustment = sex_binary * 2.0 + np.random.normal(0, 0.5, n_patients)
    data['hemoglobin'] = (base_hgb + hgb_adjustment).clip(8, 18)
    
    # Add some other cryptic columns for testing
    data['v_02'] = np.random.binomial(1, 0.95, n_patients)  # Vital status (mostly alive)
    data['t_group'] = np.random.binomial(1, 0.5, n_patients)  # Treatment group (balanced)
    
    # Add some noise columns
    data['random_01'] = np.random.random(n_patients)
    data['random_02'] = np.random.randint(0, 5, n_patients)
    
    return data


if __name__ == "__main__":
    # Test the field detection system
    sample_data = create_sample_clinical_data()
    
    print("Sample data shape:", sample_data.shape)
    print("Sample data columns:", list(sample_data.columns))
    
    # Run field detection
    results = detect_field_types(sample_data)
    
    print(f"\nDetected {len(results)} field types:")
    for result in results:
        print(f"\nField: {result.field_name}")
        print(f"Predicted type: {result.predicted_type}")
        print(f"Confidence: {result.confidence:.3f}")
        print(f"Evidence: {result.evidence}")
        print(f"Correlations: {result.correlations}")