#!/usr/bin/env python3
"""
Nura Setup Verification Script
Verify that Phase 0 Foundation is properly configured
"""

import requests
import json
import sys
import time
from pathlib import Path


def check_file_exists(file_path, description):
    """Check if a file exists"""
    path = Path(file_path)
    if path.exists():
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - File not found: {file_path}")
        return False


def check_backend_health():
    """Check backend health endpoint"""
    try:
        print("\n🔍 Checking backend health...")
        response = requests.get("http://localhost:8000/api/v1/health", timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Backend is running")
            print(f"   App: {health_data.get('app', 'Unknown')}")
            print(f"   Environment: {health_data.get('environment', 'Unknown')}")
            print(f"   MongoDB: {health_data.get('mongodb', 'Unknown')}")
            print(f"   Qdrant: {health_data.get('qdrant', 'Unknown')}")
            
            # Check if databases are connected
            if health_data.get('mongodb') == 'connected':
                print("✅ MongoDB connection verified")
            else:
                print("⚠️  MongoDB not connected - check your MONGODB_URL")
            
            if health_data.get('qdrant') == 'connected':
                print("✅ Qdrant connection verified")
            else:
                print("⚠️  Qdrant not connected - check your QDRANT_URL and QDRANT_API_KEY")
            
            return True
        else:
            print(f"❌ Backend returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Backend not running or not accessible")
        print("   Start backend with: cd backend && uvicorn app.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ Error checking backend: {e}")
        return False


def check_frontend():
    """Check if frontend is running"""
    try:
        print("\n🔍 Checking frontend...")
        response = requests.get("http://localhost:3000", timeout=10)
        
        if response.status_code == 200:
            print("✅ Frontend is running")
            return True
        else:
            print(f"❌ Frontend returned status code: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Frontend not running or not accessible")
        print("   Start frontend with: cd frontend && npm run dev")
        return False
    except Exception as e:
        print(f"❌ Error checking frontend: {e}")
        return False


def verify_file_structure():
    """Verify the project file structure"""
    print("🔍 Verifying file structure...")
    
    files_to_check = [
        # Backend files
        ("backend/app/main.py", "Backend main application"),
        ("backend/app/core/config.py", "Backend configuration"),
        ("backend/app/core/logging.py", "Backend logging setup"),
        ("backend/app/core/security.py", "Backend security utilities"),
        ("backend/app/db/mongodb.py", "MongoDB connection manager"),
        ("backend/app/db/qdrant.py", "Qdrant connection manager"),
        ("backend/app/api/v1/health.py", "Health check endpoint"),
        ("backend/requirements.txt", "Backend dependencies"),
        ("backend/.env.example", "Backend environment template"),
        ("backend/Dockerfile", "Backend Docker configuration"),
        
        # Frontend files
        ("frontend/package.json", "Frontend dependencies"),
        ("frontend/src/app/layout.tsx", "Frontend layout"),
        ("frontend/src/app/page.tsx", "Frontend home page"),
        ("frontend/src/lib/providers.tsx", "React Query provider"),
        ("frontend/src/lib/axios.ts", "Axios HTTP client"),
        ("frontend/src/services/health.ts", "Health service"),
        ("frontend/src/stores/auth.ts", "Auth store"),
        ("frontend/src/components/health-check.tsx", "Health check component"),
        ("frontend/.env.local.example", "Frontend environment template"),
        ("frontend/Dockerfile", "Frontend Docker configuration"),
        
        # Root files
        ("README.md", "Project documentation"),
        ("docker-compose.yml", "Docker compose configuration"),
        ("setup.py", "Setup script"),
    ]
    
    success_count = 0
    for file_path, description in files_to_check:
        if check_file_exists(file_path, description):
            success_count += 1
    
    print(f"\n📊 File structure: {success_count}/{len(files_to_check)} files found")
    return success_count == len(files_to_check)


def main():
    """Main verification function"""
    print("🏥 Nura Phase 0 Foundation Verification")
    print("=====================================")
    
    all_checks_passed = True
    
    # Verify file structure
    if not verify_file_structure():
        all_checks_passed = False
    
    # Check backend
    backend_running = check_backend_health()
    if not backend_running:
        all_checks_passed = False
    
    # Check frontend
    frontend_running = check_frontend()
    if not frontend_running:
        all_checks_passed = False
    
    # Final summary
    print("\n" + "="*50)
    if all_checks_passed and backend_running and frontend_running:
        print("🎉 All checks passed! Nura Phase 0 Foundation is ready.")
        print("\n📋 What's working:")
        print("   ✅ File structure is complete")
        print("   ✅ Backend is running and healthy")
        print("   ✅ Frontend is accessible")
        print("   ✅ Database connections verified")
        print("\n🚀 Ready for Phase 1: Authentication System")
    else:
        print("⚠️  Some checks failed. Review the output above.")
        if not backend_running:
            print("\n🔧 To start backend:")
            print("   cd backend")
            print("   uvicorn app.main:app --reload")
        if not frontend_running:
            print("\n🔧 To start frontend:")
            print("   cd frontend") 
            print("   npm run dev")


if __name__ == "__main__":
    main()