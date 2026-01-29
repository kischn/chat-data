# Chat Data Platform

AI-powered data analysis platform with natural language interface.

## Features

- **Dataset Management**: Upload and manage CSV, Excel, JSON files
- **AI Chat**: Ask questions about your data in natural language
- **Data Cleaning**: AI-powered suggestions for missing values, outliers, and data type issues
- **Visualization**: Generate charts through conversation
- **Team Collaboration**: Share datasets and work together
- **Secure Execution**: Sandboxed code execution environment

## Tech Stack

- **Backend**: FastAPI + Python
- **Database**: PostgreSQL + SQLAlchemy
- **Storage**: MinIO (S3-compatible)
- **AI**: DeepSeek (OpenAI-compatible API)
- **Frontend**: React + Ant Design + ECharts
- **Task Queue**: Celery + Redis

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
- PostgreSQL
- Redis
- MinIO

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
alembic upgrade head

# Start server
python -m uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Environment Variables

### Backend (.env)

```env
# Application
SECRET_KEY=your-secret-key
DEBUG=true

# Database
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=postgres
DB_NAME=chat_data

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET=chat-data

# AI Service (DeepSeek)
AI_API_KEY=your-deepseek-api-key
AI_BASE_URL=https://api.deepseek.com
```

## API Documentation

Once the backend is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
chat-data-platform/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core utilities (DB, security)
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   ├── services/      # Business logic
│   │   └── main.py        # FastAPI app
│   ├── config.yaml        # Configuration
│   └── requirements.txt
│
└── frontend/
    ├── src/
    │   ├── api/           # API client
    │   ├── pages/         # Page components
    │   ├── components/    # Reusable components
    │   └── App.tsx        # Main app
    └── package.json
```

## License

MIT
