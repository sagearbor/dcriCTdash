"""
Phase 7: Advanced Medical Vocabularies Support
Implements SNOMED CT, LOINC, ICD-10, RxNorm, and custom vocabulary management
"""

import json
import csv
import sqlite3
from typing import Dict, List, Optional, Union, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import pandas as pd
from pathlib import Path
import logging
from datetime import datetime
import requests
from functools import lru_cache
import re

logger = logging.getLogger(__name__)


class VocabularyType(Enum):
    """Supported medical vocabulary standards"""
    SNOMED_CT = "snomed_ct"
    LOINC = "loinc"
    ICD10 = "icd10"
    ICD9 = "icd9"
    RXNORM = "rxnorm"
    CPT = "cpt"
    HCPCS = "hcpcs"
    NDC = "ndc"
    CUSTOM = "custom"
    OMOP = "omop"


@dataclass
class VocabularyConcept:
    """Represents a single vocabulary concept"""
    concept_id: str
    concept_name: str
    vocabulary_type: VocabularyType
    concept_code: str
    domain: str = ""
    concept_class: str = ""
    standard_concept: bool = True
    synonyms: List[str] = field(default_factory=list)
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    attributes: Dict[str, Any] = field(default_factory=dict)
    valid_start_date: Optional[str] = None
    valid_end_date: Optional[str] = None


@dataclass
class VocabularyMapping:
    """Maps between different vocabulary systems"""
    source_concept: VocabularyConcept
    target_concept: VocabularyConcept
    mapping_type: str  # exact, narrow, broad, related
    confidence_score: float = 1.0
    mapping_source: str = ""
    validated: bool = False


class SNOMEDProvider:
    """SNOMED CT vocabulary provider"""
    
    def __init__(self):
        self.concepts: Dict[str, VocabularyConcept] = {}
        self.hierarchy: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(__name__)
        self._load_mock_data()
    
    def _load_mock_data(self):
        """Load mock SNOMED concepts for testing"""
        # Common clinical concepts
        mock_concepts = [
            ("404684003", "Clinical finding", "Finding"),
            ("73211009", "Diabetes mellitus", "Disease"),
            ("38341003", "Hypertensive disorder", "Disease"),
            ("195967001", "Asthma", "Disease"),
            ("49601007", "Cardiovascular disease", "Disease"),
            ("363406005", "Malignant neoplasm", "Disease"),
            ("386661006", "Fever", "Finding"),
            ("271737000", "Anemia", "Disease"),
            ("267036007", "Dyspnea", "Finding"),
            ("25064002", "Headache", "Finding"),
            ("84114007", "Heart failure", "Disease"),
            ("13645005", "Chronic obstructive pulmonary disease", "Disease"),
            ("44054006", "Type 2 diabetes mellitus", "Disease"),
            ("22298006", "Myocardial infarction", "Disease"),
            ("230690007", "Stroke", "Disease")
        ]
        
        for concept_id, name, concept_class in mock_concepts:
            self.concepts[concept_id] = VocabularyConcept(
                concept_id=concept_id,
                concept_name=name,
                vocabulary_type=VocabularyType.SNOMED_CT,
                concept_code=concept_id,
                domain="Condition",
                concept_class=concept_class,
                attributes={"semantic_tag": concept_class}
            )
    
    def search_concepts(self, query: str, limit: int = 10) -> List[VocabularyConcept]:
        """Search SNOMED concepts by text"""
        results = []
        query_lower = query.lower()
        
        for concept in self.concepts.values():
            if query_lower in concept.concept_name.lower():
                results.append(concept)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_concept(self, concept_id: str) -> Optional[VocabularyConcept]:
        """Get SNOMED concept by ID"""
        return self.concepts.get(concept_id)
    
    def get_hierarchy(self, concept_id: str) -> Dict[str, List[VocabularyConcept]]:
        """Get concept hierarchy (parents and children)"""
        # Mock hierarchy for demonstration
        hierarchy = {
            "parents": [],
            "children": []
        }
        
        # Simple mock: diseases are children of clinical finding
        if concept_id == "404684003":  # Clinical finding
            hierarchy["children"] = [c for c in self.concepts.values() 
                                    if c.concept_class == "Disease"]
        elif concept_id in self.concepts:
            hierarchy["parents"] = [self.concepts.get("404684003")]
        
        return hierarchy


class LOINCProvider:
    """LOINC laboratory and clinical observations provider"""
    
    def __init__(self):
        self.concepts: Dict[str, VocabularyConcept] = {}
        self.panels: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(__name__)
        self._load_mock_data()
    
    def _load_mock_data(self):
        """Load mock LOINC codes for testing"""
        # Common lab tests
        mock_loinc = [
            ("2160-0", "Creatinine [Mass/volume] in Serum or Plasma", "Chemistry"),
            ("2345-7", "Glucose [Mass/volume] in Serum or Plasma", "Chemistry"),
            ("718-7", "Hemoglobin [Mass/volume] in Blood", "Hematology"),
            ("4544-3", "Hematocrit [Volume Fraction] in Blood", "Hematology"),
            ("6690-2", "Leukocytes [#/volume] in Blood", "Hematology"),
            ("777-3", "Platelets [#/volume] in Blood", "Hematology"),
            ("2951-2", "Sodium [Moles/volume] in Serum or Plasma", "Chemistry"),
            ("2823-3", "Potassium [Moles/volume] in Serum or Plasma", "Chemistry"),
            ("2075-0", "Chloride [Moles/volume] in Serum or Plasma", "Chemistry"),
            ("2028-9", "Carbon dioxide [Moles/volume] in Serum or Plasma", "Chemistry"),
            ("3094-0", "Urea nitrogen [Mass/volume] in Serum or Plasma", "Chemistry"),
            ("1742-6", "Alanine aminotransferase [Units/volume] in Serum", "Chemistry"),
            ("1920-8", "Aspartate aminotransferase [Units/volume] in Serum", "Chemistry"),
            ("2885-2", "Protein [Mass/volume] in Serum or Plasma", "Chemistry"),
            ("1751-7", "Albumin [Mass/volume] in Serum or Plasma", "Chemistry")
        ]
        
        for code, name, category in mock_loinc:
            self.concepts[code] = VocabularyConcept(
                concept_id=code,
                concept_name=name,
                vocabulary_type=VocabularyType.LOINC,
                concept_code=code,
                domain="Measurement",
                concept_class=category,
                attributes={
                    "component": name.split("[")[0].strip() if "[" in name else name,
                    "property": self._extract_property(name),
                    "system": "Serum/Plasma/Blood",
                    "scale": "Quantitative",
                    "method": "Lab"
                }
            )
        
        # Create basic metabolic panel
        self.panels["basic_metabolic"] = ["2345-7", "2160-0", "3094-0", "2951-2", 
                                          "2823-3", "2075-0", "2028-9"]
        # Complete blood count
        self.panels["cbc"] = ["718-7", "4544-3", "6690-2", "777-3"]
    
    def _extract_property(self, name: str) -> str:
        """Extract property from LOINC name"""
        if "[" in name and "]" in name:
            return name[name.index("[")+1:name.index("]")]
        return "Unknown"
    
    def search_codes(self, query: str, limit: int = 10) -> List[VocabularyConcept]:
        """Search LOINC codes by text"""
        results = []
        query_lower = query.lower()
        
        for concept in self.concepts.values():
            if query_lower in concept.concept_name.lower():
                results.append(concept)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_panel(self, panel_name: str) -> List[VocabularyConcept]:
        """Get all tests in a panel"""
        panel_codes = self.panels.get(panel_name, [])
        return [self.concepts[code] for code in panel_codes if code in self.concepts]


class ICD10Provider:
    """ICD-10 diagnosis code provider"""
    
    def __init__(self):
        self.concepts: Dict[str, VocabularyConcept] = {}
        self.categories: Dict[str, str] = {}
        self.logger = logging.getLogger(__name__)
        self._load_mock_data()
    
    def _load_mock_data(self):
        """Load mock ICD-10 codes for testing"""
        # Common diagnosis codes
        mock_icd10 = [
            ("E11.9", "Type 2 diabetes mellitus without complications", "Endocrine"),
            ("I10", "Essential (primary) hypertension", "Circulatory"),
            ("J45.909", "Unspecified asthma, uncomplicated", "Respiratory"),
            ("N18.3", "Chronic kidney disease, stage 3", "Genitourinary"),
            ("F32.9", "Major depressive disorder, single episode", "Mental"),
            ("M79.3", "Myalgia", "Musculoskeletal"),
            ("R50.9", "Fever, unspecified", "Symptoms"),
            ("R06.02", "Shortness of breath", "Symptoms"),
            ("R51", "Headache", "Symptoms"),
            ("K21.9", "Gastro-esophageal reflux disease", "Digestive"),
            ("E78.5", "Hyperlipidemia, unspecified", "Endocrine"),
            ("I25.10", "Coronary artery disease", "Circulatory"),
            ("J44.1", "COPD with acute exacerbation", "Respiratory"),
            ("G43.909", "Migraine, unspecified", "Nervous"),
            ("D64.9", "Anemia, unspecified", "Blood")
        ]
        
        for code, name, category in mock_icd10:
            self.concepts[code] = VocabularyConcept(
                concept_id=code,
                concept_name=name,
                vocabulary_type=VocabularyType.ICD10,
                concept_code=code,
                domain="Condition",
                concept_class=category,
                attributes={
                    "chapter": category,
                    "billable": len(code) > 3
                }
            )
            
            # Store category mapping
            base_code = code[:3]
            if base_code not in self.categories:
                self.categories[base_code] = category
    
    def search_diagnoses(self, query: str, limit: int = 10) -> List[VocabularyConcept]:
        """Search ICD-10 diagnoses"""
        results = []
        query_lower = query.lower()
        
        # Search by code or name
        for concept in self.concepts.values():
            if (query_lower in concept.concept_name.lower() or 
                query.upper() in concept.concept_code):
                results.append(concept)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_category_codes(self, category: str) -> List[VocabularyConcept]:
        """Get all codes in a category"""
        return [c for c in self.concepts.values() 
                if c.attributes.get("chapter") == category]


class RxNormProvider:
    """RxNorm medication vocabulary provider"""
    
    def __init__(self):
        self.concepts: Dict[str, VocabularyConcept] = {}
        self.ingredients: Dict[str, List[str]] = {}
        self.logger = logging.getLogger(__name__)
        self._load_mock_data()
    
    def _load_mock_data(self):
        """Load mock RxNorm concepts"""
        # Common medications
        mock_rxnorm = [
            ("198211", "Simvastatin 20 MG Oral Tablet", "simvastatin", "20 mg", "tablet"),
            ("311036", "Metformin 500 MG Oral Tablet", "metformin", "500 mg", "tablet"),
            ("197361", "Amlodipine 5 MG Oral Tablet", "amlodipine", "5 mg", "tablet"),
            ("314077", "Lisinopril 10 MG Oral Tablet", "lisinopril", "10 mg", "tablet"),
            ("197517", "Albuterol 90 MCG/ACTUAT Inhalant", "albuterol", "90 mcg", "inhaler"),
            ("200031", "Amoxicillin 500 MG Oral Capsule", "amoxicillin", "500 mg", "capsule"),
            ("197516", "Acetaminophen 500 MG Oral Tablet", "acetaminophen", "500 mg", "tablet"),
            ("198062", "Omeprazole 20 MG Oral Capsule", "omeprazole", "20 mg", "capsule"),
            ("314076", "Hydrochlorothiazide 25 MG Oral Tablet", "hydrochlorothiazide", "25 mg", "tablet"),
            ("197896", "Atorvastatin 40 MG Oral Tablet", "atorvastatin", "40 mg", "tablet")
        ]
        
        for rxcui, name, ingredient, strength, form in mock_rxnorm:
            self.concepts[rxcui] = VocabularyConcept(
                concept_id=rxcui,
                concept_name=name,
                vocabulary_type=VocabularyType.RXNORM,
                concept_code=rxcui,
                domain="Drug",
                concept_class="Clinical Drug",
                attributes={
                    "ingredient": ingredient,
                    "strength": strength,
                    "dose_form": form,
                    "tty": "SCD"  # Semantic Clinical Drug
                }
            )
            
            # Track ingredients
            if ingredient not in self.ingredients:
                self.ingredients[ingredient] = []
            self.ingredients[ingredient].append(rxcui)
    
    def search_medications(self, query: str, limit: int = 10) -> List[VocabularyConcept]:
        """Search medications by name or ingredient"""
        results = []
        query_lower = query.lower()
        
        for concept in self.concepts.values():
            if (query_lower in concept.concept_name.lower() or
                query_lower in concept.attributes.get("ingredient", "").lower()):
                results.append(concept)
                if len(results) >= limit:
                    break
        
        return results
    
    def get_by_ingredient(self, ingredient: str) -> List[VocabularyConcept]:
        """Get all medications with a specific ingredient"""
        rxcuis = self.ingredients.get(ingredient.lower(), [])
        return [self.concepts[rxcui] for rxcui in rxcuis if rxcui in self.concepts]


class VocabularyManager:
    """Manages all vocabulary providers and mappings"""
    
    def __init__(self):
        self.snomed = SNOMEDProvider()
        self.loinc = LOINCProvider()
        self.icd10 = ICD10Provider()
        self.rxnorm = RxNormProvider()
        self.custom_vocabularies: Dict[str, Dict[str, VocabularyConcept]] = {}
        self.mappings: List[VocabularyMapping] = []
        self.logger = logging.getLogger(__name__)
        self._initialize_mappings()
    
    def _initialize_mappings(self):
        """Initialize cross-vocabulary mappings"""
        # Example mappings between SNOMED and ICD-10
        mapping_examples = [
            ("73211009", "E11.9", "exact"),  # Diabetes
            ("38341003", "I10", "exact"),     # Hypertension
            ("195967001", "J45.909", "exact"),  # Asthma
            ("386661006", "R50.9", "exact"),   # Fever
            ("267036007", "R06.02", "exact"),  # Dyspnea
        ]
        
        for snomed_id, icd10_code, mapping_type in mapping_examples:
            snomed_concept = self.snomed.get_concept(snomed_id)
            icd10_concept = self.icd10.concepts.get(icd10_code)
            
            if snomed_concept and icd10_concept:
                self.mappings.append(VocabularyMapping(
                    source_concept=snomed_concept,
                    target_concept=icd10_concept,
                    mapping_type=mapping_type,
                    confidence_score=0.95,
                    mapping_source="UMLS"
                ))
    
    def search_all_vocabularies(self, query: str, vocab_types: Optional[List[VocabularyType]] = None) -> Dict[str, List[VocabularyConcept]]:
        """Search across all or specified vocabularies"""
        results = {}
        
        if not vocab_types:
            vocab_types = [VocabularyType.SNOMED_CT, VocabularyType.LOINC, 
                          VocabularyType.ICD10, VocabularyType.RXNORM]
        
        for vocab_type in vocab_types:
            if vocab_type == VocabularyType.SNOMED_CT:
                results["SNOMED"] = self.snomed.search_concepts(query)
            elif vocab_type == VocabularyType.LOINC:
                results["LOINC"] = self.loinc.search_codes(query)
            elif vocab_type == VocabularyType.ICD10:
                results["ICD-10"] = self.icd10.search_diagnoses(query)
            elif vocab_type == VocabularyType.RXNORM:
                results["RxNorm"] = self.rxnorm.search_medications(query)
        
        return results
    
    def get_mappings(self, concept: VocabularyConcept, target_vocab: Optional[VocabularyType] = None) -> List[VocabularyMapping]:
        """Get mappings for a concept to other vocabularies"""
        mappings = []
        
        for mapping in self.mappings:
            if mapping.source_concept.concept_id == concept.concept_id:
                if not target_vocab or mapping.target_concept.vocabulary_type == target_vocab:
                    mappings.append(mapping)
            elif mapping.target_concept.concept_id == concept.concept_id:
                if not target_vocab or mapping.source_concept.vocabulary_type == target_vocab:
                    # Create reverse mapping
                    mappings.append(VocabularyMapping(
                        source_concept=mapping.target_concept,
                        target_concept=mapping.source_concept,
                        mapping_type=mapping.mapping_type,
                        confidence_score=mapping.confidence_score,
                        mapping_source=mapping.mapping_source
                    ))
        
        return mappings
    
    def add_custom_vocabulary(self, name: str, concepts: List[VocabularyConcept]):
        """Add a custom vocabulary"""
        self.custom_vocabularies[name] = {c.concept_id: c for c in concepts}
        self.logger.info(f"Added custom vocabulary '{name}' with {len(concepts)} concepts")
    
    def validate_code(self, code: str, vocabulary_type: VocabularyType) -> bool:
        """Validate if a code exists in a vocabulary"""
        if vocabulary_type == VocabularyType.SNOMED_CT:
            return code in self.snomed.concepts
        elif vocabulary_type == VocabularyType.LOINC:
            return code in self.loinc.concepts
        elif vocabulary_type == VocabularyType.ICD10:
            return code in self.icd10.concepts
        elif vocabulary_type == VocabularyType.RXNORM:
            return code in self.rxnorm.concepts
        elif vocabulary_type == VocabularyType.CUSTOM:
            return any(code in vocab for vocab in self.custom_vocabularies.values())
        
        return False
    
    def get_concept_details(self, code: str, vocabulary_type: VocabularyType) -> Optional[VocabularyConcept]:
        """Get detailed information about a concept"""
        if vocabulary_type == VocabularyType.SNOMED_CT:
            return self.snomed.get_concept(code)
        elif vocabulary_type == VocabularyType.LOINC:
            return self.loinc.concepts.get(code)
        elif vocabulary_type == VocabularyType.ICD10:
            return self.icd10.concepts.get(code)
        elif vocabulary_type == VocabularyType.RXNORM:
            return self.rxnorm.concepts.get(code)
        
        return None
    
    def export_vocabulary_stats(self) -> Dict[str, Any]:
        """Export statistics about loaded vocabularies"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "vocabularies": {
                "SNOMED CT": len(self.snomed.concepts),
                "LOINC": len(self.loinc.concepts),
                "ICD-10": len(self.icd10.concepts),
                "RxNorm": len(self.rxnorm.concepts),
                "Custom": sum(len(v) for v in self.custom_vocabularies.values())
            },
            "mappings": len(self.mappings),
            "panels": list(self.loinc.panels.keys()),
            "drug_ingredients": list(self.rxnorm.ingredients.keys())
        }
        
        return stats


class ClinicalValueSetBuilder:
    """Build and manage clinical value sets using vocabularies"""
    
    def __init__(self, vocab_manager: VocabularyManager):
        self.vocab_manager = vocab_manager
        self.value_sets: Dict[str, Dict[str, Any]] = {}
        self._initialize_common_value_sets()
    
    def _initialize_common_value_sets(self):
        """Initialize common clinical value sets"""
        # Diabetes value set
        self.value_sets["diabetes"] = {
            "name": "Diabetes Mellitus",
            "description": "All diabetes-related diagnoses",
            "concepts": {
                "SNOMED": ["73211009", "44054006"],
                "ICD-10": ["E11.9", "E10.9", "E13.9"]
            }
        }
        
        # Hypertension value set
        self.value_sets["hypertension"] = {
            "name": "Hypertensive Disorders",
            "description": "All hypertension-related diagnoses",
            "concepts": {
                "SNOMED": ["38341003"],
                "ICD-10": ["I10", "I11.9", "I12.9"]
            }
        }
        
        # Basic metabolic panel
        self.value_sets["basic_metabolic_panel"] = {
            "name": "Basic Metabolic Panel",
            "description": "Standard BMP lab tests",
            "concepts": {
                "LOINC": self.vocab_manager.loinc.panels.get("basic_metabolic", [])
            }
        }
    
    def create_value_set(self, name: str, description: str) -> Dict[str, Any]:
        """Create a new value set"""
        value_set = {
            "name": name,
            "description": description,
            "concepts": {},
            "created_at": datetime.now().isoformat()
        }
        self.value_sets[name] = value_set
        return value_set
    
    def add_concepts_to_value_set(self, value_set_name: str, vocabulary: str, concept_ids: List[str]):
        """Add concepts to a value set"""
        if value_set_name not in self.value_sets:
            raise ValueError(f"Value set '{value_set_name}' not found")
        
        if vocabulary not in self.value_sets[value_set_name]["concepts"]:
            self.value_sets[value_set_name]["concepts"][vocabulary] = []
        
        self.value_sets[value_set_name]["concepts"][vocabulary].extend(concept_ids)
    
    def expand_value_set(self, value_set_name: str) -> List[VocabularyConcept]:
        """Expand a value set to get all concepts"""
        if value_set_name not in self.value_sets:
            return []
        
        concepts = []
        value_set = self.value_sets[value_set_name]
        
        for vocab, concept_ids in value_set["concepts"].items():
            for concept_id in concept_ids:
                if vocab == "SNOMED":
                    concept = self.vocab_manager.snomed.get_concept(concept_id)
                elif vocab == "ICD-10":
                    concept = self.vocab_manager.icd10.concepts.get(concept_id)
                elif vocab == "LOINC":
                    concept = self.vocab_manager.loinc.concepts.get(concept_id)
                elif vocab == "RxNorm":
                    concept = self.vocab_manager.rxnorm.concepts.get(concept_id)
                else:
                    concept = None
                
                if concept:
                    concepts.append(concept)
        
        return concepts


def test_medical_vocabularies():
    """Test Phase 7 vocabulary implementation"""
    print("=== Testing Phase 7: Advanced Medical Vocabularies ===\n")
    
    # Initialize vocabulary manager
    vocab_manager = VocabularyManager()
    
    # Test 1: Search across vocabularies
    print("Test 1: Multi-vocabulary search for 'diabetes'")
    results = vocab_manager.search_all_vocabularies("diabetes")
    for vocab, concepts in results.items():
        print(f"  {vocab}: Found {len(concepts)} concepts")
        for concept in concepts[:2]:
            print(f"    - {concept.concept_code}: {concept.concept_name}")
    
    # Test 2: Get vocabulary mappings
    print("\nTest 2: Cross-vocabulary mappings")
    snomed_diabetes = vocab_manager.snomed.get_concept("73211009")
    if snomed_diabetes:
        mappings = vocab_manager.get_mappings(snomed_diabetes)
        print(f"  Found {len(mappings)} mappings for SNOMED diabetes concept")
        for mapping in mappings:
            print(f"    - Maps to {mapping.target_concept.vocabulary_type.value}: {mapping.target_concept.concept_code}")
    
    # Test 3: LOINC panels
    print("\nTest 3: LOINC panel expansion")
    bmp_tests = vocab_manager.loinc.get_panel("basic_metabolic")
    print(f"  Basic Metabolic Panel contains {len(bmp_tests)} tests:")
    for test in bmp_tests[:3]:
        print(f"    - {test.concept_code}: {test.concept_name}")
    
    # Test 4: RxNorm ingredient search
    print("\nTest 4: RxNorm medication search by ingredient")
    metformin_meds = vocab_manager.rxnorm.get_by_ingredient("metformin")
    print(f"  Found {len(metformin_meds)} metformin formulations")
    
    # Test 5: Value set builder
    print("\nTest 5: Clinical value sets")
    value_set_builder = ClinicalValueSetBuilder(vocab_manager)
    diabetes_concepts = value_set_builder.expand_value_set("diabetes")
    print(f"  Diabetes value set contains {len(diabetes_concepts)} concepts")
    
    # Test 6: Vocabulary validation
    print("\nTest 6: Code validation")
    test_codes = [
        ("73211009", VocabularyType.SNOMED_CT),
        ("2345-7", VocabularyType.LOINC),
        ("E11.9", VocabularyType.ICD10),
        ("INVALID", VocabularyType.SNOMED_CT)
    ]
    for code, vocab_type in test_codes:
        is_valid = vocab_manager.validate_code(code, vocab_type)
        print(f"  {code} in {vocab_type.value}: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Test 7: Export statistics
    print("\nTest 7: Vocabulary statistics")
    stats = vocab_manager.export_vocabulary_stats()
    print(f"  Loaded vocabularies:")
    for vocab, count in stats["vocabularies"].items():
        if count > 0:
            print(f"    - {vocab}: {count} concepts")
    print(f"  Total mappings: {stats['mappings']}")
    
    print("\n✅ Phase 7 vocabulary tests completed successfully")


if __name__ == "__main__":
    test_medical_vocabularies()