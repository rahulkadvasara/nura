# Nura - Development Makefile
# Convenient commands for development workflow

.PHONY: help install setup-backend setup-frontend start-backend start-frontend start-dev test clean docker-up docker-down

# Default help command
help:
	@echo "Nura Development Commands"
	@echo "========================="
	@echo "install          - Install all dependencies"
	@echo "setup-backend    - Setup backend environment"
	@echo "setup-frontend   - Setup frontend environment"
	@echo "start-backend    - Start backend development server"
	@echo "start-frontend   - Start frontend development server"
	@echo "start-dev        - Start both backend and frontend"
	@echo "test             - Run all tests"
	@echo "clean            - Clean build artifacts"
	@echo "docker-up        - Start Docker development environment"
	@echo "docker-down      - Stop Docker development environment"

# Install all dependencies
install: setup-backend setup-frontend

# Backend setup
setup-backend:
	@echo "Setting up backend..."
	cd backend && python -m venv venv
	cd backend && venv/Scripts/activate && pip install -r requirements.txt
	@if not exist backend/.env copy backend/.env.example backend/.env
	@echo "Backend setup complete!"

# Frontend setup
setup-frontend:
	@echo "Setting up frontend..."
	cd frontend && npm install
	@if not exist frontend/.env.local copy frontend/.env.local.example frontend/.env.local
	@echo "Frontend setup complete!"

# Start backend server
start-backend:
	@echo "Starting backend server..."
	cd backend && venv/Scripts/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Start frontend server
start-frontend:
	@echo "Starting frontend server..."
	cd frontend && npm run dev

# Start both servers (requires separate terminals)
start-dev:
	@echo "Start backend and frontend in separate terminals:"
	@echo "Terminal 1: make start-backend"
	@echo "Terminal 2: make start-frontend"

# Run tests
test:
	@echo "Running backend tests..."
	cd backend && venv/Scripts/activate && pytest
	@echo "Running frontend tests..."
	cd frontend && npm run test

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@if exist backend/__pycache__ rmdir /s /q backend/__pycache__
	@if exist backend/.pytest_cache rmdir /s /q backend/.pytest_cache
	@if exist frontend/.next rmdir /s /q frontend/.next
	@if exist frontend/node_modules/.cache rmdir /s /q frontend/node_modules/.cache
	@echo "Clean complete!"

# Docker commands
docker-up:
	@echo "Starting Docker development environment..."
	docker-compose up -d
	@echo "Services available at:"
	@echo "Frontend: http://localhost:3000"
	@echo "Backend: http://localhost:8000"
	@echo "MongoDB: mongodb://admin:password@localhost:27017"

docker-down:
	@echo "Stopping Docker development environment..."
	docker-compose down

# Health check
health:
	@echo "Checking system health..."
	@curl -f http://localhost:8000/api/v1/health || echo "Backend not running"
	@curl -f http://localhost:3000 || echo "Frontend not running"