# Nura - AI-Powered Healthcare Assistant Platform

Nura is an AI-powered healthcare assistant platform designed to help patients manage their healthcare journey through intelligent assistance, medical report analysis, medication safety validation, appointment management, and personalized health insights.

## 🏗️ Architecture
  
- **Frontend:** Next.js 15 + TypeScript + Tailwind CSS
- **Backend:** FastAPI + Python
- **Database:** MongoDB Atlas (Primary) + Qdrant (Vector DB)
- **AI:** Groq + LangGraph Multi-Agent System
- **Authentication:** JWT + Google OAuth
- **Payments:** Razorpay
- **Storage:** Supabase Storage

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.11+
- MongoDB Atlas account
- Qdrant Cloud account
- Groq API key

### Backend Setup
 
1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Start the backend:**
   
   **Option 1 - Using the run script (Recommended):**
   ```bash
   python run.py
   ```
   
   **Option 2 - Using uvicorn directly:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   
   **Option 3 - Platform-specific scripts:**
   ```bash
   # Windows
   run.bat
   
   # Unix/Linux/macOS
   ./run.sh
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Setup environment variables:**
   ```bash
   cp .env.local.example .env.local
   # Edit .env.local with your configuration
   ```

4. **Start the frontend:**
   ```bash
   npm run dev
   ```

### Access the Application

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/api/v1/health

## 📝 Environment Variables

### Backend Required Variables

```env
# Core Configuration
SECRET_KEY=your_secret_key_here
MONGODB_URL=mongodb+srv://...
QDRANT_URL=https://...
QDRANT_API_KEY=your_key
GROQ_API_KEY=gsk_...
```

### Frontend Required Variables

```env
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_APP_NAME=Nura
```

## 🐳 Docker Support

### Backend
```bash
cd backend
docker build -t nura-backend .
docker run -p 8000:8000 --env-file .env nura-backend
```

### Frontend
```bash
cd frontend
docker build -t nura-frontend .
docker run -p 3000:3000 nura-frontend
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm run test
```

## 📁 Project Structure

```
nura/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API routes
│   │   ├── core/            # Configuration & security
│   │   ├── db/              # Database connections
│   │   ├── services/        # Business logic
│   │   ├── repositories/    # Data access layer
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── models/          # Data models
│   │   ├── agents/          # AI agents
│   │   └── utils/           # Utilities
│   ├── tests/               # Test suite
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile          # Docker configuration
│
├── frontend/
│   ├── src/
│   │   ├── app/             # Next.js app router
│   │   ├── components/      # React components
│   │   ├── features/        # Feature modules
│   │   ├── hooks/           # Custom hooks
│   │   ├── lib/             # Utilities & providers
│   │   ├── services/        # API services
│   │   ├── stores/          # Zustand stores
│   │   ├── types/           # TypeScript types
│   │   └── constants/       # Application constants
│   ├── package.json         # Node.js dependencies
│   └── Dockerfile          # Docker configuration
│
└── docs/                    # Documentation
```

## 🛡️ Security Features

- JWT-based authentication with refresh tokens
- Password hashing with bcrypt
- CORS configuration
- Input validation with Pydantic
- SQL injection prevention
- Rate limiting ready

## 🤖 AI System

Phase 0 includes the foundation for the multi-agent AI system:

- **Router Agent:** Intent classification
- **Retrieval Agent:** Context retrieval from vector DB
- **Specialized Agents:** Symptom analysis, medical knowledge, etc.
- **Memory Agent:** Long-term conversation memory

## 📊 Monitoring & Logging

- Structured JSON logging
- Health check endpoint with database status
- Application metrics ready
- Error tracking ready

## 🔄 Development Workflow

1. **Phase 0:** ✅ Foundation (Current)
2. **Phase 1:** Authentication System
3. **Phase 2:** Database Models & CRUD
4. **Phase 3:** Dashboard System
5. **Phase 4:** Doctor Management
6. **Phase 5:** Appointment System
7. **Phase 6:** Payment Integration
8. **Phase 7:** AI Infrastructure
9. **Phase 8:** RAG System
10. **Phase 9:** Multi-Agent System
11. **Phase 10:** Report Analysis
12. **Phase 11:** Drug Safety System
13. **Phase 12:** Production Deployment

## 📚 Documentation

- [Product Requirements Document](docs/PRD.md)
- [Technical Requirements Document](docs/TRD.md)
- [Backend Schema](docs/BACKEND_SCHEMA.md)
- [Implementation Plan](docs/IMPLEMENTATION_PLAN.md)
- [Agent Design](docs/AGENT_DESIGN.md)
- [Database Guide](docs/DATABASE_GUIDE.md)
- [API Contract](docs/API_CONTRACT.md)
- [Environment Variables](docs/ENVIRONMENT_VARIABLES.md)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is proprietary and confidential.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the documentation in the `/docs` folder
- Review the API documentation at `/docs` endpoint when backend is running

---

**Nura - Your Intelligent Healthcare Companion** 🏥✨