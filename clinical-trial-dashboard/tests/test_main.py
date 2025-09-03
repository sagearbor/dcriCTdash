"""
Test suite for main FastAPI application.

Tests API endpoints, health checks, and basic application functionality.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

# Test client for FastAPI application
client = TestClient(app)

class TestHealthEndpoints:
    """Test health and status endpoints."""
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "dcri-clinical-trial-dashboard"
    
    def test_version_endpoint(self):
        """Test version information endpoint."""
        response = client.get("/api/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "api_version" in data
        assert data["version"] == "0.1.0"

class TestRootEndpoints:
    """Test root and redirect endpoints."""
    
    def test_root_redirect(self):
        """Test root endpoint redirects to dashboard."""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307  # Temporary redirect
        assert response.headers["location"] == "/dashboard"
    
    def test_dashboard_placeholder(self):
        """Test dashboard placeholder endpoint."""
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "DCRI Clinical Trial Analytics Dashboard" in response.text

class TestAPIEndpoints:
    """Test API placeholder endpoints."""
    
    def test_sites_endpoint(self):
        """Test sites API endpoint (placeholder)."""
        response = client.get("/api/sites")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_patients_endpoint(self):
        """Test patients API endpoint (placeholder)."""
        response = client.get("/api/patients")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
    
    def test_labs_endpoint(self):
        """Test labs API endpoint (placeholder)."""
        response = client.get("/api/labs")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data