# SpeakQL Engineering Rules

This document defines how code must be written and organised as SpeakQL moves from a single-product web app toward an enterprise platform.

These rules are primarily about:
- separation of concerns,
- file and module boundaries,
- naming,
- encapsulation,
- dependency direction,
- and avoiding structural debt.

Performance optimization is important, but it is not the primary concern in this document.

## 1. Core Principles

- Every file must have a clear responsibility.
- Every layer must have a clear responsibility.
- Business logic must be encapsulated, not scattered.
- Infrastructure concerns must have one canonical implementation.
- New code must be added to the correct layer, not to the nearest existing file.

## 2. Layer Responsibilities

### Routers

- Routers handle HTTP concerns only.
- Routers parse requests, call services, and shape HTTP responses.
- Routers may translate domain errors into HTTP errors.
- Routers must not contain multi-step business workflows.
- Routers must not directly write audit rows.

### Services

- Services contain business orchestration.
- Services coordinate repositories, audit writing, policy checks, and external providers.
- Services are the correct place for workflows that involve more than one operation.
- Services must not depend on HTTP request or response objects unless there is a clear infrastructure reason.

### Repositories

- Repositories own persistence logic.
- Repositories read and write models.
- Repositories must not implement HTTP behavior.
- Repositories must not own authorization decisions.
- Repositories must not own audit side effects.

### Models

- Models define database entities only.
- Models should not contain service orchestration logic.

### Schemas

- Schemas define contracts for requests, responses, and typed service payloads.
- Schemas should be explicit and named by domain behavior.

### Core

- `core/` contains shared infrastructure primitives.
- Configuration, logging, request context primitives, and other cross-cutting infrastructure belong here.

### Middleware

- `middleware/` contains request lifecycle logic.
- Middleware handles request IDs, auth context extraction, tenant context stamping, and similar concerns.

## 3. File and Folder Structure

Preferred backend layout:

```text
backend/
  core/
    config.py
    logging.py
    request_context.py
  middleware/
    request_context.py
  models/
  schemas/
  repositories/
  services/
    auth_service.py
    database_service.py
    query_service.py
    audit_service.py
    membership_service.py
    policy_service.py
  routers/
    auth_routes.py
    database_routes.py
    query_routes.py
    admin_routes.py
    audit_routes.py
  main.py
```

Rules:
- `main.py` assembles the application. It should not become a business-logic file.
- New domains should get their own router and service instead of extending a monolithic file.
- `utils.py` should not be the default destination for new code.
- If a utility module collects unrelated logic, it must be split by concern.

## 4. Naming Rules

### Files

- Use `snake_case` for filenames.
- Name files by responsibility, not by vagueness.
- Good examples:
  - `audit_service.py`
  - `database_routes.py`
  - `membership_repository.py`
  - `request_context.py`
- Bad examples:
  - `helpers.py`
  - `common.py`
  - `misc.py`
  - `new_utils.py`
  - `final_final.py`

### Classes

- Use `PascalCase`.
- Class names should be nouns or noun phrases.
- Examples:
  - `AuditService`
  - `RequestContext`
  - `WorkspaceMembership`

### Functions and Variables

- Use `snake_case`.
- Function names should describe actions.
- Examples:
  - `create_workspace`
  - `issue_access_token`
  - `record_audit_event`
  - `validate_workspace_access`

### Constants and Settings

- Raw environment variable names remain uppercase in `.env`.
- Python settings fields should use `snake_case`.
- Do not spread raw environment names across application code.

## 5. Encapsulation Rules

- No feature module should call `os.getenv()` directly.
- No feature module should call `load_dotenv()` directly.
- No feature module should create its own logger configuration.
- No feature module should create its own DB engine or session factory.
- No route handler should directly execute a multi-step workflow.
- No route handler should directly construct audit records.
- Security-sensitive actions must go through one canonical implementation path.

Canonical-path examples:
- password hashing
- token issuance
- credential encryption/decryption
- request-context extraction
- audit event writing
- policy evaluation

## 6. Class and Function Rules

- Prefer functions unless state or dependency ownership clearly requires a class.
- Use classes when encapsulating providers, services with dependencies, or typed domain behavior.
- Do not create classes just to hold static methods.
- Keep functions focused on one responsibility.
- If a function performs unrelated concerns, split it.
- Public interfaces should be small and explicit.
- Deep call chains with unclear ownership should be refactored.

## 7. Dependency Direction Rules

Dependencies must flow inward in a predictable direction:

- routers can depend on services
- services can depend on repositories and core modules
- repositories can depend on models and DB primitives
- middleware can depend on core modules and auth utilities
- core modules must not depend on feature modules
- repositories must not depend on routers
- services should not depend on routers

If a dependency crosses layers in the wrong direction, that design should be treated as suspect.

## 8. Error Handling Rules

- Repositories should not raise HTTP exceptions.
- Services should express business and domain failures clearly.
- Routers are responsible for HTTP status translation.
- Do not mix HTTP semantics deep into business logic.
- Error messages must not leak secrets, credentials, or sensitive internals.

## 9. Configuration and Secrets Rules

- There must be one central configuration entrypoint.
- All application code should import config from that central module.
- Secrets loaded from `.env` in development must still come through the central config layer.
- The application should behave as if it already has a secret service boundary, even if `.env` is still the current backend for secrets.
- Replacing `.env` with Vault, KMS, or a managed secret store later should not require widespread feature-code changes.

## 10. Logging and Audit Rules

- Never use `print()` in application code.
- Use one encapsulated logging setup.
- Every log line must support request correlation through `request_id`.
- Operational logging and audit logging are separate concerns.
- Query history is not the compliance audit trail.
- Sensitive values such as passwords, raw tokens, decrypted secrets, and credentials must never appear in logs.
- SQL logging must be disabled by default outside explicit debug mode.
- Audit event writing must go through one encapsulated service path.

## 11. Auth and RBAC Rules

- JWTs carry active workspace context, not the full authorization model.
- Use one active workspace per access token.
- JWT role claims are for coarse request gating only.
- Sensitive actions must verify current authorization state server-side.
- Role and permission logic must live in reusable guards or services, not be scattered across route handlers.
- MCP authentication must be workspace-aware and auditable.

## 12. Frontend Separation Rules

- Keep page containers separate from reusable UI components.
- Keep data fetching in hooks or providers, not buried across UI trees.
- Admin, workflow, and catalog surfaces should live in their own route areas.
- Frontend state shape must not depend on backend shortcuts known to be temporary.
- Auth and active workspace context should each have one clear source of truth.

## 13. What To Avoid

- No business logic added directly to `main.py`.
- No direct env access spread across many files.
- No new generic dumping-ground utility files.
- No route handlers manually constructing audit rows.
- No feature module owning its own logging or DB setup.
- No database-only trust model for MCP in enterprise mode.
- No premature admin UI before tenancy and request-context foundations are in place.

## 14. Deferred Concerns

These are important, but they should not distort early structural decisions:
- micro-optimizations
- aggressive caching
- generic repository frameworks
- over-abstracted plugin systems
- speculative abstraction for future connectors that do not yet exist

Optimization can be revisited later. Encapsulation and separation of concerns must be established now.

## 15. Enforcement Mindset

These rules exist to reduce future rewrites and keep governance features implementable.

If a design choice makes tenant context, audit consistency, policy enforcement, or service boundaries harder to reason about, that choice should be rejected even if it appears faster in the short term.
