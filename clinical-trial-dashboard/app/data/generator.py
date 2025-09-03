"""
Mock Data Generator

Generates realistic mock clinical trial data for development and testing.
Creates CDISC-compliant data for ~20 sites and ~2,000 patients with laboratory results.
"""

import pandas as pd
import numpy as np
from datetime import datetime, date, timedelta
from typing import List, Dict, Tuple
from faker import Faker
import random

# Initialize Faker for generating realistic data
fake = Faker()
fake.seed_instance(42)  # For reproducible data generation

class ClinicalDataGenerator:
    """
    Generates mock clinical trial data following CDISC standards.
    
    Attributes:
        start_date: Trial start date
        end_date: Trial end date 
        n_sites: Number of clinical sites
        target_patients: Target total patient enrollment
    """
    
    def __init__(
        self, 
        start_date: date = date(2023, 1, 1),
        end_date: date = date(2024, 12, 31),
        n_sites: int = 20,
        target_patients: int = 2000
    ):
        self.start_date = start_date
        self.end_date = end_date
        self.n_sites = n_sites
        self.target_patients = target_patients
        
        # Common lab test configurations
        self.lab_tests = {
            "GLUC": {"name": "Glucose", "unit": "mg/dL", "ref_low": 70, "ref_high": 100},
            "HGB": {"name": "Hemoglobin", "unit": "g/dL", "ref_low": 12.0, "ref_high": 17.5},
            "WBC": {"name": "White Blood Cell Count", "unit": "K/uL", "ref_low": 4.0, "ref_high": 11.0},
            "CREAT": {"name": "Creatinine", "unit": "mg/dL", "ref_low": 0.6, "ref_high": 1.3},
            "ALT": {"name": "Alanine Aminotransferase", "unit": "U/L", "ref_low": 10, "ref_high": 40},
            "CHOL": {"name": "Total Cholesterol", "unit": "mg/dL", "ref_low": 100, "ref_high": 200},
            "HDL": {"name": "HDL Cholesterol", "unit": "mg/dL", "ref_low": 40, "ref_high": 100},
            "LDL": {"name": "LDL Cholesterol", "unit": "mg/dL", "ref_low": 0, "ref_high": 130},
            "TRIG": {"name": "Triglycerides", "unit": "mg/dL", "ref_low": 50, "ref_high": 150},
            "HBA1C": {"name": "Hemoglobin A1c", "unit": "%", "ref_low": 4.0, "ref_high": 5.6}
        }
        
        # Visit schedule
        self.visit_schedule = [
            {"visit_num": 1, "visit_name": "Screening", "day": -14},
            {"visit_num": 2, "visit_name": "Baseline", "day": 0},
            {"visit_num": 3, "visit_name": "Week 2", "day": 14},
            {"visit_num": 4, "visit_name": "Week 4", "day": 28},
            {"visit_num": 5, "visit_name": "Week 8", "day": 56},
            {"visit_num": 6, "visit_name": "Week 12", "day": 84},
            {"visit_num": 7, "visit_name": "Week 16", "day": 112},
            {"visit_num": 8, "visit_name": "Week 24", "day": 168},
            {"visit_num": 9, "visit_name": "End of Study", "day": 336}
        ]
    
    def generate_sites(self) -> pd.DataFrame:
        """
        Generate clinical trial site data.
        
        Returns:
            pd.DataFrame: Site information with geographic data
        """
        sites_data = []
        
        # Define countries with realistic site distributions
        countries = ["US", "CA", "GB", "DE", "FR", "IT", "ES", "AU", "JP", "KR"]
        country_weights = [0.4, 0.1, 0.1, 0.08, 0.08, 0.06, 0.06, 0.04, 0.04, 0.04]
        
        for i in range(1, self.n_sites + 1):
            country = random.choices(countries, weights=country_weights)[0]
            
            # Generate realistic coordinates based on country
            lat, lon = self._generate_coordinates_for_country(country)
            
            site_data = {
                "site_id": f"SITE{i:03d}",
                "site_name": f"{fake.company()} Medical Center - Site {i:03d}",
                "country": country,
                "latitude": lat,
                "longitude": lon,
                "enrollment_target": random.randint(80, 150)  # Varied enrollment targets
            }
            sites_data.append(site_data)
        
        return pd.DataFrame(sites_data)
    
    def generate_patients(self, sites_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate patient enrollment data.
        
        Args:
            sites_df: DataFrame of site information
            
        Returns:
            pd.DataFrame: Patient enrollment and demographic data
        """
        patients_data = []
        patient_id = 1
        
        for _, site in sites_df.iterrows():
            # Generate enrollment pattern (gradual ramp-up)
            site_target = site["enrollment_target"]
            actual_enrolled = random.randint(
                int(site_target * 0.6), 
                int(site_target * 1.1)
            )  # Some sites over/under-enroll
            
            for p in range(actual_enrolled):
                # Generate enrollment date with realistic pattern
                enrollment_date = self._generate_enrollment_date()
                
                # Generate CDISC-compliant USUBJID
                usubjid = f"DCRI-{site['site_id']}-{patient_id:04d}"
                
                patient_data = {
                    "usubjid": usubjid,
                    "site_id": site["site_id"],
                    "date_of_enrollment": enrollment_date,
                    "age": random.randint(18, 80),
                    "sex": random.choice(["M", "F", "M", "F", "U"]),  # Slight male bias
                    "race": random.choice([
                        "WHITE", "BLACK OR AFRICAN AMERICAN", "ASIAN", 
                        "HISPANIC OR LATINO", "OTHER", "UNKNOWN"
                    ])
                }
                patients_data.append(patient_data)
                patient_id += 1
        
        return pd.DataFrame(patients_data)
    
    def generate_visits(self, patients_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate patient visit data.
        
        Args:
            patients_df: DataFrame of patient information
            
        Returns:
            pd.DataFrame: Visit scheduling and attendance data
        """
        visits_data = []
        visit_id = 1
        
        for _, patient in patients_df.iterrows():
            enrollment_date = pd.to_datetime(patient["date_of_enrollment"]).date()
            
            for visit_info in self.visit_schedule:
                # Calculate visit date
                visit_date = enrollment_date + timedelta(days=visit_info["day"])
                
                # Skip visits that would be in the future or before trial start
                if visit_date > self.end_date or visit_date < self.start_date:
                    continue
                
                # Some patients miss visits (realistic dropout pattern)
                if visit_info["visit_num"] > 2:  # After baseline
                    dropout_prob = 0.05 * (visit_info["visit_num"] - 2)  # Increasing dropout
                    if random.random() < dropout_prob:
                        continue  # Patient dropped out
                
                # Add realistic visit date variability (±3 days)
                date_variance = random.randint(-3, 3)
                actual_visit_date = visit_date + timedelta(days=date_variance)
                
                visit_data = {
                    "visit_id": f"VIS{visit_id:06d}",
                    "usubjid": patient["usubjid"],
                    "visit_name": visit_info["visit_name"],
                    "visit_num": visit_info["visit_num"],
                    "visit_date": actual_visit_date
                }
                visits_data.append(visit_data)
                visit_id += 1
        
        return pd.DataFrame(visits_data)
    
    def generate_labs(self, patients_df: pd.DataFrame, visits_df: pd.DataFrame) -> pd.DataFrame:
        """
        Generate laboratory test results.
        
        Args:
            patients_df: DataFrame of patient information
            visits_df: DataFrame of visit information
            
        Returns:
            pd.DataFrame: Laboratory test results following CDISC LB domain
        """
        labs_data = []
        lab_id = 1
        
        for _, visit in visits_df.iterrows():
            # Get patient info for context
            patient_info = patients_df[patients_df["usubjid"] == visit["usubjid"]].iloc[0]
            
            # Determine which tests to run (not all tests at all visits)
            tests_to_run = self._determine_visit_tests(visit["visit_num"])
            
            for test_code in tests_to_run:
                test_info = self.lab_tests[test_code]
                
                # Generate realistic lab values
                lab_value, ref_indicator = self._generate_lab_value(
                    test_code, patient_info, visit["visit_num"]
                )
                
                lab_data = {
                    "lab_id": f"LAB{lab_id:08d}",
                    "usubjid": visit["usubjid"],
                    "visit_id": visit["visit_id"],
                    "lbtestcd": test_code,
                    "lbtest": test_info["name"],
                    "lborres": str(lab_value),  # Original result as string
                    "lbstresn": lab_value,  # Standardized numeric result
                    "lbstresu": test_info["unit"],
                    "lbnrind": ref_indicator,
                    "collection_date": visit["visit_date"]
                }
                labs_data.append(lab_data)
                lab_id += 1
        
        return pd.DataFrame(labs_data)
    
    def _generate_coordinates_for_country(self, country_code: str) -> Tuple[float, float]:
        """Generate realistic coordinates for a given country."""
        # Simplified coordinate generation - would use real geographic data in production
        coord_ranges = {
            "US": (25, 49, -125, -65),  # lat_min, lat_max, lon_min, lon_max
            "CA": (45, 60, -140, -60),
            "GB": (50, 59, -8, 2),
            "DE": (47, 55, 6, 15),
            "FR": (42, 51, -5, 8),
            "IT": (36, 47, 7, 18),
            "ES": (36, 44, -9, 4),
            "AU": (-39, -10, 113, 154),
            "JP": (24, 46, 123, 146),
            "KR": (33, 43, 124, 132)
        }
        
        if country_code in coord_ranges:
            lat_min, lat_max, lon_min, lon_max = coord_ranges[country_code]
            lat = round(random.uniform(lat_min, lat_max), 4)
            lon = round(random.uniform(lon_min, lon_max), 4)
            return lat, lon
        else:
            return 0.0, 0.0  # Default coordinates
    
    def _generate_enrollment_date(self) -> date:
        """Generate realistic enrollment date with ramp-up pattern."""
        # Create enrollment pattern that ramps up over time
        total_days = (self.end_date - self.start_date).days
        
        # Weight enrollment dates to simulate realistic enrollment pattern
        # Early dates have lower probability, middle dates higher
        day_offset = int(np.random.beta(2, 3) * total_days)  # Beta distribution for realism
        return self.start_date + timedelta(days=day_offset)
    
    def _determine_visit_tests(self, visit_num: int) -> List[str]:
        """Determine which lab tests to perform at each visit."""
        # Comprehensive testing at screening and baseline
        if visit_num in [1, 2]:
            return list(self.lab_tests.keys())
        
        # Routine monitoring tests for follow-up visits
        elif visit_num in [3, 4, 5, 6, 7, 8]:
            return ["GLUC", "HGB", "WBC", "CREAT", "ALT"]
        
        # Full panel at end of study
        elif visit_num == 9:
            return list(self.lab_tests.keys())
        
        return []
    
    def _generate_lab_value(self, test_code: str, patient_info: pd.Series, visit_num: int) -> Tuple[float, str]:
        """Generate realistic lab values with appropriate reference range indicators."""
        test_info = self.lab_tests[test_code]
        
        # Base value generation using normal distribution around reference range midpoint
        ref_mid = (test_info["ref_low"] + test_info["ref_high"]) / 2
        ref_range = test_info["ref_high"] - test_info["ref_low"]
        
        # Add patient-specific factors
        age_factor = 1.0
        sex_factor = 1.0
        
        if patient_info["age"] > 65:
            age_factor = 1.1  # Slightly higher values for elderly
        
        if test_code == "HGB" and patient_info["sex"] == "F":
            sex_factor = 0.9  # Lower hemoglobin for females
        
        # Generate value with some variability
        base_value = np.random.normal(ref_mid, ref_range * 0.2)
        adjusted_value = base_value * age_factor * sex_factor
        
        # Add visit-to-visit variability (some patients have progression)
        if visit_num > 2:
            trend_factor = 1.0 + (visit_num - 2) * 0.02 * random.choice([-1, 1])
            adjusted_value *= trend_factor
        
        # Round to appropriate decimal places
        if test_code in ["GLUC", "CHOL", "HDL", "LDL", "TRIG", "ALT", "WBC"]:
            final_value = round(adjusted_value, 0)
        else:
            final_value = round(adjusted_value, 1)
        
        # Determine reference range indicator
        if final_value < test_info["ref_low"]:
            ref_indicator = "LOW"
        elif final_value > test_info["ref_high"]:
            ref_indicator = "HIGH"
        else:
            ref_indicator = "NORMAL"
        
        return final_value, ref_indicator
    
    def generate_complete_dataset(self) -> Dict[str, pd.DataFrame]:
        """
        Generate complete clinical trial dataset.
        
        Returns:
            Dict[str, pd.DataFrame]: Dictionary containing all generated datasets
        """
        print(f"Generating mock clinical trial data...")
        print(f"- Target sites: {self.n_sites}")
        print(f"- Target patients: {self.target_patients}")
        print(f"- Trial period: {self.start_date} to {self.end_date}")
        
        # Generate data in dependency order
        sites_df = self.generate_sites()
        print(f"✓ Generated {len(sites_df)} sites")
        
        patients_df = self.generate_patients(sites_df)
        print(f"✓ Generated {len(patients_df)} patients")
        
        visits_df = self.generate_visits(patients_df)
        print(f"✓ Generated {len(visits_df)} visits")
        
        labs_df = self.generate_labs(patients_df, visits_df)
        print(f"✓ Generated {len(labs_df)} lab results")
        
        dataset = {
            "sites": sites_df,
            "patients": patients_df,
            "visits": visits_df,
            "labs": labs_df
        }
        
        print(f"\n📊 Dataset Summary:")
        for name, df in dataset.items():
            print(f"  {name}: {len(df):,} records")
        
        return dataset

# Convenience functions for quick data generation
def generate_mock_data() -> Dict[str, pd.DataFrame]:
    """Generate mock clinical trial data with default parameters."""
    generator = ClinicalDataGenerator()
    return generator.generate_complete_dataset()

def save_mock_data_to_csv(data: Dict[str, pd.DataFrame], output_dir: str = "data") -> None:
    """Save generated datasets to CSV files."""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    for table_name, df in data.items():
        filepath = os.path.join(output_dir, f"{table_name}.csv")
        df.to_csv(filepath, index=False)
        print(f"Saved {table_name} data to {filepath}")

# For testing the generator
if __name__ == "__main__":
    # Generate and display sample data
    generator = ClinicalDataGenerator(n_sites=5, target_patients=200)  # Smaller sample for testing
    sample_data = generator.generate_complete_dataset()
    
    print("\n📋 Sample Data Preview:")
    for name, df in sample_data.items():
        print(f"\n{name.upper()} (first 3 rows):")
        print(df.head(3).to_string(index=False))