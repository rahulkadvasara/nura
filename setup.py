#!/usr/bin/env python3
"""
Nura Setup Script
Automated setup for Phase 0 Foundation
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, cwd=None):
    """Run a command and handle errors"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            check=True,
            capture_output=True,
            text=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error output: {e.stderr}")
        return None


def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python
    try:
        python_version = subprocess.check_output([sys.executable, "--version"], text=True)
        print(f"✅ {python_version.strip()}")
    except:
        print("❌ Python not found")
        return False
    
    # Check Node.js
    try:
        node_version = subprocess.check_output(["node", "--version"], text=True)
        print(f"✅ Node.js {node_version.strip()}")
    except:
        print("❌ Node.js not found")
        return False
    
    # Check npm
    try:
        npm_version = subprocess.check_output(["npm", "--version"], text=True)
        print(f"✅ npm {npm_version.strip()}")
    except:
        print("❌ npm not found")
        return False
    
    return True


def setup_backend():
    """Setup backend environment"""
    print("\n🐍 Setting up backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    # Create virtual environment
    print("Creating Python virtual environment...")
    if not run_command(f"{sys.executable} -m venv venv", cwd=backend_dir):
        return False
    
    # Determine activation script path
    if os.name == 'nt':  # Windows
        activate_script = backend_dir / "venv" / "Scripts" / "activate.bat"
        pip_path = backend_dir / "venv" / "Scripts" / "pip"
    else:  # Unix/Linux/macOS
        activate_script = backend_dir / "venv" / "bin" / "activate"
        pip_path = backend_dir / "venv" / "bin" / "pip"
    
    # Install dependencies
    print("Installing Python dependencies...")
    if not run_command(f"{pip_path} install -r requirements.txt", cwd=backend_dir):
        return False
    
    # Copy environment file
    env_example = backend_dir / ".env.example"
    env_file = backend_dir / ".env"
    
    if env_example.exists() and not env_file.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("⚠️  Please edit backend/.env with your configuration")
    
    print("✅ Backend setup complete!")
    return True


def setup_frontend():
    """Setup frontend environment"""
    print("\n⚛️  Setting up frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Install dependencies
    print("Installing Node.js dependencies...")
    if not run_command("npm install", cwd=frontend_dir):
        return False
    
    # Copy environment file
    env_example = frontend_dir / ".env.local.example"
    env_file = frontend_dir / ".env.local"
    
    if env_example.exists() and not env_file.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env.local file from template")
        print("⚠️  Please edit frontend/.env.local with your configuration")
    
    print("✅ Frontend setup complete!")
    return True


def print_next_steps():
    """Print next steps for the user"""
    print("\n🎉 Nura Phase 0 Foundation setup complete!")
    print("\n📋 Next Steps:")
    print("1. Configure environment variables:")
    print("   - Edit backend/.env with your database and API keys")
    print("   - Edit frontend/.env.local with your API URL")
    print("\n2. Start the development servers:")
    print("   Backend:  cd backend && uvicorn app.main:app --reload")
    print("   Frontend: cd frontend && npm run dev")
    print("\n3. Access the application:")
    print("   Frontend: http://localhost:3000")
    print("   Backend:  http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print("   Health:   http://localhost:8000/api/v1/health")
    print("\n4. Required Services:")
    print("   - MongoDB Atlas account and connection string")
    print("   - Qdrant Cloud account and API key")
    print("   - Groq API key for AI functionality")
    print("\n📚 Documentation: Check the docs/ folder for detailed guides")
    print("\n🚀 Happy coding!")


def main():
    """Main setup function"""
    print("🏥 Nura - AI-Powered Healthcare Assistant Platform")
    print("=================================================")
    print("Phase 0 Foundation Setup")
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please install missing tools.")
        sys.exit(1)
    
    # Setup backend
    if not setup_backend():
        print("\n❌ Backend setup failed.")
        sys.exit(1)
    
    # Setup frontend  
    if not setup_frontend():
        print("\n❌ Frontend setup failed.")
        sys.exit(1)
    
    # Print next steps
    print_next_steps()


if __name__ == "__main__":
    main()