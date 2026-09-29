# SpeakQL Backend

SpeakQL is an enterprise-grade AI-powered database query interface. The backend is built with FastAPI and provides a secure, governed, and highly auditable pipeline for generating and executing SQL queries via LLMs (Large Language Models).

## 🌟 Key Features

- **AI-Powered Query Generation:** Integrates with Gemini and OpenAI to translate natural language into SQL using a ReAct agent loop.
- **Robust Governance & Security:**
  - **AST-Based SQL Validation:** Uses `sqlglot` to parse and validate SQL safely without vulnerable string-matching (protects against SQL injection and bypassing via comments).
  - **Policy Enforcement:** Blocks write operations, enforces row limits, restricts roles, and blocks specific keywords using deep AST inspection.
  - **Risk & Confidence Scoring:** Automatically scores generated queries for risk (e.g., cross-schema, full table scans) and LLM confidence.
  - **Approval Workflows:** High-risk or low-confidence queries automatically trigger approval requests before execution.
- **Enterprise Auth & RBAC:** JWT-based authentication with strict workspace-level Role-Based Access Control (Admin, Analyst, Viewer).
- **Tamper-Evident Audit Vault:** All actions (logins, query executions, exports, policy blocks) are cryptographically chained in a tamper-evident audit log.
- **Dynamic Masking & Sensitivity:** Data masking applied automatically based on column-level sensitivity rules.
- **Data Catalog & Reporting:** Integrated business glossary, metric definitions, and automated background report scheduling.

## 🛠️ Tech Stack

- **Framework:** FastAPI
- **Database ORM:** SQLModel (SQLAlchemy 2.0 under the hood) + Asyncpg
- **SQL Parser:** `sqlglot` (for safe AST manipulation and validation)
- **AI Integration:** `google-generativeai`, `openai`
- **Security:** `python-jose` (JWT), `bcrypt` / `argon2-cffi` (Password Hashing), `cryptography` (Fernet)

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL database
- (Optional) `argon2-cffi` for enhanced password security

### 1. Installation

```bash
# Clone the repository and navigate to the backend directory
cd backend

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the `backend/` directory. **Never use the default `JWT_SECRET_KEY` or `FERNET_KEY` in production.** The application will refuse to start in production if insecure defaults are detected.

```env
# Application
ENV=dev # Set to 'prod' or 'production' in deployment
DEBUG=True

# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/speakql
SQL_ECHO=False

# Security (MUST BE SET IN PROD)
JWT_SECRET_KEY=your_secure_random_jwt_key
FERNET_KEY=your_secure_fernet_key # Generate via cryptography.fernet.Fernet.generate_key()
ACCESS_TOKEN_EXPIRE_MINUTES=60

# AI Providers
GEMINI_API_KEY=your_gemini_api_key
OPENAI_API_KEY=your_openai_api_key
```

### 3. Running the Server

Start the FastAPI server using Uvicorn:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API documentation will be available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📂 Architecture & Structure

```
backend/
├── auth/           # Authentication guards and JWT bearer dependencies
├── core/           # App configuration, context, and logging setup
├── middleware/     # Request context middleware (request IDs)
├── models/         # SQLModel database schemas (User, Tenant, Audit, Workflow, etc.)
├── repositories/   # Database access layer (CRUD operations, isolating DB logic)
├── routers/        # FastAPI endpoint definitions (Agent, Auth, Governance, etc.)
├── schemas/        # Pydantic models for request/response validation
├── services/       # Core business logic and governance pipeline
└── utils/          # LLM Agents, AST parsers, SQL safety tools, and helpers
```

## 🔒 Security Notes

This backend has been recently hardened against several vulnerabilities:
- **No Direct Session Access:** Services strictly use repositories to prevent session leakage.
- **Timezone-Aware:** Fully utilizes timezone-aware `datetime.now(timezone.utc)` for reliable distributed timestamping.
- **Safe DB Connections:** Connection pooling with pre-ping enabled to prevent stale connections under load.
- **Race-Condition Safe Audits:** Cryptographic audit chains use PostgreSQL `FOR UPDATE` advisory locks to serialize concurrent audit events safely.
- **Strict CORS:** Defaults to strict method and header exposure rather than wildcard allowances.
