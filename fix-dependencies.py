#!/usr/bin/env python3
"""
Nura Dependency Fix Script
Fix backend pydantic imports and update frontend packages
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return success status"""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True, capture_output=True, text=True)
        print(f"✅ {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {command}")
        print(f"Error: {e.stderr}")
        return False

def fix_backend():
    """Fix backend dependencies"""
    print("🐍 Fixing Backend Dependencies...")
    backend_dir = Path("backend")
    
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    # Update pip first
    print("Updating pip...")
    if os.name == 'nt':  # Windows
        pip_path = backend_dir / "venv" / "Scripts" / "pip"
    else:  # Unix/Linux/macOS
        pip_path = backend_dir / "venv" / "bin" / "pip"
    
    run_command(f"{pip_path} install --upgrade pip", cwd=backend_dir)
    
    # Install updated requirements
    print("Installing updated requirements...")
    success = run_command(f"{pip_path} install -r requirements.txt", cwd=backend_dir)
    
    if success:
        print("✅ Backend dependencies updated successfully!")
        return True
    else:
        print("❌ Backend dependency update failed")
        return False

def fix_frontend():
    """Fix frontend dependencies"""
    print("\n⚛️  Fixing Frontend Dependencies...")
    frontend_dir = Path("frontend")
    
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Clear npm cache
    print("Clearing npm cache...")
    run_command("npm cache clean --force", cwd=frontend_dir)
    
    # Remove node_modules and package-lock.json
    print("Removing old dependencies...")
    node_modules = frontend_dir / "node_modules"
    package_lock = frontend_dir / "package-lock.json"
    
    if node_modules.exists():
        run_command("rm -rf node_modules" if os.name != 'nt' else "rmdir /s /q node_modules", cwd=frontend_dir)
    
    if package_lock.exists():
        package_lock.unlink()
    
    # Install fresh dependencies
    print("Installing updated dependencies...")
    success = run_command("npm install", cwd=frontend_dir)
    
    if success:
        print("✅ Frontend dependencies updated successfully!")
        return True
    else:
        print("❌ Frontend dependency update failed")
        return False

def main():
    """Main fix function"""
    print("🔧 Nura Dependency Fix Script")
    print("============================")
    
    backend_success = fix_backend()
    frontend_success = fix_frontend()
    
    print("\n" + "="*50)
    if backend_success and frontend_success:
        print("🎉 All dependencies fixed successfully!")
        print("\n📋 Next Steps:")
        print("1. Backend: cd backend && python run.py")
        print("2. Frontend: cd frontend && npm run dev")
        print("3. Access: http://localhost:3000")
    else:
        print("⚠️  Some fixes failed. Check the output above.")
        if not backend_success:
            print("💡 Backend fix failed - try manually: cd backend && pip install -r requirements.txt")
        if not frontend_success:
            print("💡 Frontend fix failed - try manually: cd frontend && npm install")

if __name__ == "__main__":
    main()