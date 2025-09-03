#!/usr/bin/env python3
"""
Complete DCRI Clinical Trial Analytics Dashboard Server

This runs both the FastAPI backend and the Dash frontend dashboard
for immediate testing and use.
"""

import os
import sys
import subprocess

def main():
    print("🚀 DCRI Clinical Trial Analytics Dashboard")
    print("=" * 60)
    print("")
    print("🔧 CHOOSE HOW TO RUN THE DASHBOARD:")
    print("")
    print("1️⃣  COMPLETE DASHBOARD (Recommended)")
    print("   → FastAPI Backend + Dash Frontend")
    print("   → Interactive dashboard with charts and data")
    print("   → Command: python run_integrated_server.py")
    print("")
    print("2️⃣  API ONLY (Backend Only)")
    print("   → Just the FastAPI backend for API testing")
    print("   → Command: python run_api_only.py")
    print("")
    print("=" * 60)
    print("")
    print("🎯 QUICK START - Complete Dashboard:")
    print("   python run_integrated_server.py")
    print("")
    print("   Then navigate to:")
    print("   • Dashboard: http://localhost:8050")
    print("   • API Docs: http://localhost:8000/api/docs") 
    print("")
    
    # Check if user wants to run automatically
    response = input("Run the complete dashboard now? (Y/n): ").strip().lower()
    
    if response in ['', 'y', 'yes']:
        print("🚀 Starting complete dashboard...")
        os.system("python run_integrated_server.py")
    else:
        print("✅ Use the commands above to start manually.")

if __name__ == "__main__":
    main()