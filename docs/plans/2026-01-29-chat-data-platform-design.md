# Chat Data Platform - Design Document

**Date**: 2026-01-29
**Status**: Draft
**Version**: 1.0

---

## 1. Overview

### 1.1 Project Description

A web-based platform that wraps Python data analysis capabilities through AI-powered conversations. Users can upload datasets and perform data processing, analysis, and mining with AI assistance, generating reports.

The system fully leverages AI's inherent knowledge to provide capabilities such as data analysis solution design.

### 1.2 Core Principles

- AI as an active collaborator, not just a code generator
- Secure data handling with multi-tenant isolation
- Support for GB-scale data processing
- Team collaboration with dataset sharing

---

## 2. Architecture

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend Layer                          │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐ │
│  │  Dataset  │  │  AI Chat  │  │Visualization│ │  Report   │ │
│  │Management │  │  Session  │  │  Display  │  │  Viewer   │ │
│  └───────────┘  └───────────┘  └───────────┘  └───────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     Backend Layer (FastAPI)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │User/Auth Svc│  │Dataset Svc  │  │AI Chat Svc  │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │Task Scheduler│ │Visualization│ │Report Gen   │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ File Storage  │    │   Database    │    │  AI Service   │
│   (MinIO/S3)  │    │ (PostgreSQL)  │    │  (DeepSeek)   │
└───────────────┘    └───────────────┘    └───────────────┘
```

### 2.2 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Backend Framework | FastAPI | High performance, async,API support |
| native Open AI SDK | LangChain / OpenAI SDK | Mature ecosystem, unified abstraction |
| Data Analysis | Pandas + Polars | Pandas ecosystem, Polars for performance |
| Database | PostgreSQL + MinIO | Powerful queries, S3-compatible storage |
| Task Queue | Celery + Redis | Distributed tasks, async processing |
| Frontend | React + Ant Design | Rich components, strong data tables |
| Visualization | ECharts / Plotly | Interactive, rich chart types |
| Code Sandbox | Docker + eBPF | Code isolation, security control |

---

## 3. Core Components

### 3.1 AI Chat Service

**Responsibilities**:
- Receive natural language requests from users
- Generate Python code using dataset metadata
- Execute code in sandboxed environment
- Return results to users with visualization

**Key Mechanisms**:
- System prompt design with role definition and constraints
- Context building with dataset schema and conversation history
- Static code analysis before execution
- Result caching for identical queries

### 3.2 Dataset Service

**Responsibilities**:
- Manage file upload, storage, and versioning
- Parse data and infer schema
- Generate statistical summaries for AI context
- Handle dataset sharing and permissions

**Data Flow**:
1. User uploads CSV/Excel file
2. System validates format
3. Parse and sample data to infer schema
4. Extract metadata and statistical summary
5. Store in MinIO, metadata in PostgreSQL

### 3.3 Task Scheduler

**Responsibilities**:
- Handle long-running analysis tasks
- Distribute tasks across workers
- Track task status and results
- Support modeling and batch processing

---

## 4. Functional Modules

### 4.1 Data Cleaning & Preprocessing (Priority 1)

| Feature | Description | AI Capability |
|---------|-------------|---------------|
| Missing Value Handling | Detection, imputation, deletion | AI suggests optimal strategies per data type |
| Outlier Detection | IQR, Z-score, Isolation Forest | AI recommends methods and explains reasoning |
| Data Type Conversion | Auto-inference, manual specification | AI analyzes distributions for appropriate types |
| Deduplication & Merging | Duplicate detection, table joins | AI generates merge strategy suggestions |
| Feature Engineering | Encoding, standardization | AI suggests features based on business context |

### 4.2 Data Exploration & Visualization (Priority 2)

| Feature | Description | AI Capability |
|---------|-------------|---------------|
| Statistical Summary | Descriptive statistics | AI automatically interprets results |
| Correlation Analysis | Correlation coefficients, heatmaps | AI identifies key relationships |
| Time Series Analysis | Trend, seasonality, decomposition | AI discovers periodic patterns |
| Smart Charts | One-click visualization | AI recommends best chart types |
| Interactive Exploration | Drill-down, filtering | AI guides exploration direction |

### 4.3 Analysis & Modeling (Priority 3)

| Feature | Description |
|---------|-------------|
| Statistical Tests | Hypothesis testing, A/B testing |
| Regression Analysis | Linear, logistic, polynomial |
| Classification | Decision trees, random forests, clustering |
| Time Series Forecasting | ARIMA, Prophet, LSTM |

### 4.4 Report Generation (Priority 4)

| Feature | Description |
|---------|-------------|
| Markdown Reports | Structured analysis summary |
| PDF Export | Printable formatted reports |
| Chart Embedding | Inline visualizations |

---

## 5. Data Model

### 5.1 PostgreSQL Schema

```sql
-- Users table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Teams table
CREATE TABLE teams (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Team members (many-to-many)
CREATE TABLE team_members (
    team_id UUID REFERENCES teams(id),
    user_id UUID REFERENCES users(id),
    role VARCHAR(50) DEFAULT 'member',
    PRIMARY KEY (team_id, user_id)
);

-- Datasets table
CREATE TABLE datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    file_type VARCHAR(50),
    owner_id UUID REFERENCES users(id),
    team_id UUID REFERENCES teams(id),
    is_public BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Dataset columns with statistics
CREATE TABLE dataset_columns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    data_type VARCHAR(50),
    nullable BOOLEAN,
    statistics JSONB,
    sample_values JSONB,
    position INTEGER
);

-- Conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id),
    user_id UUID REFERENCES users(id),
    title VARCHAR(500),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    code_result JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Reports table
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dataset_id UUID REFERENCES datasets(id),
    user_id UUID REFERENCES users(id),
    title VARCHAR(500),
    content JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Analysis tasks table
CREATE TABLE analysis_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    dataset_id UUID REFERENCES datasets(id),
    task_type VARCHAR(100) NOT NULL,
    parameters JSONB,
    status VARCHAR(50) DEFAULT 'pending',
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### 5.2 MinIO/S3 Storage Structure

```
{tenant_id}/
├── datasets/
│   ├── {dataset_id}/
│   │   ├── data.csv           (original data)
│   │   ├── cleaned.csv        (cleaned data)
│   │   └── versions/
│   │       ├── v1/
│   │       ├── v2/
│   │       └── ...
│   └── ...
└── reports/
    └── {report_id}/
        └── report.pdf
```

---

## 6. API Design

### 6.1 Authentication

```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

### 6.2 Dataset Management

```
POST   /api/v1/datasets/upload           # Upload dataset
GET    /api/v1/datasets                  # List (with filtering)
GET    /api/v1/datasets/{id}             # Detail + metadata
PUT    /api/v1/datasets/{id}             # Update metadata
DELETE /api/v1/datasets/{id}             # Delete
GET    /api/v1/datasets/{id}/sample      # Sample preview
POST   /api/v1/datasets/{id}/share       # Share dataset
GET    /api/v1/datasets/public           # Public datasets
```

### 6.3 AI Conversation

```
POST   /api/v1/conversations             # Create session
GET    /api/v1/conversations/{id}        # Get history
POST   /api/v1/conversations/{id}/chat   # Send message
        Body: { "message": "...", "code_execution": true/false }
DELETE /api/v1/conversations/{id}        # End session
GET    /api/v1/conversations/{id}/code   # Get generated code
```

### 6.4 Analysis Tasks (Async)

```
POST   /api/v1/tasks                     # Create task
GET    /api/v1/tasks/{id}                # Status query
GET    /api/v1/tasks/{id}/result         # Get result
GET    /api/v1/tasks                     # List user's tasks
```

### 6.5 Reports

```
GET    /api/v1/reports                   # List
GET    /api/v1/reports/{id}              # Detail
POST   /api/v1/reports/generate          # Generate from conversation
DELETE /api/v1/reports/{id}              # Delete
```

---

## 7. Security Design

### 7.1 Authentication & Authorization

| Layer | Measure |
|-------|---------|
| Authentication | JWT Token + Refresh mechanism |
| Authorization | RBAC (User/Admin/Super Admin) |
| Data Isolation | Tenant ID + User ID double isolation |

### 7.2 AI Code Sandbox

- **Pre-execution analysis**: Static code analysis to prevent dangerous operations
- **Runtime restrictions**: No os/network/file system access
- **Timeout**: Maximum execution time limits
- **Resource limits**: Memory and CPU constraints

### 7.3 Sensitive Data Protection

- PII automatic detection and masking
- Regex patterns for common PII (email, phone, SSN)
- AI-assisted PII identification

---

## 8. GB-Level Data Processing Strategy

| Strategy | Description |
|----------|-------------|
| Sampling Analysis | AI analyzes sample data first, then executes on full dataset |
| Incremental Processing | Long tasks use Celery sharding |
| Result Caching | Cache identical query results |
| Columnar Storage | Consider Parquet format for large datasets |

---

## 9. Implementation Phases

### Phase 1: Core Foundation
- User authentication system
- Basic dataset upload and storage
- Simple AI chat interface
- Minimal viable product

### Phase 2: Data Processing
- Data cleaning module
- Missing value and outlier handling
- Basic visualization

### Phase 3: Advanced Features
- Complex analysis capabilities
- Report generation
- Team collaboration features

### Phase 4: Optimization
- Performance tuning
- Enhanced AI prompts
- Additional visualization options

---

## 10. Open Questions

1. Should real-time collaboration (multiple users in same conversation) be supported?
2. Are there specific compliance requirements for data storage (e.g., GDPR)?
3. Should there be limits on storage per user/team?
4. Is there a need for data lineage tracking?

---

## Appendix: AI Prompt Template

```
You are a professional data analysis assistant. Your role is to help users
explore, clean, analyze, and visualize their datasets.

## Context
- Current Dataset: {dataset_name}
- Columns: {column_list}
- Data Types: {column_types}
- Statistical Summary: {statistics}

## Guidelines
1. Always load data before analysis
2. Generate clean, executable Python code
3. Use matplotlib/plotly for visualizations
4. Explain your reasoning and findings
5. Suggest follow-up analyses when relevant

## Safety Rules
- Never access file system or network
- Never modify original data without user confirmation
- Handle errors gracefully with clear messages

## Current Task
{user_message}
```
