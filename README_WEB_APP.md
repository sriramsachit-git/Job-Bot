# Job Search Pipeline - Web Application

A modern web-based job search pipeline with automated resume generation, built with FastAPI and React.

## 🏗️ Architecture

- **Backend**: FastAPI with SQLAlchemy (async)
- **Frontend**: React + TypeScript + Vite
- **Database**: SQLite (can be upgraded to PostgreSQL)
- **Styling**: Tailwind CSS + Shadcn/ui components
- **State Management**: React Query (TanStack Query)

## 📁 Project Structure

```
job_search_pipeline/
├── backend/
│   ├── app/
│   │   ├── api/routes/      # API endpoints
│   │   ├── core/            # Pipeline orchestrator
│   │   ├── models/         # SQLAlchemy models
│   │   ├── schemas/         # Pydantic schemas
│   │   └── services/        # Business logic
│   ├── data/               # Database and config files
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── components/      # React components
    │   ├── pages/           # Page components
    │   ├── services/         # API client
    │   └── types/            # TypeScript types
    └── package.json
```

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- Google Custom Search API key
- OpenAI API key

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Initialize database:**
   ```bash
   python -c "from app.database import init_db; import asyncio; asyncio.run(init_db())"
   ```

6. **Run backend:**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
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

3. **Run development server:**
   ```bash
   npm run dev
   ```

4. **Open browser:**
   ```
   http://localhost:3000
   ```

## 📋 Features

### ✅ Completed

- [x] FastAPI backend with async support
- [x] SQLAlchemy database models
- [x] RESTful API endpoints
- [x] WebSocket support for real-time updates
- [x] React frontend with TypeScript
- [x] Tailwind CSS + Shadcn/ui components
- [x] Dashboard with statistics
- [x] Multi-step search wizard
- [x] Real-time search progress
- [x] Job filtering, sorting, and pagination
- [x] Resume generation
- [x] Cloud storage integration (S3/GCS/R2)

### 🔄 In Progress

- [ ] Settings page enhancements
- [ ] Docker configuration
- [ ] Production deployment guide

## 🔌 API Endpoints

### Dashboard
- `GET /api/dashboard/stats` - Get dashboard statistics
- `GET /api/dashboard/recent-jobs` - Get recent jobs

### Jobs
- `GET /api/jobs` - List jobs (with filtering/pagination)
- `GET /api/jobs/{id}` - Get job details
- `PATCH /api/jobs/{id}` - Update job
- `DELETE /api/jobs/{id}` - Delete job

### Search
- `POST /api/search/start` - Start new search
- `GET /api/search/{id}/status` - Get search status
- `GET /api/search/{id}/results` - Get search results
- `POST /api/search/cancel/{id}` - Cancel search
- `WS /api/search/ws/{id}` - WebSocket for real-time updates

### Resumes
- `POST /api/resumes` - Generate resume
- `POST /api/resumes/bulk-generate` - Bulk generate
- `GET /api/resumes` - List resumes
- `GET /api/resumes/{id}` - Get resume
- `DELETE /api/resumes/{id}` - Delete resume

### Settings
- `GET /api/settings` - Get settings
- `PUT /api/settings` - Update settings

## 🎨 Frontend Routes

- `/` - Dashboard
- `/search/new` - New search wizard
- `/jobs/:id` - Job details
- `/settings` - Settings page

## 🔧 Configuration

### Environment Variables

**Backend (.env):**
```env
GOOGLE_API_KEY=your_key
GOOGLE_CSE_ID=your_id
OPENAI_API_KEY=your_key
DATABASE_URL=sqlite+aiosqlite:///./data/jobs.db
CLOUD_STORAGE_PROVIDER=local  # or s3, gcs, r2
```

**Frontend:**
- API proxy configured in `vite.config.ts`
- Backend URL: `http://localhost:8000`

## 🐳 Docker Deployment

Coming soon - Docker configuration will be added.

## 📝 Notes

- The backend uses async SQLAlchemy for better performance
- WebSocket updates are polled every 2 seconds as fallback
- Resume generation requires `data/resume_config.yaml` and `data/projects.json`
- Cloud storage is optional (defaults to local file serving)

## 🐛 Troubleshooting

1. **Database errors**: Ensure `backend/data/` directory exists
2. **API connection**: Check CORS settings in `backend/app/main.py`
3. **WebSocket issues**: Verify WebSocket proxy in `vite.config.ts`
4. **Resume generation**: Ensure LaTeX is installed for PDF compilation

## 📚 Documentation

- API docs available at: `http://localhost:8000/docs`
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
