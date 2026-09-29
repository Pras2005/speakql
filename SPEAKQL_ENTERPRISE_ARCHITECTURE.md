# SpeakQL Enterprise — Comprehensive Architecture & Build Guide

> From an AI SQL interface to a governed data access platform trusted by regulated enterprises and consultancy firms.

---

## Table of Contents

1. [Product Vision](#1-product-vision)
2. [Core Architecture](#2-core-architecture)
3. [Data Model](#3-data-model)
4. [Phase-by-Phase Roadmap](#4-phase-by-phase-roadmap)
5. [Policy Engine](#5-policy-engine)
6. [Audit Vault](#6-audit-vault)
7. [Masking & PII Governance](#7-masking--pii-governance)
8. [AI Agent Design](#8-ai-agent-design)
9. [Multi-Tenancy](#9-multi-tenancy)
10. [Security Hardening](#10-security-hardening)
11. [Admin Console](#11-admin-console)
12. [Workflow System](#12-workflow-system)
13. [Data Catalog & Semantic Layer](#13-data-catalog--semantic-layer)
14. [Connector Strategy](#14-connector-strategy)
15. [Observability](#15-observability)
16. [Hidden Differentiators](#16-hidden-differentiators)
17. [Frontend Architecture](#17-frontend-architecture)
18. [Deployment & Infrastructure](#18-deployment--infrastructure)
19. [Enterprise Sales Checklist](#19-enterprise-sales-checklist)
20. [Implementation Reality Check](#20-implementation-reality-check)
21. [Lessons From Code Example](#21-lessons-from-code-example)

---

## 1. Product Vision

### What SpeakQL is becoming

SpeakQL is not just a natural language SQL tool. The enterprise version is a **governed data access platform** — the layer between human intent and regulated data that enforces trust, control, and auditability at every step.

| Current product | Enterprise product |
|---|---|
| NL to SQL | Governed NL access to regulated data |
| Execute query | Policy-enforced execution |
| Inspect schema | Explainable query generation |
| View history | Auditable analyst workflows |
| Single user | Multi-tenant client workspaces |

### The core shift in mental model

Every query in SpeakQL Enterprise passes through a pipeline that is **check → generate → validate → mask → execute → audit**. No step is skippable. The policy engine is the control plane. The audit vault is the paper trail. The masking service is the last line of defence before data leaves the system.

### Who buys this

- **Consultancy firms** managing multiple client data estates
- **Regulated enterprises** (finance, healthcare, legal) with strict access control requirements
- **Cloud providers** (like ESDS) offering managed data analytics to tenants
- **Internal data teams** that need to enforce standards across analysts

---

## 2. Core Architecture

### Layer overview

```
┌─────────────────────────────────────────────────────────┐
│  CLIENT LAYER                                           │
│  Chat UI  │  Admin Console  │  MCP Clients  │  SSO     │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│  GATEWAY LAYER                                          │
│  JWT/SAML auth · Rate limiting · CORS · Request IDs    │
│  Org + Workspace resolution on every request           │
└───────┬───────────┬──────────────┬──────────────────────┘
        │           │              │
┌───────▼──┐  ┌─────▼──────┐  ┌───▼──────────┐
│  Policy  │  │  AI Agent  │  │   Masking    │
│  Engine  │  │  (ReAct)   │  │   Service    │
└───────┬──┘  └─────┬──────┘  └───┬──────────┘
        │           │              │
┌───────▼───────────▼──────────────▼──────────────────────┐
│  EXECUTION PIPELINE                                     │
│  policy check → AST parse → mask → execute → audit     │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│  DATA LAYER                                             │
│  App DB  │  Audit Vault  │  Secret Manager  │  Cache   │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│  CONNECTOR LAYER                                        │
│  PostgreSQL  │  Snowflake  │  BigQuery  │  SQL Server  │
└─────────────────────────────────────────────────────────┘
```

### Key architectural decisions

**Tenant isolation at the gateway.** Every inbound request is stamped with `org_id` and `workspace_id` before it touches any service. No service needs to re-derive tenancy — it trusts the gateway-injected context. This is enforced via a middleware dependency injected into every FastAPI route.

**RBAC uses JWT for context, not as the sole source of truth.** Access tokens carry identity and active workspace context such as `sub`, `org_id`, `workspace_id`, `membership_id`, `role`, and `token_version` so common request-time checks are fast. Mutable authorization state still lives server-side. High-risk actions such as policy changes, audit export, connector rotation, approval decisions, and MCP access must validate current membership and permission state from the database or cache.

**The execution pipeline is a chain, not a function.** Each step (policy check, AST parse, masking, execute, audit) is a discrete service call with its own success/failure logging. A failure at step 2 still writes an audit event.

**Secrets never leave the backend.** Database credentials are encrypted at rest using Fernet, stored in the app DB, and fetched per-request via the secret manager path. They are decrypted in memory only for the duration of the connection. No credential ever appears in logs, responses, or audit events.

**Infrastructure primitives must be centralised early.** Typed settings, a shared async session factory, and service-layer orchestration are not cleanup tasks for later. They are prerequisites for tenant-aware policy enforcement, safe logging defaults, and request lifecycle hooks such as audit and masking.

---

## 3. Data Model

### New entities required for enterprise

The single most important step is getting the data model right before building any features. Everything else layers onto these entities.

```sql
-- Tenant hierarchy
organization        (id, name, slug, sovereign_mode, billing_plan, created_at)
workspace           (id, org_id, name, slug, settings_json, created_at)
membership          (id, user_id, workspace_id, role, invited_by, joined_at)

-- Access control
role                ENUM: viewer | analyst | admin | compliance_admin
permission          (id, role, resource_type, resource_id, action)
invitation          (id, email, workspace_id, role, token, expires_at, accepted_at)

-- Governance
policy              (id, workspace_id, name, rules_json, priority, active)
sensitivity_rule    (id, workspace_id, table_pattern, column_pattern, label, mask_type)
approval_request    (id, query_id, requested_by, reviewed_by, status, reviewed_at)

-- Audit
audit_event         (id, org_id, workspace_id, user_id, event_type, hash,
                     details_json, previous_hash, created_at)
-- NOTE: audit_event is append-only. No UPDATE or DELETE permissions on this table.
-- It uses SHA-256 chain-hashing for tamper-evidence.

-- Workflow
saved_query         (id, workspace_id, created_by, name, prompt, sql, tags, is_template)
query_run           (id, saved_query_id, run_by, result_snapshot_ref, ran_at, row_count)
query_comment       (id, query_id, user_id, body, created_at)
report              (id, workspace_id, name, schedule_cron, last_ran_at, delivery_config)

-- Catalog
catalog_entry       (id, workspace_id, db_id, table_name, description, owner, freshness)
column_annotation   (id, catalog_entry_id, column_name, description, sensitivity_label)
metric_definition   (id, workspace_id, name, sql_expression, certified_by, certified_at)
business_term       (id, workspace_id, term, definition, synonyms_json, maps_to_table)
```

### Migration strategy

When adding multi-tenancy to an existing database:

1. Create a default `organization` and `workspace` row.
2. Add `org_id` and `workspace_id` nullable columns to all existing tables.
3. Backfill all rows with the default org and workspace IDs.
4. Add NOT NULL constraints and foreign keys.
5. Add row-level security policies in PostgreSQL to enforce tenant isolation at the DB layer as a second line of defence.

```sql
-- Example: RLS policy for workspaces
ALTER TABLE user_database ENABLE ROW LEVEL SECURITY;

CREATE POLICY workspace_isolation ON user_database
  USING (workspace_id = current_setting('app.workspace_id')::uuid);
```

---

## 4. Phase-by-Phase Roadmap

### Phase 1 — Data model surgery (weeks 1–4)

**Goal:** Existing users are unaffected. New data model is in place. This is the foundation.

Deliverables:
- `organization`, `workspace`, `membership`, `role` tables
- Backfill all existing users into a default org/workspace
- `audit_event` table (append-only) wired to: login, failed login, SQL generate, execute
- Gateway middleware: resolve org + workspace on every request
- Request ID header (`X-Request-ID`) injected and threaded through all logs
- MCP authentication migration: move from database-only key semantics to workspace-aware credentials and audit context
- Backend refactor foundation: typed settings module, shared async session factory, and route/service separation sufficient to support tenant-aware orchestration

**Do not build UI in this phase.** This is not just a prioritisation preference. Any admin or workflow UI built before the tenant and policy schema stabilises will encode incorrect assumptions into routing, form payloads, cache keys, data fetching, and client state. Those assumptions will have to be unwound once `org_id`, `workspace_id`, RBAC, and policy semantics become first-class.

### Phase 2 — Policy engine + RBAC (weeks 5–10)

**Goal:** Enforce access control. This is the minimum viable governance story.

Deliverables:
- Role enforcement: viewer (no SQL edit), analyst (no PII), admin (full)
- Hybrid authorization model: JWT carries active workspace role context, while mutable permissions and sensitive-action authorization remain server-side
- `policy` table with rules: allowed SQL classes, table allowlists, row limits, timeout, blocked keywords
- Replace regex SQL safety with AST-based parser (`sqlglot`)
- Approval queue for destructive queries (DROP, TRUNCATE, ALTER, DELETE)
- Deny events written to audit vault with policy match reason
- Basic admin page: users list, role assignment

### Phase 3 — Trust surfaces (weeks 11–18)

**Goal:** Build the features you demo to enterprise buyers.

Deliverables:
- PII masking middleware (see [section 7](#7-masking--pii-governance))
- Sensitivity labels on columns (per `sensitivity_rule` table)
- Explainability layer: "why this SQL", tables used, risk score, confidence indicator
- Ambiguity warnings: prompt flagged as "needs review" if low confidence
- Admin console: policy management, audit log viewer, connector health, sensitivity rules
- Export controls: CSV/XLSX/PDF exports write to audit vault with export event

### Phase 4 — Workflow + catalog (weeks 19–28)

**Goal:** Make SpeakQL indispensable for repeat work.

Deliverables:
- Saved queries, templates, replay from history
- SQL diff between runs, result snapshot comparison
- Query comments and team sharing
- Approval/review workflow for analyst-to-admin
- Data catalog: table/column descriptions, business glossary
- Certified metrics with approved SQL expressions
- Scheduled reports with email/Slack delivery

### Phase 5 — Platformisation (weeks 29+)

**Goal:** Sell to enterprises and cloud providers.

Deliverables:
- SSO/SAML (Okta, Azure AD, Google Workspace)
- SCIM provisioning
- Snowflake + BigQuery connector layer
- Sovereign mode: per-org toggle forcing all AI to local LLMs (Ollama/vLLM)
- Usage-based billing and quota enforcement
- White-label portal with custom domain support
- KMS-backed encryption, secret manager integration (HashiCorp Vault / AWS Secrets Manager)
- Multi-region deployment support
- Client access expiration and engagement-level audit exports

---

## 5. Policy Engine

The policy engine is the control plane of SpeakQL Enterprise. It intercepts every query before execution and every result before delivery.

### RBAC operating model

RBAC in SpeakQL Enterprise is hybrid by design:

1. The access token carries the active workspace context for fast request-time gating.
2. The database or cache remains the source of truth for mutable permissions.
3. Policy evaluation always runs with explicit `org_id`, `workspace_id`, `membership_id`, and `role` context.
4. High-risk actions must re-check current authorization state server-side even if the JWT contains a role claim.

Recommended access-token claims:

```json
{
  "sub": "user_id",
  "org_id": "org_id",
  "workspace_id": "workspace_id",
  "membership_id": "membership_id",
  "role": "analyst",
  "token_version": 3
}
```

Design constraints:
- JWT role claims are appropriate for coarse request gating and tenant context.
- JWTs must not be the only authorization source because role changes, membership revocation, and policy changes need near-immediate effect.
- Tokens should be short-lived, and `token_version` or `membership_version` should support revocation when roles change.
- Each access token should represent one active workspace, not every workspace the user belongs to.

### Policy rule types

```python
class PolicyRule(BaseModel):
    # SQL class restrictions
    allowed_sql_classes: list[str]       # ["SELECT"] for read-only
    blocked_keywords: list[str]          # ["DROP", "TRUNCATE", "ALTER"]

    # Schema restrictions
    allowed_schemas: list[str] | None    # None = all schemas allowed
    allowed_tables: list[str] | None     # None = all tables allowed
    blocked_tables: list[str]            # Always blocked regardless of other rules

    # Execution limits
    max_row_count: int                   # Hard cap on returned rows
    max_execution_ms: int                # Query timeout
    max_result_bytes: int                # Result size cap

    # Approval requirements
    require_approval_for: list[str]      # ["DELETE", "UPDATE"] → approval queue
    auto_deny: list[str]                 # Denied outright, no appeal

    # Column-level
    restricted_columns: list[str]        # Columns that must be masked
    redacted_for_roles: list[str]        # Roles that see redacted data
```

### Policy evaluation order

```
1. Load all active policies for the workspace (ordered by priority ASC)
2. For each policy, evaluate rules against the parsed AST
3. First DENY match → reject immediately, write audit event
4. First APPROVE_WITH_MASK match → allow, apply masking
5. First REQUIRE_APPROVAL match → route to approval queue
6. If no policy matches → apply workspace default (typically DENY)
```

### AST-based SQL validation

Replace the current regex approach with `sqlglot`:

```python
import sqlglot
from sqlglot import exp

def validate_sql(sql: str, policy: PolicyRule) -> ValidationResult:
    try:
        parsed = sqlglot.parse_one(sql)
    except sqlglot.errors.ParseError as e:
        return ValidationResult(allowed=False, reason=f"Invalid SQL: {e}")

    # Check statement type
    stmt_type = type(parsed).__name__
    if stmt_type not in policy.allowed_sql_classes:
        return ValidationResult(
            allowed=False,
            reason=f"Statement type {stmt_type} not in allowed classes"
        )

    # Check for blocked keywords in AST (not raw string — bypass-proof)
    for node in parsed.walk():
        if isinstance(node, (exp.Drop, exp.AlterTable, exp.Truncate)):
            if "DROP" in policy.blocked_keywords:
                return ValidationResult(allowed=False, reason="DDL blocked by policy")

    # Check referenced tables against allowlist
    referenced = {t.name for t in parsed.find_all(exp.Table)}
    if policy.allowed_tables is not None:
        blocked = referenced - set(policy.allowed_tables)
        if blocked:
            return ValidationResult(
                allowed=False,
                reason=f"Tables not in allowlist: {blocked}"
            )

    return ValidationResult(allowed=True)
```

---

## 6. Audit Vault

### Design principles

The audit vault is **append-only and tamper-evident**. It uses chain hashing to make retrospective modification detectable, and is designed to satisfy SOC2 Type II and ISO 27001 audit requirements.

### Audit event types

```python
class AuditEventType(str, Enum):
    # Auth
    LOGIN_SUCCESS         = "auth.login.success"
    LOGIN_FAILED          = "auth.login.failed"
    LOGOUT                = "auth.logout"
    TOKEN_REFRESHED       = "auth.token.refreshed"

    # Prompt & generation
    PROMPT_SUBMITTED      = "query.prompt.submitted"
    SQL_GENERATED         = "query.sql.generated"
    SQL_EDITED_BY_USER    = "query.sql.edited"

    # Execution
    EXECUTION_REQUESTED   = "query.execution.requested"
    EXECUTION_ALLOWED     = "query.execution.allowed"
    EXECUTION_DENIED      = "query.execution.denied"
    EXECUTION_COMPLETED   = "query.execution.completed"
    EXECUTION_FAILED      = "query.execution.failed"

    # Policy
    POLICY_MATCHED        = "policy.matched"
    POLICY_DENIED         = "policy.denied"
    APPROVAL_REQUESTED    = "policy.approval.requested"
    APPROVAL_GRANTED      = "policy.approval.granted"
    APPROVAL_DENIED       = "policy.approval.denied"

    # Data access
    DATA_MASKING_APPLIED  = "data.masking.applied"
    EXPORT_PERFORMED      = "data.export.performed"
    RESULT_VIEWED         = "data.result.viewed"

    # Admin
    CONNECTOR_ADDED       = "admin.connector.added"
    CONNECTOR_DELETED     = "admin.connector.deleted"
    CREDENTIAL_ROTATED    = "admin.credential.rotated"
    MCP_KEY_ROTATED       = "admin.mcp_key.rotated"
    POLICY_CREATED        = "admin.policy.created"
    POLICY_UPDATED        = "admin.policy.updated"
    USER_INVITED          = "admin.user.invited"
    ROLE_CHANGED          = "admin.role.changed"
```

### Chain hashing implementation

```python
import hashlib, json
from datetime import datetime, timezone

async def write_audit_event(
    session: AsyncSession,
    org_id: UUID,
    workspace_id: UUID,
    user_id: UUID,
    event_type: AuditEventType,
    payload: dict,
) -> AuditEvent:
    # Get the hash of the last event for this workspace (chain integrity)
    last = await session.execute(
        select(AuditEvent)
        .where(AuditEvent.workspace_id == workspace_id)
        .order_by(AuditEvent.created_at.desc())
        .limit(1)
    )
    prev = last.scalar_one_or_none()
    prev_hash = prev.payload_hash if prev else "GENESIS"

    # Hash the payload
    payload_str = json.dumps(payload, sort_keys=True, default=str)
    payload_hash = hashlib.sha256(
        f"{prev_hash}:{payload_str}:{datetime.now(timezone.utc).isoformat()}".encode()
    ).hexdigest()

    event = AuditEvent(
        org_id=org_id,
        workspace_id=workspace_id,
        user_id=user_id,
        event_type=event_type,
        payload_json=payload,
        payload_hash=payload_hash,
        prev_hash=prev_hash,
        created_at=datetime.now(timezone.utc),
    )
    session.add(event)
    await session.commit()
    return event
```

### Audit log enforcement at DB level

```sql
-- Revoke destructive permissions from the application role
REVOKE UPDATE, DELETE, TRUNCATE ON audit_event FROM speakql_app;

-- Only the app role can INSERT
GRANT INSERT, SELECT ON audit_event TO speakql_app;

-- A separate compliance role can SELECT but not modify
CREATE ROLE speakql_compliance;
GRANT SELECT ON audit_event TO speakql_compliance;
```

---

## 7. Masking & PII Governance

### Sensitivity labels

```python
class SensitivityLabel(str, Enum):
    PUBLIC       = "public"
    INTERNAL     = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED   = "restricted"   # PII, financial data
    SECRET       = "secret"       # Credentials, keys
```

### Masking strategies

```python
class MaskType(str, Enum):
    REDACT       = "redact"        # Replace with [REDACTED]
    PARTIAL      = "partial"       # Show first/last N chars: ABCD****XYZ
    HASH         = "hash"          # SHA-256 deterministic pseudonymisation
    TOKENISE     = "tokenise"      # Format-preserving token (reversible for admins)
    NULLIFY      = "nullify"       # Replace with NULL
    GENERALISE   = "generalise"    # Replace DOB with age range, postcode with region
```

### PII detection pipeline

```python
import re

PII_PATTERNS = {
    "aadhaar":      r"\b[2-9]{1}[0-9]{3}\s[0-9]{4}\s[0-9]{4}\b",
    "pan":          r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b",
    "email":        r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b",
    "phone_in":     r"\b(?:\+91|0)?[6-9]\d{9}\b",
    "credit_card":  r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
    "passport_in":  r"\b[A-PR-WY][1-9]\d\s?\d{4}[1-9]\b",
    "ifsc":         r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
}

async def detect_and_mask(
    rows: list[dict],
    sensitivity_rules: list[SensitivityRule],
    user_role: str,
) -> tuple[list[dict], list[MaskingEvent]]:
    masking_events = []

    for row in rows:
        for col, value in row.items():
            if value is None or not isinstance(value, str):
                continue

            # Check column-level sensitivity rules first
            rule = find_rule(col, sensitivity_rules)
            if rule and should_mask(rule, user_role):
                row[col] = apply_mask(value, rule.mask_type)
                masking_events.append(MaskingEvent(column=col, reason="sensitivity_rule"))
                continue

            # Fallback: pattern-based PII detection
            for pii_type, pattern in PII_PATTERNS.items():
                if re.search(pattern, str(value)):
                    row[col] = apply_mask(value, MaskType.PARTIAL)
                    masking_events.append(MaskingEvent(column=col, reason=f"pii_detected:{pii_type}"))
                    break

    return rows, masking_events
```

---

## 8. AI Agent Design

### Separation of concerns

The current agent conflates schema retrieval, prompt construction, and SQL generation. For enterprise scale these must be separate:

```
schema_retrieval   → catalog_service.get_schema_map(workspace_id, db_id, prompt)
prompt_construction → prompt_builder.build(schema_map, user_prompt, policy_context)
sql_generation     → llm_provider.generate(prompt)
validation         → dry_run_validator.check(sql, db_connection)
explanation        → explainer.explain(sql, schema_map)
risk_scoring       → risk_scorer.score(sql, policy)
```

### Risk scoring before execution

```python
class SQLRiskScore(BaseModel):
    score: int                  # 0–100
    level: str                  # low | medium | high | critical
    reasons: list[str]
    requires_approval: bool
    warnings: list[str]

def score_sql(sql: str, parsed_ast, policy: PolicyRule) -> SQLRiskScore:
    score = 0
    reasons = []

    # Penalise write operations
    if isinstance(parsed_ast, (exp.Insert, exp.Update, exp.Delete)):
        score += 60
        reasons.append("Write operation detected")

    # Penalise full table scans (no WHERE clause)
    if isinstance(parsed_ast, exp.Select) and parsed_ast.find(exp.Where) is None:
        score += 20
        reasons.append("No WHERE clause — full table scan")

    # Penalise SELECT *
    for col in parsed_ast.find_all(exp.Star):
        score += 10
        reasons.append("SELECT * used — may expose sensitive columns")
        break

    # Penalise JOINs across many tables (complexity)
    join_count = len(list(parsed_ast.find_all(exp.Join)))
    if join_count > 4:
        score += 10 * (join_count - 4)
        reasons.append(f"Complex query: {join_count} joins")

    level = "low" if score < 25 else "medium" if score < 50 else "high" if score < 75 else "critical"
    return SQLRiskScore(
        score=score,
        level=level,
        reasons=reasons,
        requires_approval=score >= 60,
        warnings=reasons,
    )
```

### Explainability output

Every generated SQL must be accompanied by a structured explanation:

```python
class SQLExplanation(BaseModel):
    plain_english: str              # "This query counts active users by region"
    tables_used: list[TableUsage]   # [{name, reason, columns_accessed}]
    join_rationale: list[str]       # ["users joined to orders on user_id"]
    assumptions: list[str]          # ["'active' means status = 'active'"]
    risk_score: SQLRiskScore
    confidence: float               # 0.0–1.0
    needs_review: bool              # True if confidence < 0.7 or risk >= high
    clarification_questions: list[str]  # For ambiguous prompts
```

### Prompt injection defence

Schema metadata enters the LLM context directly. A malicious database schema could contain table names or column comments designed to manipulate the model:

```python
INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|prior)\s+instructions",
    r"you\s+are\s+now\s+a",
    r"forget\s+everything",
    r"system\s*:",
    r"<\s*system\s*>",
]

def sanitise_schema_metadata(schema: dict) -> dict:
    for table in schema.get("tables", []):
        table["name"] = sanitise_string(table["name"])
        table["description"] = sanitise_string(table.get("description", ""))
        for col in table.get("columns", []):
            col["name"] = sanitise_string(col["name"])
            col["description"] = sanitise_string(col.get("description", ""))
    return schema

def sanitise_string(s: str) -> str:
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, s, re.IGNORECASE):
            return "[SANITISED]"
    return s
```

### Sovereign mode

Per-organisation setting that forces all inference to local models:

```python
async def get_llm_provider(org: Organization, workspace: Workspace) -> LLMProvider:
    if org.sovereign_mode:
        # All inference stays local — no external API calls
        return OllamaProvider(
            model=workspace.settings.get("local_model", "qwen2.5-coder:7b"),
            base_url=settings.OLLAMA_BASE_URL,
        )

    # Default: use configured cloud provider
    return GeminiProvider(model="gemini-2.0-flash")
```

---

## 9. Multi-Tenancy

### The three-tier model

```
Organization
  └── Workspace A (e.g. "Client: HDFC Project")
  │     ├── Members: alice (admin), bob (analyst), carol (viewer)
  │     ├── Databases: hdfc_prod_readonly, hdfc_staging
  │     └── Policies: finance_policy_pack
  └── Workspace B (e.g. "Internal: Operations")
        ├── Members: dave (admin), eve (analyst)
        ├── Databases: internal_ops_db
        └── Policies: default_policy
```

### Tenant isolation in FastAPI

```python
# middleware/tenant.py
from fastapi import Request, HTTPException
from jose import jwt

async def tenant_middleware(request: Request, call_next):
    # Extract and validate JWT
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except Exception:
        raise HTTPException(status_code=401)

    # Stamp request state — available to all downstream handlers
    request.state.user_id      = payload["sub"]
    request.state.org_id       = payload["org_id"]
    request.state.workspace_id = payload.get("workspace_id")
    request.state.membership_id = payload.get("membership_id")
    request.state.role         = payload["role"]
    request.state.token_version = payload.get("token_version")

    # Inject into PostgreSQL session for RLS
    async with get_session() as session:
        await session.execute(
            text("SELECT set_config('app.workspace_id', :wid, true)"),
            {"wid": str(request.state.workspace_id)}
        )

    return await call_next(request)
```

### Workspace-scoped token strategy

- Access tokens carry one active `workspace_id`, not all workspace memberships.
- Switching workspaces should mint a new access token so routing, audit, policy evaluation, and connector access all share the same active tenant context.
- Role claims in the token are for speed, but sensitive operations still validate current membership and permission state from the database or cache.
- MCP credentials must follow the same tenant model. Database-only API keys are not sufficient in the enterprise architecture because policy and audit need workspace context.

### Per-workspace connection pool isolation

```python
# Each workspace gets its own pool to prevent cross-tenant connection sharing
_pool_cache: dict[str, AsyncEngine] = {}

async def get_engine(workspace_id: UUID, db_config: UserDatabase) -> AsyncEngine:
    cache_key = f"{workspace_id}:{db_config.id}"
    if cache_key not in _pool_cache:
        _pool_cache[cache_key] = create_async_engine(
            build_connection_string(db_config),
            pool_size=5,
            max_overflow=2,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
    return _pool_cache[cache_key]
```

---

## 10. Security Hardening

### Secrets management

Never store raw database credentials. The recommended path:

```
User submits DB credentials
    → Encrypt with Fernet (current, acceptable for MVP)
    → Store in app DB

Production upgrade path:
    → Store encryption key in HashiCorp Vault or AWS KMS
    → Fetch key per-request via Vault token auth
    → Credential rotation triggers re-encryption without downtime
```

### API hardening checklist

```python
# main.py additions

# 1. Strict CORS — environment-specific
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,   # ["https://app.speakql.io"] in prod
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# 2. Rate limiting (use slowapi)
from slowapi import Limiter
limiter = Limiter(key_func=lambda req: req.state.user_id or req.client.host)

@app.post("/agent/generate")
@limiter.limit("30/minute")
async def generate_sql(request: Request, ...): ...

# 3. Request size limits
app.add_middleware(
    ContentSizeMiddleware,
    max_content_size=512 * 1024   # 512 KB max request body
)

# 4. Request IDs for log correlation
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# 5. API versioning
app.include_router(v1_router, prefix="/api/v1")
```

### Runtime safety defaults

- SQL logging must be off by default. Debug flags like SQLAlchemy `echo=True` should be enabled only behind explicit development settings because raw SQL and bound parameters can otherwise leak outside the governed audit path.
- The async session factory should be created once at process startup and reused. Rebuilding it per dependency call is unnecessary and makes connection management harder to reason about under concurrency.
- Business logic should move out of route handlers into service-layer orchestration so audit writes, policy checks, masking, and tenant resolution attach in one place instead of scattering across endpoints.

### Execution hardening

```python
async def execute_query_safely(
    sql: str,
    engine: AsyncEngine,
    policy: PolicyRule,
    request_id: str,
) -> QueryResult:
    # 1. AST validation (not regex)
    validation = validate_sql(sql, policy)
    if not validation.allowed:
        raise PolicyViolationError(validation.reason)

    # 2. Server-side pagination — never return unbounded results
    paginated_sql = f"SELECT * FROM ({sql}) AS __q LIMIT {policy.max_row_count} OFFSET 0"

    # 3. Statement timeout at DB level
    async with engine.connect() as conn:
        await conn.execute(
            text(f"SET statement_timeout = '{policy.max_execution_ms}ms'")
        )
        result = await conn.execute(text(paginated_sql))
        rows = result.mappings().all()

    return QueryResult(rows=rows, truncated=len(rows) == policy.max_row_count)
```

---

## 11. Admin Console

### Required pages

| Page | Purpose | Roles |
|---|---|---|
| Users & Roles | Invite, assign roles, deactivate | admin |
| Policy management | Create, edit, prioritise policies | admin |
| Audit log viewer | Filter by user/event/date, export | admin, compliance_admin |
| Connector management | Add/test/rotate/delete DB connections | admin |
| Sensitivity rules | Column-level labelling and masking | admin |
| Approval queue | Review and approve pending queries | admin |
| Model/provider settings | Configure AI provider, sovereign mode | admin |
| Usage analytics | Token consumption, query volume, costs | admin |
| Failed query review | Inspect denied queries, adjust policies | admin |
| Prompt/SQL oversight | Review all generated SQL (compliance) | compliance_admin |

### Audit log viewer filters

```
Filter by:  user | workspace | database | event_type | policy_result | date range
Export as:  CSV | PDF (with digital signature for compliance)
Columns:    timestamp | user | event | resource | policy | result | request_id
```

---

## 12. Workflow System

### Query lifecycle

```
1. User submits prompt
2. AI generates SQL + explanation
3. Risk score computed
4. If score >= high → "Needs review" state, admin notified
5. Analyst optionally edits SQL (edit event written to audit)
6. Execute → results returned (masked if applicable)
7. User can save query → becomes saved_query record
8. Saved query can be promoted to template (shared across workspace)
9. Template can be parameterised → runbook
```

### SQL diff on re-run

When a saved query is re-run, compute a structural diff between the original and new SQL:

```python
import sqlglot

def compute_sql_diff(old_sql: str, new_sql: str) -> SQLDiff:
    old_ast = sqlglot.parse_one(old_sql)
    new_ast = sqlglot.parse_one(new_sql)

    old_tables = {t.name for t in old_ast.find_all(exp.Table)}
    new_tables = {t.name for t in new_ast.find_all(exp.Table)}

    return SQLDiff(
        tables_added=new_tables - old_tables,
        tables_removed=old_tables - new_tables,
        where_changed=str(old_ast.find(exp.Where)) != str(new_ast.find(exp.Where)),
        structural_change=old_ast.sql() != new_ast.sql(),
    )
```

---

## 13. Data Catalog & Semantic Layer

### Auto-generation on connection

When a database is connected, run a one-shot catalog generation pass:

```python
async def generate_catalog_draft(db_id: UUID, workspace_id: UUID):
    schema_map = await get_full_schema(db_id)
    prompt = build_catalog_prompt(schema_map)

    response = await llm.generate(prompt)
    draft = parse_catalog_response(response)

    # Insert as DRAFT status — admin must review before publishing
    for entry in draft.table_entries:
        await catalog_service.create_draft(workspace_id, db_id, entry)
```

### Business glossary example

```json
{
  "term": "AUM",
  "definition": "Assets Under Management — total market value of assets managed on behalf of clients",
  "synonyms": ["assets under management", "portfolio value", "managed assets"],
  "maps_to": {
    "table": "portfolio_holdings",
    "column": "market_value",
    "aggregation": "SUM"
  },
  "certified_by": "data_team",
  "certified_at": "2025-01-15T00:00:00Z"
}
```

When a user asks for "total AUM by client", the semantic layer resolves the term before sending to the LLM, injecting the correct table/column mapping directly into the prompt.

---

## 14. Connector Strategy

### Phase rollout

| Phase | Connectors |
|---|---|
| 1 (current) | PostgreSQL (asyncpg) |
| 2 | Snowflake, BigQuery |
| 3 | SQL Server (aioodbc), Databricks SQL |
| 4 | Oracle, Redshift, MySQL |

### Connector health monitoring

```python
class ConnectorHealth(BaseModel):
    db_id: UUID
    status: str                  # healthy | degraded | unreachable
    latency_ms: float
    last_checked: datetime
    pool_size: int
    pool_checked_out: int
    error: str | None

async def check_connector_health(db_id: UUID) -> ConnectorHealth:
    engine = await get_engine_for_db(db_id)
    start = time.monotonic()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        latency = (time.monotonic() - start) * 1000
        return ConnectorHealth(status="healthy", latency_ms=latency, ...)
    except Exception as e:
        return ConnectorHealth(status="unreachable", error=str(e), ...)
```

---

## 15. Observability

### Structured logging (every log line is JSON)

```python
import structlog

logger = structlog.get_logger()

# Every log carries context automatically
logger.info(
    "query.executed",
    org_id=str(org_id),
    workspace_id=str(workspace_id),
    user_id=str(user_id),
    db_id=str(db_id),
    request_id=request_id,
    duration_ms=duration,
    row_count=row_count,
    policy_result="allowed",
    risk_score=risk_score,
)
```

### Key metrics to instrument

```
# Query pipeline
speakql_query_total{status, workspace_id}
speakql_query_duration_ms{quantile, workspace_id}
speakql_policy_denials_total{reason, workspace_id}
speakql_masking_events_total{pii_type, workspace_id}

# AI agent
speakql_llm_latency_ms{provider, model, quantile}
speakql_llm_tokens_used{provider, type}          # type: prompt | completion
speakql_llm_errors_total{provider, error_type}
speakql_risk_score_histogram{level}              # low | medium | high | critical

# Connectors
speakql_connector_health{db_id, status}
speakql_connector_pool_utilisation{db_id}
speakql_connector_query_timeout_total{db_id}

# Auth
speakql_login_total{status}                      # success | failed
speakql_active_sessions_total{workspace_id}
```

---

## 16. Hidden Differentiators

These are not in the standard enterprise checklist but are high-value differentiators.

### Query fingerprinting

Hash every generated SQL (normalised, parameter-stripped) to build frequency analytics:

```python
import sqlglot, hashlib

def fingerprint_sql(sql: str) -> str:
    normalised = sqlglot.parse_one(sql).sql(dialect="postgres", pretty=False)
    return hashlib.sha256(normalised.encode()).hexdigest()[:16]
```

Use cases:
- Detect "certified queries" that have run 100+ times without issue → auto-approve
- Identify the top 20 most common query patterns per workspace → pre-warm cache
- Detect anomalous one-off queries that never repeat → flag for compliance review

### Result watermarking

Before any CSV/Excel export, embed an invisible watermark mapping to the `audit_event_id`:

```python
def watermark_dataframe(df: pd.DataFrame, audit_event_id: UUID) -> pd.DataFrame:
    # Embed a hidden column with the audit trace
    df["__speakql_trace"] = str(audit_event_id)

    # For numeric columns: add a sub-epsilon perturbation (undetectable, traceable)
    for col in df.select_dtypes(include=["float64"]).columns:
        seed = int(str(audit_event_id).replace("-", ""), 16) % 10000
        noise = (seed / 1e10)   # ~0.000000001 — imperceptible
        df[col] = df[col] + noise

    return df
```

If a client leaks exported data, the watermark traces it back to the exact query, user, timestamp, and workspace.

### Dead-reckoning catalog generation

Rather than waiting for admins to manually describe every table, generate draft descriptions automatically on connection. Admins review and approve — they do not write from scratch. For a schema with 200 tables this reduces onboarding time from weeks to hours.

### Approval queue analytics

Track approval patterns over time:
- Which query types are most frequently sent for approval?
- Which analysts have the highest approval rates?
- Are certain policies producing too many false positives?

This data feeds back into policy tuning recommendations shown in the admin console.

---

## 17. Frontend Architecture

### Required additions

```

Implementation constraint:
- Admin, workflow, and policy-management UI should begin only after Phase 1 backend tenancy and request-context primitives are in place. Otherwise the client will be built against a transient schema and authorization model and will require structural rework.
client/src/
  ├── providers/
  │   ├── AuthProvider.tsx         # Session state, JWT refresh, SSO redirect
  │   ├── WorkspaceProvider.tsx    # Active org + workspace context
  │   └── QueryStateProvider.tsx   # TanStack Query setup
  ├── hooks/
  │   ├── usePolicy.ts             # Fetch and cache workspace policy
  │   ├── useAudit.ts              # Stream audit events for admin view
  │   ├── useCatalog.ts            # Catalog entries + business terms
  │   └── useExecution.ts          # Query execution with policy awareness
  ├── views/
  │   ├── Chat/
  │   │   ├── ChatView.tsx         # Container (was monolithic Chat.tsx)
  │   │   ├── PromptInput.tsx      # NL input with voice toggle
  │   │   ├── SQLPanel.tsx         # Generated SQL + explanation + risk score
  │   │   ├── ResultPanel.tsx      # Table + chart auto-suggestion
  │   │   └── ApprovalBanner.tsx   # "This query needs admin approval"
  │   ├── Admin/
  │   │   ├── UsersPage.tsx
  │   │   ├── PoliciesPage.tsx
  │   │   ├── AuditPage.tsx
  │   │   ├── ConnectorsPage.tsx
  │   │   └── SensitivityPage.tsx
  │   ├── Catalog/
  │   │   ├── CatalogView.tsx
  │   │   └── GlossaryView.tsx
  │   └── Workflows/
  │       ├── SavedQueriesView.tsx
  │       ├── TemplatesView.tsx
  │       └── ApprovalQueueView.tsx
  └── admin/                       # Separate route module for admin surfaces
```

### State management

Replace ad-hoc fetch logic with TanStack Query for server state:

```typescript
// hooks/useExecution.ts
import { useMutation } from "@tanstack/react-query";

export function useExecuteQuery() {
  return useMutation({
    mutationFn: async (payload: ExecuteRequest) => {
      const res = await api.post("/api/v1/agent/execute", payload);
      return res.data as ExecuteResponse;
    },
    onSuccess: (data) => {
      // Invalidate history cache
      queryClient.invalidateQueries({ queryKey: ["query-history"] });
    },
  });
}
```

---

## 18. Deployment & Infrastructure

### docker-compose (development)

```yaml
services:
  app:
    build: ./backend
    environment:
      DATABASE_URL: postgresql+asyncpg://speakql:speakql@db:5432/speakql
      SECRET_KEY: ${SECRET_KEY}
      ALLOWED_ORIGINS: "http://localhost:5173"
      VAULT_ADDR: http://vault:8200
    depends_on: [db, vault, redis]

  client:
    build: ./client
    ports: ["5173:5173"]

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: speakql
      POSTGRES_USER: speakql
      POSTGRES_PASSWORD: speakql
    volumes: ["pgdata:/var/lib/postgresql/data"]

  vault:
    image: hashicorp/vault:1.16
    cap_add: [IPC_LOCK]
    environment:
      VAULT_DEV_ROOT_TOKEN_ID: root

  redis:
    image: redis:7-alpine    # For rate limiting + schema cache

volumes:
  pgdata:
```

### Production checklist

- [ ] PostgreSQL with RLS policies enabled for tenant isolation
- [ ] Read replica for query execution (primary for writes only)
- [ ] Redis for rate limiting, policy cache, and schema metadata cache
- [ ] HashiCorp Vault or AWS Secrets Manager for credential storage
- [ ] Structured logging to a log aggregator (Loki, Datadog, CloudWatch)
- [ ] Prometheus metrics endpoint + Grafana dashboards
- [ ] Sentry for error tracking with `request_id` correlation
- [ ] Alembic migrations with rollback scripts for every schema change
- [ ] Pre-production environment that mirrors production data model exactly
- [ ] Automated DB backup with point-in-time recovery
- [ ] TLS everywhere — no HTTP in production, not even internal
- [ ] API versioning: `/api/v1/` path prefix on all routes

---

## 19. Enterprise Sales Checklist

Before closing an enterprise contract, SpeakQL must satisfy:

### Security & compliance
- [ ] SOC 2 Type II evidence: audit vault with chain hashes + export capability
- [ ] Role-based access control with least-privilege enforcement
- [ ] Data encryption at rest and in transit
- [ ] PII masking with configurable policies
- [ ] Credential rotation capability without downtime
- [ ] No raw DB credentials in logs, responses, or error messages

### Governance
- [ ] Policy engine: allowlists, denylists, row limits, timeout enforcement
- [ ] Approval workflow for sensitive query classes
- [ ] Immutable audit log exportable to CSV/PDF
- [ ] Sensitivity labels on columns with automated PII detection

### Multi-tenancy
- [ ] Complete workspace isolation (data, connections, policies)
- [ ] Per-workspace role assignment
- [ ] User invitation flow with expiring tokens
- [ ] Admin console accessible to client's own admin user

### AI controls
- [ ] Explainability: "why this SQL" with tables, assumptions, risk score
- [ ] Sovereign mode available for data residency requirements
- [ ] Local model option (Ollama/vLLM) for highly sensitive deployments
- [ ] No training on client data (documented Anthropic/Google policy links)

### Operability
- [ ] SLA-backed uptime with status page
- [ ] Connector health monitoring with alerts
- [ ] Slow query telemetry visible to admin
- [ ] Support for client's existing SSO provider

---

## 20. Implementation Reality Check

This section reflects the current repository state. Its conclusions are already incorporated into the roadmap and architecture decisions above; it remains here as an explicit baseline snapshot so there is no loss of context.

### Current repo gap against this plan

- Phase 1 (Tenancy) and Phase 2 (Policy) are structurally complete.
- Phase 3 (Trust Surfaces) foundations are mostly completed:
    - Append-only audit vault with SHA-256 chain-hashing is implemented.
    - PII masking, explainability payloads, and risk scoring are in place.
    - Governance routes for policy, sensitivity, audit, and health are available.
    - Approval workflow is workspace-scoped.
    - Governed export (CSV/XLSX) is implemented and audited.
- MCP trust-model migration is partially complete: requests execute through the governed pipeline, but credential isolation is still database-key oriented.
- Frontend trust surfaces (Admin Console) are being redesigned under v2 specification to move from a chat-only view to a governed workbench.

### Why Phase 1 comes first

- COMPLETED: Multi-tenancy is first-class. Policies, approvals, audit, catalog, and connectors depend on `workspace_id`.
- COMPLETED: Audit correctness depends on request context. Request IDs, workspace IDs, and user roles are threaded through the system.
- COMPLETED: Policy enforcement is AST-based and role-aware.
- NEXT: Frontend trust surfaces (Phase 3 UI) are being implemented under the v2 Workbench design.

### MCP migration risk in the current codebase

- The existing MCP authentication model is currently database-key oriented. In an enterprise multi-tenant model, that is no longer sufficient because policy enforcement and audit events need workspace context, not just database identity.
- `mcp_server.py` should therefore be treated as a Phase 1 migration surface. MCP credentials need to become workspace-scoped or workspace-aware so requests can carry the same tenant context as the web application.
- If this change is delayed, the platform risks ending up with two incompatible trust models: workspace-aware governance in the web app and database-key access in MCP integrations.

### Recommended implementation sequence

1. Finish Phase 1 exactly as the platform foundation: tenant entities, workspace backfill, request context middleware, request IDs, and initial audit event writes.
2. Move to Phase 2 once the data model is stable: RBAC, `policy` entities, AST validation with `sqlglot`, and approval routing.
3. Only then build trust and admin surfaces from Phase 3 on top of a backend that already knows tenant context, policy decisions, and audit semantics.

### Practical justification

This ordering is the shortest path to a system that can credibly pass enterprise scrutiny. It reduces rework, keeps schema changes concentrated early, and ensures that later features such as masking, risk scoring, audit exports, and admin review are built on durable primitives instead of temporary single-tenant assumptions.

---

## 21. Lessons From Code Example

This section captures practical lessons from reviewing `code_example/graphbackend` against the current SpeakQL backend. These lessons are already reflected in the architecture decisions and roadmap above; they are retained here to preserve the concrete reasoning behind those choices.

### Good patterns worth adopting

- Centralised database session setup is better in the example than in the current SpeakQL backend. The example creates the engine and session factory once in [code_example/graphbackend/db/session.py](/home/admin/Desktop/speakql/code_example/graphbackend/db/session.py), while the current SpeakQL backend rebuilds the sessionmaker inside [backend/database.py:21](/home/admin/Desktop/speakql/backend/database.py:21) on every dependency call.
- Configuration concerns are separated more cleanly in the example. [code_example/graphbackend/core/config.py](/home/admin/Desktop/speakql/code_example/graphbackend/core/config.py) gives a clearer home for environment-driven settings than the current pattern of loading env values ad hoc in multiple places like [backend/database.py](/home/admin/Desktop/speakql/backend/database.py) and [backend/utils/agent.py](/home/admin/Desktop/speakql/backend/utils/agent.py).
- Router composition is cleaner when domain routes live outside `main.py`. The example keeps `main.py` mostly focused on app bootstrap and route registration, while SpeakQL still carries many business endpoints directly in [backend/main.py](/home/admin/Desktop/speakql/backend/main.py).
- Query shaping in the example is often more efficient. In [code_example/graphbackend/crud/post_crud.py](/home/admin/Desktop/speakql/code_example/graphbackend/crud/post_crud.py), counts and related values are aggregated in SQL instead of fetched row by row. That is the right general pattern for SpeakQL too: do heavy data shaping in the database when possible, especially for audit views, policy dashboards, and query history summaries.

### Problems in the current SpeakQL backend highlighted by that comparison

- `main.py` is carrying too much application logic. Auth, database management, key rotation, and history routes are all concentrated in [backend/main.py](/home/admin/Desktop/speakql/backend/main.py) instead of being split into domain routers and services.
- Infrastructure concerns are not centralised enough. DB config, env loading, and model-provider setup are spread across [backend/database.py](/home/admin/Desktop/speakql/backend/database.py) and [backend/utils/agent.py](/home/admin/Desktop/speakql/backend/utils/agent.py), which makes later enterprise features like tenant-aware config and sovereign mode harder to implement cleanly.
- Current CRUD functions mix persistence and business workflow. For example, [backend/crud/db_crud.py](/home/admin/Desktop/speakql/backend/crud/db_crud.py) handles validation, encryption, persistence, and token generation together. For enterprise work, those concerns should be separated into service-layer orchestration plus thinner repository-style DB access.
- Debug and startup defaults are too loose for a governed platform. [backend/database.py:13](/home/admin/Desktop/speakql/backend/database.py:13) uses `echo=True`, which is not a minor hygiene issue. SQLAlchemy echo logging can emit raw executed SQL and parameters to stdout, creating a side channel outside the audit vault if logs are collected centrally. It should be disabled by default and only enabled behind an explicit debug setting.
- Session factory lifecycle is also weaker than it should be. [backend/database.py:21](/home/admin/Desktop/speakql/backend/database.py:21) rebuilds the sessionmaker per dependency call, whereas the example centralises the session factory in [code_example/graphbackend/db/session.py](/home/admin/Desktop/speakql/code_example/graphbackend/db/session.py). In an async FastAPI service under load, this pattern is harder to reason about and can create avoidable connection-management issues once concurrency increases.

### What not to copy from the example

- The example is not consistently DRY. [code_example/graphbackend/crud/post_crud.py](/home/admin/Desktop/speakql/code_example/graphbackend/crud/post_crud.py) repeats large chunks of similar aggregation logic across multiple functions. SpeakQL should learn the SQL-shaping principle, not the duplication.
- The example still uses create-all startup initialization in [code_example/graphbackend/db/session.py:20](/home/admin/Desktop/speakql/code_example/graphbackend/db/session.py:20). For SpeakQL Enterprise, Alembic-first schema management remains the correct path.
- Some example config access is still split between module globals and settings objects in [code_example/graphbackend/core/config.py](/home/admin/Desktop/speakql/code_example/graphbackend/core/config.py). SpeakQL should prefer a single typed settings layer rather than copying that mixed approach.

### Concrete architectural actions for SpeakQL

1. Introduce a proper `core/config.py` for typed settings and move env access out of leaf modules.
2. Refactor `backend/main.py` into route modules such as `auth_routes`, `database_routes`, `audit_routes`, and `admin_routes`.
3. Replace per-call sessionmaker creation with a single shared async session factory.
4. Add a service layer between routers and CRUD modules so policy, audit, masking, and tenant context orchestration do not accumulate inside route handlers.
5. Favor DB-side aggregation for enterprise reporting views, but keep shared query-building helpers to avoid the duplication pattern present in the example backend.

### Why this matters

SpeakQL is still a web app, but enterprise requirements amplify ordinary web-app design mistakes. If config, routing, session management, and business orchestration stay loosely structured now, policy enforcement, audit guarantees, and multi-tenant isolation will become expensive to retrofit later.

---

*Last updated: 2026. This document is the living architecture reference for SpeakQL Enterprise. Update it alongside major schema or service changes.*
