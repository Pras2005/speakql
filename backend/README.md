# SpeakQL Backend

SpeakQL is an enterprise-grade AI-powered database query interface. The backend is built with FastAPI and provides a secure, governed, and highly auditable pipeline for generating and executing SQL queries via LLMs (Large Language Models).

Unlike standard "text-to-SQL" wrappers that blindly trust LLM outputs, SpeakQL is built on a **Zero-Trust Security Architecture** and an **Autonomous Agentic Workflow**.

---

## 🛡️ Zero-Trust Security Architecture

SpeakQL treats the LLM as an *untrusted user* and wraps it in a multi-layered security mesh:

- **AST-Level SQL Firewall (`sqlglot`)**
  Instead of using fragile regular expressions to block dangerous commands (which can be bypassed via comments or aliases), SpeakQL parses the LLM's output into an Abstract Syntax Tree (AST). It mathematically proves whether a query is a read or a write operation by analyzing the tree nodes. If a policy dictates a row limit, the backend injects the limit directly into the AST, ensuring it cannot be circumvented by malicious subqueries.
- **Cryptographic Tamper-Evident Audit Vault**
  Every execution, approval, and policy block is hashed (SHA-256) together with the hash of the *previous* event in a blockchain-style chain. Using PostgreSQL advisory row-locks (`SELECT ... FOR UPDATE`), the system guarantees the chain remains intact even under massive concurrent loads. Any manual tampering with the database logs instantly breaks the chain, triggering `verify_chain` alerts.
- **Dynamic, Late-Binding Data Masking**
  Query execution is separated from data delivery. The `MaskingService` intercepts the result set *after* execution but *before* returning it to the user. It evaluates column-level sensitivity rules and applies dynamic redaction (e.g., masking emails or hashing SSNs) strictly based on the RBAC level of the requesting user.
- **Zero-Leakage Asynchronous Context**
  Leverages Python's `contextvars` to maintain a strict `RequestContext` across the async pipeline, guaranteeing that multi-tenant boundaries (Org, Workspace, User) are inherently bound to the executing task without risking cross-tenant data leakage under high concurrency.

---

## 🧠 Autonomous Agentic Workflow

SpeakQL operates as a true **Agentic ReAct (Reason + Act) Loop**, acting like a human data analyst rather than a zero-shot generator.

- **Iterative Schema Exploration (Tool Calling)**
  Instead of cramming a massive schema into a single LLM prompt, the `DatabaseAgent` starts with minimal context. It uses internal tools to search for relevant tables, inspect column types, and check data distributions *before* generating the final SQL.
- **Self-Correction**
  If the agent writes a query that fails, it reads the PostgreSQL error, reasons about the failure (e.g., "I used the wrong foreign key"), and rewrites the query autonomously within the loop.
- **Confidence-Driven Human-in-the-Loop (HITL)**
  SpeakQL dual-scores every query before execution. It evaluates **Structural Risk** (e.g., Cartesian products, missing `WHERE` clauses) and **Agent Confidence**. If a query is high-risk or confidence falls below `0.7`, the system automatically pauses execution and routes an `ApprovalRequest` ticket to a human Data Steward.
- **Explainability as a First-Class Citizen**
  The agent returns a rich `explainability` payload with every query, including the English rationale for table choices, the exact list of tables touched (extracted via AST), and a breakdown of which governance policies influenced the execution.

---

## 🛠️ Tech Stack

- **Framework:** FastAPI
- **Database ORM:** SQLModel (SQLAlchemy 2.0 under the hood) + Asyncpg
- **SQL Parser:** `sqlglot` (for safe AST manipulation and validation)
- **AI Integration:** `google-generativeai`, `openai`
- **Security:** `python-jose` (JWT), `bcrypt` / `argon2-cffi` (Password Hashing), `cryptography` (Fernet)

---

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
