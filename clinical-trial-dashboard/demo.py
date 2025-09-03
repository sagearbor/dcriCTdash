#!/usr/bin/env python3
"""
Demo script to verify the DCRI Clinical Trial Analytics Dashboard setup.

This script demonstrates that all components are working correctly:
- FastAPI application startup
- Data model imports 
- Mock data generation
- Basic database operations
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def demo_imports():
    """Demonstrate all key imports work."""
    print("🔧 Testing imports...")
    
    try:
        from app.main import app
        print("  ✓ FastAPI app imported")
        
        from app.data.models import Site, Patient, Visit, Lab
        print("  ✓ Data models imported")
        
        from app.data.generator import ClinicalDataGenerator
        print("  ✓ Mock data generator imported")
        
        from app.data.database import get_database_info
        print("  ✓ Database utilities imported")
        
        return True
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def demo_data_generation():
    """Demonstrate mock data generation."""
    print("\n📊 Testing mock data generation...")
    
    try:
        from app.data.generator import ClinicalDataGenerator
        
        # Generate small sample for demo
        generator = ClinicalDataGenerator(n_sites=3, target_patients=50)
        sample_data = generator.generate_complete_dataset()
        
        print("  ✓ Sample data generated successfully:")
        for table_name, df in sample_data.items():
            print(f"    - {table_name}: {len(df)} records")
        
        return True, sample_data
    except Exception as e:
        print(f"  ❌ Data generation failed: {e}")
        return False, None

def demo_database_info():
    """Demonstrate database configuration."""
    print("\n💾 Testing database configuration...")
    
    try:
        from app.data.database import get_database_info, check_database_connection
        
        db_info = get_database_info()
        print("  ✓ Database info retrieved:")
        for key, value in db_info.items():
            print(f"    - {key}: {value}")
        
        return True
    except Exception as e:
        print(f"  ❌ Database configuration failed: {e}")
        return False

def demo_api_response():
    """Demonstrate API response."""
    print("\n🌐 Testing API functionality...")
    
    try:
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        
        # Test health endpoint
        response = client.get("/health")
        print(f"  ✓ Health check: {response.json()}")
        
        # Test version endpoint
        response = client.get("/api/version")
        print(f"  ✓ Version info: {response.json()}")
        
        return True
    except Exception as e:
        print(f"  ❌ API test failed: {e}")
        return False

def main():
    """Run all demo functions."""
    print("🎯 DCRI Clinical Trial Analytics Dashboard - Setup Demo")
    print("=" * 60)
    
    success_count = 0
    total_tests = 4
    
    # Test 1: Imports
    if demo_imports():
        success_count += 1
    
    # Test 2: Data generation
    data_success, sample_data = demo_data_generation()
    if data_success:
        success_count += 1
    
    # Test 3: Database configuration
    if demo_database_info():
        success_count += 1
    
    # Test 4: API functionality
    if demo_api_response():
        success_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📋 Demo Summary: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All systems operational! The project is ready for development.")
        print("\n🚀 Next steps:")
        print("   1. Run: python app/main.py (to start the application)")
        print("   2. Visit: http://localhost:8000 (to see the dashboard)")
        print("   3. API docs: http://localhost:8000/api/docs")
        return 0
    else:
        print("⚠️  Some components need attention before proceeding.")
        return 1

if __name__ == "__main__":
    exit(main())