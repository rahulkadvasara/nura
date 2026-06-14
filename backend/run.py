#!/usr/bin/env python3
"""
Nura Backend - Development Server Runner
Simple script to start the FastAPI development server
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if required environment variables are set"""
    env_file = backend_dir / ".env"
    
    if not env_file.exists():
        logger.error("❌ .env file not found")
        logger.info("💡 Copy .env.example to .env and configure your settings")
        return False
    
    # Check for critical environment variables
    critical_vars = ['SECRET_KEY', 'MONGODB_URL', 'QDRANT_URL', 'QDRANT_API_KEY', 'GROQ_API_KEY']
    missing_vars = []
    
    # Load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
    except ImportError:
        logger.warning("⚠️  python-dotenv not installed, skipping .env validation")
        return True
    
    for var in critical_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        logger.info("💡 Please update your .env file with the missing variables")
        return False
    
    logger.info("✅ Environment configuration looks good")
    return True


def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import fastapi
        import uvicorn
        import motor
        import qdrant_client
        logger.info("✅ Core dependencies are installed")
        return True
    except ImportError as e:
        logger.error(f"❌ Missing dependency: {e}")
        logger.info("💡 Run: pip install -r requirements.txt")
        return False


def start_server(host="0.0.0.0", port=8000, reload=True):
    """Start the FastAPI development server"""
    logger.info("🚀 Starting Nura Backend Server...")
    logger.info(f"📍 Server will be available at: http://{host}:{port}")
    logger.info(f"📚 API Documentation: http://{host}:{port}/docs")
    logger.info(f"🔍 Health Check: http://{host}:{port}/api/v1/health")
    logger.info("🛑 Press Ctrl+C to stop the server")
    
    try:
        # Start uvicorn server
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("\n🛑 Server stopped by user")
    except Exception as e:
        logger.error(f"❌ Server failed to start: {e}")
        sys.exit(1)


def main():
    """Main function"""
    print("🏥 Nura Backend - Development Server")
    print("====================================")
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Check environment
    if not check_environment():
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Parse command line arguments
    host = "0.0.0.0"
    port = 8000
    reload = True
    
    if len(sys.argv) > 1:
        if "--help" in sys.argv or "-h" in sys.argv:
            print("\nUsage: python run.py [options]")
            print("Options:")
            print("  --host HOST     Bind socket to this host (default: 0.0.0.0)")
            print("  --port PORT     Bind socket to this port (default: 8000)")
            print("  --no-reload     Disable auto-reload")
            print("  --help, -h      Show this help message")
            return
        
        for i, arg in enumerate(sys.argv[1:], 1):
            if arg == "--host" and i + 1 < len(sys.argv):
                host = sys.argv[i + 1]
            elif arg == "--port" and i + 1 < len(sys.argv):
                try:
                    port = int(sys.argv[i + 1])
                except ValueError:
                    logger.error("❌ Port must be a number")
                    sys.exit(1)
            elif arg == "--no-reload":
                reload = False
    
    # Start the server
    start_server(host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()