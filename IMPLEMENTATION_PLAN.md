# Implementation Plan: Chat Data Platform

**Worktree**: `.worktrees/implement`
**Branch**: `implement`
**Date**: 2026-01-29

---

## Phase 1: Project Foundation (Days 1-3)

### 1.1 Initialize Project Structure

```
chat-data-platform/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # Application entry point
│   │   ├── config.py          # Settings
│   │   ├── api/               # Route handlers
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── datasets.py
│   │   │   └── chat.py
│   │   ├── core/              # Core utilities
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   └── database.py
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── dataset.py
│   │   │   └── conversation.py
│   │   ├── schemas/           # Pydantic schemas
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   └── dataset.py
│   │   └── services/          # Business logic
│   │       ├── __init__.py
│   │       ├── ai_service.py
│   │       └── dataset_service.py
│   ├── tests/
│   │   └── __init__.py
│   ├── requirements.txt
│   └── pyproject.toml
│
└── frontend/                  # React frontend
    ├── src/
    │   ├── App.tsx
    │   ├── main.tsx
    │   ├── api/              # API client
    │   ├── pages/            # Page components
    │   └── components/       # Reusable components
    ├── package.json
    └── vite.config.ts
```

### 1.2 Backend Dependencies (`requirements.txt`)

```
fastapi==0.109.0
uvicorn[standard]==0.27.0
sqlalchemy==2.0.25
alembic==1.13.1
pydantic==2.5.3
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
aiofiles==23.2.1
openai==1.12.0
langchain==0.1.5
pandas==2.1.4
celery==5.3.4
redis==5.0.1
minio==7.2.0
python-dotenv==1.0.0
pytest==7.4.4
pytest-asyncio==0.23.3
httpx==0.26.0
```

### 1.3 Frontend Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.21.0",
    "antd": "^5.12.0",
    "@ant-design/icons": "^5.2.6",
    "axios": "^1.6.2",
    "echarts": "^5.4.3",
    "echarts-for-react": "^3.0.2"
  },
  "devDependencies": {
    "@types/react": "^18.2.45",
    "@types/react-dom": "^18.2.18",
    "@vitejs/plugin-react": "^4.2.1",
    "typescript": "^5.3.3",
    "vite": "^5.0.10"
  }
}
```

---

## Phase 2: Core Backend (Days 4-7)

### 2.1 Database Models

#### User Model
- UUID primary key
- email (unique, indexed)
- username
- password_hash
- is_active
- created_at, updated_at

#### Team Model
- UUID primary key
- name
- created_at

#### TeamMember (Association)
- team_id, user_id (composite PK)
- role ('owner', 'admin', 'member')

#### Dataset Model
- UUID primary key
- name, description
- file_path (MinIO path)
- file_size, file_type
- owner_id, team_id (optional)
- is_public
- metadata (JSONB)
- created_at, updated_at

#### DatasetColumn Model
- UUID primary key
- dataset_id (FK)
- name, data_type
- nullable
- statistics (JSONB)
- sample_values (JSONB)

#### Conversation Model
- UUID primary key
- dataset_id (FK, nullable)
- user_id (FK)
- title
- created_at, updated_at

#### Message Model
- UUID primary key
- conversation_id (FK)
- role ('user', 'assistant')
- content (text)
- code_result (JSONB, nullable)
- created_at

### 2.2 API Endpoints (MVP)

#### Auth
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login, return JWT
- `POST /auth/refresh` - Refresh token
- `GET /auth/me` - Get current user

#### Datasets
- `POST /datasets/upload` - Upload file
- `GET /datasets` - List user's datasets
- `GET /datasets/{id}` - Get dataset with metadata
- `DELETE /datasets/{id}` - Delete dataset

#### Chat
- `POST /conversations` - Create new conversation
- `POST /conversations/{id}/chat` - Send message
- `GET /conversations/{id}` - Get conversation history

### 2.3 AI Service (Basic)

```python
# app/services/ai_service.py

class AIService:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    async def generate_response(
        self,
        user_message: str,
        dataset_metadata: dict,
        conversation_history: list
    ) -> dict:
        """Generate AI response with code execution capability."""

        # Build context from dataset metadata
        context = self._build_context(dataset_metadata)

        # Build conversation history
        messages = self._build_messages(
            user_message,
            context,
            conversation_history
        )

        # Call LLM
        response = await self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            temperature=0.7
        )

        return {
            "content": response.choices[0].message.content,
            "role": "assistant"
        }
```

---

## Phase 3: Data Processing (Days 8-12)

### 3.1 Dataset Upload & Parsing

```python
# app/services/dataset_service.py

class DatasetService:
    async def upload_dataset(
        self,
        file: UploadFile,
        user_id: UUID,
        team_id: UUID | None = None
    ) -> Dataset:
        """Upload and process dataset file."""

        # Upload to MinIO
        file_path = await self._upload_to_minio(file)

        # Parse and extract metadata
        metadata = await self._extract_metadata(file_path)

        # Save to database
        dataset = await self._create_dataset_record(
            file.filename,
            file_path,
            metadata,
            user_id,
            team_id
        )

        # Queue background task for full analysis
        await self._queue_analysis_task(dataset.id)

        return dataset

    async def _extract_metadata(self, file_path: str) -> dict:
        """Extract schema and statistics from data file."""

        # Use pandas for initial parsing
        df = await run_in_executor(
            lambda: pd.read_csv(file_path, nrows=1000)
        )

        # Generate column statistics
        statistics = {}
        for col in df.columns:
            statistics[col] = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isna().sum()),
                "null_rate": float(df[col].isna().mean()),
                "unique_count": int(df[col].nunique()),
                "sample_values": df[col].dropna().head(5).tolist()
            }

            # Numeric column statistics
            if pd.api.types.is_numeric_dtype(df[col]):
                statistics[col].update({
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean()),
                    "std": float(df[col].std())
                })

        return {
            "columns": list(df.columns),
            "row_count": len(df),
            "statistics": statistics
        }
```

### 3.2 Data Cleaning Service

```python
# app/services/cleaning_service.py

class DataCleaningService:
    """AI-assisted data cleaning."""

    async def suggest_cleaning_strategy(
        self,
        dataset_id: UUID
    ) -> dict:
        """Analyze data and suggest cleaning strategies."""

        # Get column statistics
        columns = await self._get_column_stats(dataset_id)

        suggestions = []

        for col in columns:
            # Missing value strategy
            if col.statistics.null_rate > 0:
                strategy = self._suggest_missing_value_strategy(col)
                suggestions.append({
                    "column": col.name,
                    "issue": "missing_values",
                    "strategy": strategy
                })

            # Outlier detection
            if col.is_numeric:
                outliers = self._detect_outliers(col)
                if outliers > 0:
                    suggestions.append({
                        "column": col.name,
                        "issue": "outliers",
                        "count": outliers,
                        "strategy": "IQR method recommended"
                    })

        return {"suggestions": suggestions}

    async def execute_cleaning(
        self,
        dataset_id: UUID,
        operations: list[dict]
    ) -> str:
        """Execute cleaning operations and return new file path."""

        # Generate cleaning code
        code = self._generate_cleaning_code(dataset_id, operations)

        # Execute in sandbox
        result = await self._execute_code(code)

        # Save cleaned file
        cleaned_path = await self._save_cleaned_file(dataset_id, result)

        return cleaned_path
```

---

## Phase 4: AI Chat Enhancement (Days 13-17)

### 4.1 Enhanced System Prompt

```python
SYSTEM_PROMPT = """You are an expert data analysis assistant. Your role is to help
users explore, clean, analyze, and visualize their datasets.

## Current Dataset Context
- Dataset: {dataset_name}
- Columns: {columns}
- Data Types: {dtypes}
- Rows: {row_count}

## Column Details
{column_details}

## Guidelines
1. Always load data using pandas before analysis
2. Generate clean, executable Python code
3. Use matplotlib or plotly for visualizations
4. Explain your reasoning and findings clearly
5. Suggest relevant follow-up analyses
6. For visualizations, save to /tmp and return the path

## Safety Rules
- Never access file system, network, or environment variables
- Never modify the original data file
- Handle errors gracefully with clear error messages
- Maximum execution time: 60 seconds

## Output Format
Always respond in this format:
1. Your analysis/explanation
2. Python code block (if code is needed)
3. Summary of findings

User's message: {user_message}
"""
```

### 4.2 Code Execution Sandbox

```python
# app/services/code_executor.py

import asyncio
import signal
import os
from concurrent.futures import ThreadPoolExecutor

class CodeExecutor:
    """Sandboxed code execution environment."""

    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.executor = ThreadPoolExecutor(max_workers=4)

    async def execute(
        self,
        code: str,
        dataset_path: str
    ) -> dict:
        """Execute code in sandboxed environment."""

        # Prepare execution context
        context = {
            "dataset_path": dataset_path,
            "output_dir": "/tmp/visualizations"
        }

        # Create execution function
        async def run_code():
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self.executor,
                lambda: self._safe_execute(code, context)
            )

        try:
            result = await asyncio.wait_for(
                run_code(),
                timeout=self.timeout
            )
            return result
        except asyncio.TimeoutError:
            return {"error": "Execution timed out"}

    def _safe_execute(self, code: str, context: dict) -> dict:
        """Execute code with safety restrictions."""
        import pandas as pd
        import matplotlib.pyplot as plt
        import json

        # Restricted globals
        restricted_globals = {
            "pd": pd,
            "plt": plt,
            "json": json,
            "print": print,
            "__builtins__": {
                "len": len,
                "str": str,
                "int": int,
                "float": float,
                "list": list,
                "dict": dict,
                "range": range,
                "enumerate": enumerate,
            }
        }

        # Load dataset
        df = pd.read_csv(context["dataset_path"])

        # Execute user code
        exec(code, restricted_globals)

        return {
            "success": True,
            "dataframe_info": {
                "shape": df.shape,
                "columns": list(df.columns)
            }
        }
```

---

## Phase 5: Frontend Development (Days 18-24)

### 5.1 Page Structure

```
src/pages/
├── Login.tsx              # Login/Register page
├── Dashboard.tsx          # Main dashboard
├── DatasetList.tsx        # Dataset management
├── DatasetDetail.tsx      # Dataset view + metadata
└── Analysis.tsx           # AI chat interface
    ├── ChatPanel.tsx      # Conversation
    ├── CodePanel.tsx      # Generated code display
    └── Visualization.tsx  # Charts display
```

### 5.2 Key Components

#### Dataset Upload Component
- Drag & drop file upload
- Format validation
- Progress indicator
- Preview table

#### AI Chat Component
- Message list with syntax highlighting
- Code blocks with copy button
- Visualization display
- Markdown support

#### Data Preview Component
- Paginated table view
- Column statistics sidebar
- Data type indicators

---

## Phase 6: Testing & Polish (Days 25-30)

### 6.1 Test Coverage Requirements

| Module | Coverage Target |
|--------|----------------|
| Core API | 80%+ |
| Services | 70%+ |
| AI Integration | 60%+ |

### 6.2 Test Types

- **Unit Tests**: Individual functions and classes
- **Integration Tests**: API endpoints with test database
- **E2E Tests**: Critical user flows (login, upload, analyze)

---

## Task Checklist

### Phase 1: Foundation
- [ ] Initialize backend project structure
- [ ] Initialize frontend project structure
- [ ] Set up database configuration
- [ ] Create basic config.yaml

### Phase 2: Core Backend
- [ ] Implement User model and auth endpoints
- [ ] Implement Team model and collaboration
- [ ] Implement Dataset CRUD endpoints
- [ ] Set up JWT authentication
- [ ] Configure MinIO client

### Phase 3: Data Processing
- [ ] Implement file upload to MinIO
- [ ] Implement pandas metadata extraction
- [ ] Create background task queue (Celery)
- [ ] Implement data cleaning suggestions

### Phase 4: AI Chat
- [ ] Set up OpenAI/DeepSeek integration
- [ ] Implement prompt template system
- [ ] Create code execution sandbox
- [ ] Implement conversation storage

### Phase 5: Frontend
- [ ] Implement authentication pages
- [ ] Create dataset management UI
- [ ] Build AI chat interface
- [ ] Add visualization display

### Phase 6: Testing
- [ ] Write unit tests for core logic
- [ ] Write integration tests for APIs
- [ ] Perform E2E testing
- [ ] Fix bugs and polish UI

---

## Estimated Timeline

| Phase | Duration | Milestone |
|-------|----------|-----------|
| Phase 1 | 3 days | Project structure ready |
| Phase 2 | 4 days | Core APIs working |
| Phase 3 | 5 days | Data upload + cleaning |
| Phase 4 | 5 days | AI chat functional |
| Phase 5 | 7 days | Frontend complete |
| Phase 6 | 6 days | Testing + polish |
| **Total** | **30 days** | **MVP complete** |

---

## Next Steps

1. Review this implementation plan
2. Begin Phase 1: Initialize project structure
