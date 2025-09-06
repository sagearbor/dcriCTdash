# DCRI Clinical Trial Dashboard - Development Roadmap

## Overview
This document outlines the complete development roadmap for the DCRI Clinical Trial Analytics Dashboard, including all phases from Phase 4 fixes through Phase 7 advanced features.

---

## 🔧 **PHASE 4 FIXES** (Priority: Critical)

### Issues Identified:
1. **Lab Value Distribution dropdown filters not updating charts**
   - Problem: Box plot doesn't respond to test selector changes
   - Root cause: Callback connectivity issues
   - Fix: Verify callback decorators and input/output mappings

2. **3D Lab Data Explorer dropdown filters not updating plots** 
   - Problem: 3D scatter plot ignores dropdown selections
   - Root cause: Callback not triggering chart updates
   - Fix: Debug callback chain and data filtering logic

3. **Patient Disposition Flow 'Show Numbers' dropdown not working**
   - Problem: Sankey diagram doesn't respond to numbers toggle
   - Root cause: Missing callback or improper state management
   - Fix: Implement proper callback for numbers display mode

4. **PDF Report Generation bytearray encoding error**
   - Error: `'bytearray' object has no attribute 'encode'`
   - Root cause: String/bytes conversion issue in PDF generation
   - Fix: Proper encoding handling in report generation pipeline

5. **Field Detection UX Enhancement**
   - Add explanatory tooltips for statistical correlations
   - Include mapped values display (e.g., "0=Female, 1=Male")
   - Provide context for why correlations indicate field types

### Success Criteria:
- All dashboard dropdowns respond correctly
- PDF generation works for all report types
- Field detection includes helpful explanatory text
- All Phase 4 features fully functional

---

## 🎨 **PHASE 4.5: MULTI-TIER INTERFACE** (Priority: High)

### Objective:
Create adaptive UI complexity levels for different user types

### Implementation:
1. **Executive View** (Default)
   - Key metrics dashboard
   - Traffic light indicators (red/yellow/green status)
   - High-level summaries only
   - Minimal controls

2. **Clinical View** (Standard)
   - Standard dashboard controls
   - Filtered dropdown options
   - Clinical context and explanations
   - Moderate detail level

3. **Technical View** (Advanced)
   - Full parameter access
   - Advanced filtering options
   - Statistical details
   - Configuration controls

4. **Developer View** (Expert)
   - Raw data inspection
   - API endpoint access
   - Debugging information
   - System performance metrics

### UI Components:
- Interface complexity toggle in header
- Progressive disclosure of controls
- Context-sensitive help text
- Role-based feature visibility

### Success Criteria:
- Smooth transitions between interface levels
- Appropriate feature visibility per level
- User preference persistence
- Clean, intuitive navigation

---

## 📊 **PHASE 5: CLINICAL DATA FORMAT SUPPORT** (Priority: High)

### Objective:
Support industry-standard clinical trial data formats

### Priority Order:
1. **REDCap Integration**
   - CSV data dictionary import
   - REDCap export format support
   - Field mapping automation
   - Validation rule import

2. **Custom CSV/JSON Dictionaries**
   - Generic dictionary parser
   - Flexible field mapping
   - Custom validation rules
   - Multiple file format support

3. **OMOP CDM Support**
   - Standard OMOP table structures
   - Vocabulary integration
   - Concept mapping
   - CDM validation

4. **FHIR Support**
   - FHIR R4/R5 resources
   - Patient, Observation, Encounter
   - Bundle processing
   - FHIR validation

### Mock Data Generation Enhancement:
- Format-specific templates
- Realistic clinical data scenarios
- Proper code systems and vocabularies
- Cross-format conversion utilities

### Success Criteria:
- Import data dictionaries from common formats
- Generate mock data in multiple clinical formats
- Seamless format conversion
- Validation against format specifications

---

## 🗂️ **PHASE 6: GENERIC DATA DICTIONARY ENGINE** (Priority: Medium)

### Objective:
Universal data dictionary processing and field mapping system

### Core Components:

1. **Dictionary Parser**
   - CSV data dictionary support
   - JSON schema support
   - XML define.xml support
   - YAML configuration support

2. **Intelligent Field Mapping**
   - Automatic detection of standard fields
   - Fuzzy matching for similar names
   - Statistical correlation analysis
   - Machine learning field classification

3. **Data Normalization Pipeline**
   - Value standardization (units, formats)
   - Date/time harmonization
   - Categorical value mapping
   - Range validation and outlier detection

4. **Validation Framework**
   - Schema compliance checking
   - Data quality scoring
   - Missing data analysis
   - Consistency validation

### User Interface:
- Dictionary upload interface
- Interactive field mapping tool
- Validation result dashboard
- Mapping confidence scores

### Success Criteria:
- Parse multiple dictionary formats
- Accurate automatic field mapping (>90%)
- Robust data validation pipeline
- User-friendly mapping interface

---

## 🏥 **PHASE 7: ADVANCED VOCABULARIES** (Priority: Future)

### Objective:
Integration with clinical coding standards and vocabularies

### Vocabulary Support:

1. **SNOMED CT**
   - Concept hierarchy navigation
   - Semantic relationships
   - Clinical finding codes
   - Procedure codes

2. **LOINC**
   - Laboratory test codes
   - Clinical observations
   - Units of measure
   - Reference ranges

3. **ICD-10/11**
   - Diagnosis codes
   - Procedure codes
   - Mortality statistics
   - Morbidity classification

4. **Medication Coding**
   - RxNorm drug codes
   - ATC classification
   - NDC product codes
   - Drug interaction data

### Implementation Features:
- Code lookup and validation
- Concept mapping between vocabularies
- Terminology services integration
- Local vocabulary caching

### Success Criteria:
- Accurate code validation
- Cross-vocabulary mapping
- Fast terminology lookup
- Comprehensive coverage of clinical concepts

---

## 📝 **DEVELOPMENT TASKS BREAKDOWN**

### Phase 4 Fixes (Estimated: 8-12 hours)
- [ ] Debug and fix lab distribution dropdown callbacks (2-3 hours)
- [ ] Fix 3D scatter plot interaction callbacks (2-3 hours)  
- [ ] Repair Sankey diagram numbers toggle (1-2 hours)
- [ ] Resolve PDF generation encoding error (2-3 hours)
- [ ] Add explanatory tooltips to field detection (1-2 hours)

### Phase 4.5 Multi-tier Interface (Estimated: 12-16 hours)
- [ ] Design interface complexity levels (2-3 hours)
- [ ] Implement progressive disclosure system (4-6 hours)
- [ ] Create role-based visibility controls (3-4 hours)
- [ ] Add interface toggle and persistence (2-3 hours)
- [ ] Testing and refinement (1-2 hours)

### Phase 5 Clinical Formats (Estimated: 20-30 hours)
- [ ] REDCap dictionary parser (6-8 hours)
- [ ] Custom CSV/JSON dictionary support (6-8 hours)
- [ ] OMOP CDM integration (4-6 hours)
- [ ] FHIR resource support (4-6 hours)
- [ ] Format conversion utilities (2-4 hours)

### Phase 6 Dictionary Engine (Estimated: 25-35 hours)
- [ ] Universal dictionary parser (8-12 hours)
- [ ] Field mapping algorithms (8-12 hours)
- [ ] Data normalization pipeline (6-8 hours)
- [ ] Validation framework (3-5 hours)

### Phase 7 Advanced Vocabularies (Estimated: 30-40 hours)
- [ ] SNOMED CT integration (8-12 hours)
- [ ] LOINC code support (6-8 hours)
- [ ] ICD coding integration (6-8 hours)
- [ ] Medication vocabularies (6-8 hours)
- [ ] Cross-vocabulary mapping (4-6 hours)

---

## 📋 **QUALITY ASSURANCE**

### Testing Strategy:
- Unit tests for all new components
- Integration tests for data pipelines
- User acceptance testing for UI changes
- Performance testing for large datasets

### Documentation Requirements:
- API documentation updates
- User guide enhancements
- Developer documentation
- Deployment instructions

### Success Metrics:
- Zero critical bugs in production
- User interface satisfaction scores >8/10
- Data processing accuracy >99%
- System performance within acceptable limits

---

## 🚀 **DEPLOYMENT STRATEGY**

### Development Workflow:
1. Feature development in isolated branches
2. Code review and testing
3. Staging environment validation
4. Production deployment with rollback capability

### Rollback Plan:
- Database migration rollback procedures
- Feature flag system for quick disabling
- Automated backup and restore processes
- Emergency contact procedures

---

**Document Version**: 1.0  
**Last Updated**: 2025-09-06  
**Next Review**: After Phase 4 completion