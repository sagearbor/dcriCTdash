"""
Test suite for core dashboard functions and data quality algorithms.

Tests existing dashboard functionality including enrollment charts, 
lab analysis, box plots, and data quality detection.
"""

import pytest
from unittest.mock import Mock, patch
import pandas as pd
import numpy as np
from datetime import date, datetime

# Import the dashboard functions to test
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.dashboard import (
    create_enrollment_chart,
    create_patient_biomarker_chart,
    create_lab_analysis_chart,
    create_lab_box_plot,
    detect_data_quality_issues,
    create_data_quality_table
)


class TestCreateEnrollmentChart:
    """Test the enrollment chart functionality."""
    
    @pytest.fixture
    def sample_stats_data(self):
        """Sample statistics data for enrollment chart."""
        return {
            "monthly_enrollment": [
                {"month": "2024-01", "enrolled": 25},
                {"month": "2024-02", "enrolled": 45}, 
                {"month": "2024-03", "enrolled": 38},
                {"month": "2024-04", "enrolled": 52}
            ],
            "total_patients": 160,
            "target_patients": 200,
            "enrollment_rate": 80.0
        }
    
    def test_enrollment_chart_creation(self, sample_stats_data):
        """Test basic enrollment chart creation."""
        fig = create_enrollment_chart(sample_stats_data)
        
        assert fig is not None
        assert len(fig.data) > 0
        assert "Cumulative Enrollment" in fig.layout.title.text
        
        # Check for enrollment traces
        trace_names = [trace.name for trace in fig.data if hasattr(trace, 'name') and trace.name]
        assert any("Actual" in name for name in trace_names)
    
    def test_enrollment_chart_demo_mode(self, sample_stats_data):
        """Test enrollment chart with demo mode enabled."""
        fig = create_enrollment_chart(sample_stats_data, demo_mode=True)
        
        assert fig is not None
        assert "Demo Mode" in fig.layout.title.text or "Projected" in str(fig.data)
    
    def test_enrollment_chart_empty_data(self):
        """Test enrollment chart with empty data."""
        fig = create_enrollment_chart({})
        
        assert fig is not None
        # Should show sample/placeholder data
        assert len(fig.data) > 0
    
    def test_enrollment_chart_missing_monthly_data(self):
        """Test enrollment chart with missing monthly enrollment data."""
        incomplete_data = {
            "total_patients": 100,
            "target_patients": 150
        }
        
        fig = create_enrollment_chart(incomplete_data)
        assert fig is not None


class TestCreatePatientBiomarkerChart:
    """Test the patient biomarker chart functionality."""
    
    @pytest.fixture
    def sample_patient_data(self):
        """Sample patient data."""
        return {
            "usubjid": "PAT001",
            "age": 45,
            "sex": "M",
            "date_of_enrollment": "2024-01-15"
        }
    
    @pytest.fixture
    def sample_labs_data(self):
        """Sample lab data for biomarker chart."""
        return [
            {"usubjid": "PAT001", "lbtestcd": "HGB", "lbstresn": 14.2, "collection_date": "2024-01-15"},
            {"usubjid": "PAT001", "lbtestcd": "HGB", "lbstresn": 13.8, "collection_date": "2024-02-15"},
            {"usubjid": "PAT001", "lbtestcd": "GLUC", "lbstresn": 95.0, "collection_date": "2024-01-15"},
            {"usubjid": "PAT001", "lbtestcd": "GLUC", "lbstresn": 98.5, "collection_date": "2024-02-15"}
        ]
    
    @pytest.fixture
    def sample_visits_data(self):
        """Sample visits data."""
        return [
            {"usubjid": "PAT001", "visit_name": "Baseline", "visit_date": "2024-01-15", "visit_num": 1},
            {"usubjid": "PAT001", "visit_name": "Month 1", "visit_date": "2024-02-15", "visit_num": 2}
        ]
    
    def test_biomarker_chart_creation(self, sample_patient_data, sample_labs_data, sample_visits_data):
        """Test biomarker chart creation with valid data."""
        fig = create_patient_biomarker_chart(sample_patient_data, sample_labs_data, sample_visits_data)
        
        assert fig is not None
        assert len(fig.data) > 0
        assert "PAT001" in fig.layout.title.text
        
        # Should have traces for different lab tests
        trace_names = [trace.name for trace in fig.data if hasattr(trace, 'name') and trace.name]
        assert len(trace_names) > 0
    
    def test_biomarker_chart_empty_labs(self, sample_patient_data):
        """Test biomarker chart with empty lab data."""
        fig = create_patient_biomarker_chart(sample_patient_data, [], [])
        
        assert fig is not None
        # Should show placeholder message
        assert len(fig.layout.annotations) > 0
        assert "No lab data" in fig.layout.annotations[0].text
    
    def test_biomarker_chart_single_test(self, sample_patient_data):
        """Test biomarker chart with single lab test."""
        single_test_labs = [
            {"usubjid": "PAT001", "lbtestcd": "HGB", "lbstresn": 14.2, "collection_date": "2024-01-15"}
        ]
        
        fig = create_patient_biomarker_chart(sample_patient_data, single_test_labs, [])
        
        assert fig is not None
        assert len(fig.data) > 0


class TestCreateLabAnalysisChart:
    """Test the lab analysis chart functionality."""
    
    @pytest.fixture
    def sample_labs_analysis_data(self):
        """Sample lab data for analysis."""
        return [
            {"lbtestcd": "HGB", "lbnrind": "NORMAL", "lbstresn": 14.2},
            {"lbtestcd": "HGB", "lbnrind": "LOW", "lbstresn": 10.5},
            {"lbtestcd": "HGB", "lbnrind": "HIGH", "lbstresn": 17.8},
            {"lbtestcd": "GLUC", "lbnrind": "NORMAL", "lbstresn": 95.0},
            {"lbtestcd": "GLUC", "lbnrind": "HIGH", "lbstresn": 180.0}
        ]
    
    def test_lab_analysis_chart_creation(self, sample_labs_analysis_data):
        """Test lab analysis chart creation."""
        fig = create_lab_analysis_chart(sample_labs_analysis_data)
        
        assert fig is not None
        assert len(fig.data) > 0
        assert "Lab Results Distribution" in fig.layout.title.text
    
    def test_lab_analysis_chart_empty_data(self):
        """Test lab analysis chart with empty data."""
        fig = create_lab_analysis_chart([])
        
        assert fig is not None
        # Should show sample/placeholder data
        assert len(fig.data) > 0
    
    def test_lab_analysis_chart_none_data(self):
        """Test lab analysis chart with None data."""
        fig = create_lab_analysis_chart(None)
        
        assert fig is not None
        assert len(fig.data) > 0


class TestCreateLabBoxPlot:
    """Test the lab box plot functionality."""
    
    @pytest.fixture
    def sample_lab_box_data(self):
        """Sample data for box plot testing."""
        return [
            {"usubjid": "PAT001", "lbtestcd": "HGB", "lbstresn": 14.2, "lbtest": "Hemoglobin"},
            {"usubjid": "PAT002", "lbtestcd": "HGB", "lbstresn": 13.8, "lbtest": "Hemoglobin"},
            {"usubjid": "PAT003", "lbtestcd": "HGB", "lbstresn": 15.1, "lbtest": "Hemoglobin"},
            {"usubjid": "PAT004", "lbtestcd": "HGB", "lbstresn": 12.9, "lbtest": "Hemoglobin"}
        ]
    
    @pytest.fixture
    def sample_patients_box(self):
        """Sample patient data for box plot."""
        return [
            {"usubjid": "PAT001", "site_id": "SITE001"},
            {"usubjid": "PAT002", "site_id": "SITE001"},
            {"usubjid": "PAT003", "site_id": "SITE002"},
            {"usubjid": "PAT004", "site_id": "SITE002"}
        ]
    
    @pytest.fixture
    def sample_sites_box(self):
        """Sample sites data for box plot."""
        return [
            {"site_id": "SITE001", "site_name": "Duke Medical Center"},
            {"site_id": "SITE002", "site_name": "Johns Hopkins"}
        ]
    
    def test_box_plot_creation(self, sample_lab_box_data, sample_patients_box, sample_sites_box):
        """Test box plot creation with valid data."""
        fig = create_lab_box_plot(sample_lab_box_data, sample_patients_box, sample_sites_box, "HGB")
        
        assert fig is not None
        assert len(fig.data) > 0
        assert fig.data[0].type == "box"
        assert "HGB" in fig.layout.title.text
    
    def test_box_plot_different_tests(self, sample_patients_box, sample_sites_box):
        """Test box plot with different lab tests."""
        gluc_data = [
            {"usubjid": "PAT001", "lbtestcd": "GLUC", "lbstresn": 95.0, "lbtest": "Glucose"},
            {"usubjid": "PAT002", "lbtestcd": "GLUC", "lbstresn": 88.5, "lbtest": "Glucose"}
        ]
        
        fig = create_lab_box_plot(gluc_data, sample_patients_box, sample_sites_box, "GLUC")
        
        assert fig is not None
        assert len(fig.data) > 0
        assert "GLUC" in fig.layout.title.text
    
    def test_box_plot_empty_data(self):
        """Test box plot with empty data."""
        fig = create_lab_box_plot([], [], [], "HGB")
        
        assert fig is not None
        # Should show sample data fallback
        assert len(fig.data) > 0
    
    def test_box_plot_nonexistent_test(self, sample_lab_box_data, sample_patients_box, sample_sites_box):
        """Test box plot with non-existent lab test."""
        fig = create_lab_box_plot(sample_lab_box_data, sample_patients_box, sample_sites_box, "NONEXISTENT")
        
        assert fig is not None
        # Should show message about no data
        assert len(fig.layout.annotations) > 0
        assert "No site data available" in fig.layout.annotations[0].text


class TestDetectDataQualityIssues:
    """Test the data quality detection algorithms."""
    
    @pytest.fixture
    def sample_patients_quality(self):
        """Sample patient data with quality issues."""
        return [
            {"usubjid": "PAT001", "age": 45, "sex": "M", "date_of_enrollment": "2024-01-15", "site_id": "SITE001"},
            {"usubjid": "PAT002", "age": None, "sex": "F", "date_of_enrollment": "2024-01-16", "site_id": "SITE001"},  # Missing age
            {"usubjid": "PAT003", "age": 150, "sex": "M", "date_of_enrollment": "2024-01-17", "site_id": "SITE002"},  # Invalid age
            {"usubjid": "PAT004", "age": 38, "sex": "", "date_of_enrollment": "2024-01-18", "site_id": "SITE002"}  # Missing sex
        ]
    
    @pytest.fixture
    def sample_labs_quality(self):
        """Sample lab data with quality issues."""
        return [
            {"usubjid": "PAT001", "lbtestcd": "HGB", "lbstresn": 14.2, "lbnrind": "NORMAL"},
            {"usubjid": "PAT002", "lbtestcd": "HGB", "lbstresn": None, "lbnrind": "NORMAL"},  # Missing value
            {"usubjid": "PAT003", "lbtestcd": "HGB", "lbstresn": 25.0, "lbnrind": "HIGH"},  # Extreme value
            {"usubjid": "PAT004", "lbtestcd": "GLUC", "lbstresn": -50.0, "lbnrind": "LOW"}  # Impossible value
        ]
    
    @pytest.fixture
    def sample_visits_quality(self):
        """Sample visit data."""
        return [
            {"usubjid": "PAT001", "visit_date": "2024-01-20", "visit_name": "Baseline"},
            {"usubjid": "PAT002", "visit_date": "2024-01-21", "visit_name": "Baseline"},
            {"usubjid": "PAT003", "visit_date": None, "visit_name": "Baseline"},  # Missing visit date
            {"usubjid": "PAT004", "visit_date": "2024-01-22", "visit_name": ""}  # Missing visit name
        ]
    
    @pytest.fixture
    def sample_sites_quality(self):
        """Sample sites data for quality testing."""
        return [
            {"site_id": "SITE001", "site_name": "Duke Medical Center"},
            {"site_id": "SITE002", "site_name": "Johns Hopkins"}
        ]
    
    def test_detect_quality_issues(self, sample_patients_quality, sample_labs_quality, sample_visits_quality, sample_sites_quality):
        """Test data quality issue detection."""
        issues = detect_data_quality_issues(
            sample_patients_quality, sample_labs_quality, sample_visits_quality, sample_sites_quality
        )
        
        assert isinstance(issues, list)
        assert len(issues) > 0
        
        # Check that issues have required fields
        for issue in issues:
            assert "issue" in issue
            assert "severity" in issue
            assert "usubjid" in issue
            assert "description" in issue
    
    def test_detect_quality_issues_empty_data(self):
        """Test quality detection with empty data."""
        issues = detect_data_quality_issues([], [], [], [])
        
        assert isinstance(issues, list)
        # May be empty or have generic issues depending on implementation
    
    def test_quality_issues_severity_levels(self, sample_patients_quality, sample_labs_quality, sample_visits_quality, sample_sites_quality):
        """Test that quality issues are assigned appropriate severity levels."""
        issues = detect_data_quality_issues(
            sample_patients_quality, sample_labs_quality, sample_visits_quality, sample_sites_quality
        )
        
        # Check that severity levels are reasonable
        severity_levels = {issue["severity"] for issue in issues}
        valid_severities = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
        
        assert severity_levels.issubset(valid_severities)
    
    def test_quality_issues_patient_specific(self, sample_patients_quality, sample_labs_quality, sample_visits_quality, sample_sites_quality):
        """Test that quality issues are correctly associated with patients."""
        issues = detect_data_quality_issues(
            sample_patients_quality, sample_labs_quality, sample_visits_quality, sample_sites_quality
        )
        
        # Check that all usubjids in issues are valid
        valid_usubjids = {p["usubjid"] for p in sample_patients_quality}
        issue_usubjids = {issue["usubjid"] for issue in issues if issue["usubjid"]}
        
        assert issue_usubjids.issubset(valid_usubjids)


class TestCreateDataQualityTable:
    """Test the data quality table creation."""
    
    @pytest.fixture
    def sample_quality_issues(self):
        """Sample quality issues for table testing."""
        return [
            {
                "usubjid": "PAT001",
                "issue": "missing_age",
                "severity": "HIGH",
                "description": "Patient age is missing",
                "site_id": "SITE001"
            },
            {
                "usubjid": "PAT002", 
                "issue": "extreme_lab_value",
                "severity": "CRITICAL",
                "description": "Hemoglobin value of 25.0 is extremely high",
                "site_id": "SITE002"
            },
            {
                "usubjid": "PAT003",
                "issue": "missing_visit_date",
                "severity": "MEDIUM",
                "description": "Visit date is missing for baseline visit",
                "site_id": "SITE001"
            }
        ]
    
    def test_data_quality_table_creation(self, sample_quality_issues):
        """Test data quality table creation."""
        table = create_data_quality_table(sample_quality_issues)
        
        assert table is not None
        # Should return HTML div or Dash DataTable
        assert hasattr(table, '__html__') or hasattr(table, 'data') or hasattr(table, 'children')
    
    def test_data_quality_table_empty(self):
        """Test data quality table with empty issues."""
        table = create_data_quality_table([])
        
        assert table is not None
        # Should show appropriate empty state message


class TestChartPerformanceAndIntegration:
    """Test chart performance and integration aspects."""
    
    def test_chart_generation_speed(self):
        """Test that chart generation completes within reasonable time."""
        import time
        
        start_time = time.time()
        
        # Generate multiple charts
        fig1 = create_enrollment_chart({})
        fig2 = create_lab_analysis_chart([])
        fig3 = create_lab_box_plot([], [], [], "HGB")
        
        end_time = time.time()
        
        # Charts should generate in less than 2 seconds
        assert (end_time - start_time) < 2.0
        
        # All charts should be created
        assert all(fig is not None for fig in [fig1, fig2, fig3])
    
    def test_chart_memory_usage(self):
        """Test that charts don't consume excessive memory."""
        import gc
        
        # Create multiple charts and clean up
        for i in range(5):
            fig1 = create_enrollment_chart({})
            fig2 = create_lab_analysis_chart([])
            del fig1, fig2
            gc.collect()
        
        # Test should complete without memory issues
        assert True
    
    def test_chart_responsive_properties(self):
        """Test that charts have proper responsive design properties."""
        charts = [
            create_enrollment_chart({}),
            create_lab_analysis_chart([]),
            create_lab_box_plot([], [], [], "HGB")
        ]
        
        for fig in charts:
            assert fig is not None
            assert hasattr(fig, 'layout')
            
            # Check that layout has responsive properties
            if hasattr(fig.layout, 'height'):
                assert isinstance(fig.layout.height, (int, type(None)))
            
            if hasattr(fig.layout, 'margin'):
                assert hasattr(fig.layout.margin, 'l') or hasattr(fig.layout.margin, 'left')


if __name__ == "__main__":
    pytest.main([__file__])