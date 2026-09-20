# SpeakQL

SpeakQL is a full-stack platform that enables natural language querying of databases. It bridges the gap between conversational AI and SQL databases by providing a dedicated Model Context Protocol (MCP) server alongside a modern web interface. 

## Core Features & Architecture

- **Natural Language to SQL**: Core engine translates user prompts into executable SQL queries via `DatabaseAgent`.
- **MCP Server Integration**: Features an integrated Model Context Protocol server (`backend/mcp_server.py`) exposing tools (`ask_database`, `get_schema`) for external AI assistants to interact with registered databases securely.
- **Connection & Credential Management**: Users can register and manage multiple database connections securely. Includes MCP API key rotation for granting controlled access to the databases.
- **Query History Auditing**: Maintains detailed logs of all natural language prompts, generated SQL, execution status, and timestamps.
- **Full-Stack Stack**: 
  - **Backend**: FastAPI with asynchronous SQLAlchemy (Alembic for migrations). Exposes REST endpoints for the client and SSE/HTTP endpoints for the MCP Server.
  - **Client**: React frontend configured with Vite and TypeScript for managing connections and history.

## Prerequisites

- **Python 3.10+**
- **Node.js 18+** & **pnpm**
- **PostgreSQL** or equivalent RDBMS for the application backend

## Installation & Setup

Both the backend and client can be orchestrated using Docker Compose, or run locally.

### Using Docker
```bash
docker-compose up --build
```

### Local Development Setup

**Backend**:
1. Navigate to the `backend/` directory.
2. Create a virtual environment and activate it.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run Alembic migrations to set up the DB:
   ```bash
   alembic upgrade head
   ```
5. Start the backend application:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

**Client**:
1. Navigate to the `client/` directory.
2. Install dependencies:
   ```bash
   pnpm install
   ```
3. Start the Vite development server:
   ```bash
   pnpm run dev
   ```

## Usage

- **Client Application**: Access the UI at `http://localhost:5173` to sign up, add your target databases, and view query history.
- **MCP Server**: The MCP server is mounted at `/mcp`. Provide your generated `X-SpeakQL-API-Key` to your compatible AI client (like Claude Desktop) to allow the AI to directly query your databases using natural language.

## Project Structure

```text
.
├── backend/                  # FastAPI Application
│   ├── main.py               # Core REST API (Auth, User Databases, History)
│   ├── mcp_server.py         # Model Context Protocol endpoints and tools
│   ├── auth/                 # JWT Authentication logic
│   ├── crud/                 # Database operation wrappers
│   ├── utils/agent.py        # Logic for NL to SQL generation and execution
│   └── alembic/              # Database migration definitions
├── client/                   # Vite + React Frontend
│   ├── src/                  # TS Components and Pages
│   └── package.json          # Node dependencies
└── docker-compose.yml        # Orchestration configuration
```
