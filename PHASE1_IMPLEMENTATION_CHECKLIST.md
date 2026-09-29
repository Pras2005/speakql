# SpeakQL Enterprise Phase 1 Checklist

This checklist is the execution tracker for Phase 1 foundations. It is intentionally implementation-focused and should stay aligned with [SPEAKQL_ENTERPRISE_ARCHITECTURE.md](/home/admin/Desktop/speakql/SPEAKQL_ENTERPRISE_ARCHITECTURE.md).

## Foundation

- [x] Create `backend/core/config.py` with typed settings.
- [x] Remove ad hoc environment loading from leaf modules.
- [x] Create one shared async engine and one shared async session factory.
- [x] Disable SQLAlchemy SQL echo by default and gate it behind debug config.
- [x] Introduce route/service/repository separation.
- [x] Move business logic out of `backend/main.py`.

## Tenant Data Model

- [x] Add `organization` table.
- [x] Add `workspace` table.
- [x] Add `membership` table.
- [x] Add membership role field: `viewer | analyst | admin | compliance_admin`.
- [x] Add `org_id` and `workspace_id` to workspace-owned resources.
- [x] Add foreign keys and indexes for tenant columns.
- [x] Identify which existing tables are truly workspace-owned versus derivable.
- [x] Enforce `NOT NULL` constraints on `org_id` and `workspace_id` in schema.

## Backfill and Migration

- [ ] Create default organization. (Logic verified in `TenantService` + Smoke Test)
- [ ] Create default workspace. (Logic verified in `TenantService` + Smoke Test)
- [ ] Backfill existing users into default workspace membership.
- [ ] Backfill existing resources with default `org_id` and `workspace_id`.
- [ ] Make tenant columns non-null after backfill.
- [ ] Add Alembic migrations for each step. (Deferred: Backend never ran yet)
- [ ] Keep rollout backward-compatible until backfill is complete.

## JWT and Auth Context

- [x] Define JWT payload with `sub`, `org_id`, `workspace_id`, `membership_id`, `role`, `token_version`.
- [x] Issue one active-workspace token per session. (Implemented in `AuthService.login`)
- [x] Add workspace-switch token reissue flow. (Implemented in `tenant_routes.py`)
- [x] Use JWT for coarse request gating only.
- [x] Add server-side membership verification for sensitive actions. (Implemented via `RoleChecker` guards)
- [x] Add token versioning for revocation on role or membership change. (Implemented in `User` model and JWT payload)

## Request Context Middleware

- [x] Generate or propagate `X-Request-ID`.
- [x] Decode JWT once in middleware. (Implemented in `JWTBearer`)
- [x] Attach `user_id`, `org_id`, `workspace_id`, `membership_id`, `role`, and `request_id` to request state. (Implemented in `RequestContext`)
- [x] Reject protected requests with invalid tenant context. (Enforced via `JWTBearer(require_workspace=True)`)
- [x] Prepare DB session context injection for future RLS.

## Logging and Audit Encapsulation

- [x] Add encapsulated application logging module. (`backend/core/logging.py`)
- [x] Add request-context-aware logging fields.
- [x] Add dedicated `audit_event` model.
- [x] Add encapsulated `audit_service`.
- [x] Keep audit separate from product query history.
- [x] Ensure every audit event carries `request_id`, `org_id`, `workspace_id`, `user_id`, and `event_type`.

## Minimum Audit Events

- [x] Log login success.
- [x] Log login failure.
- [x] Log database added.
- [x] Log SQL generated.
- [x] Log execution requested.
- [x] Log execution completed.
- [x] Log execution denied. (Implemented in `DatabaseService.log_query`)
- [x] Log MCP credential rotation or equivalent credential event.

## MCP Migration

- [x] Review current `mcp_server.py` auth model.
- [x] Replace database-only key semantics with workspace-aware credentials. (Keys are now bound to workspace-owned `UserDatabase`)
- [x] Ensure MCP requests resolve `org_id`, `workspace_id`, and target database.
- [x] Ensure MCP actions pass through policy and audit context.
- [x] Decide whether MCP credentials are workspace keys or service-account-style principals. (Decision: Workspace-scoped keys for Phase 1)

## Refactor Targets

- [x] Split auth routes into dedicated router and service.
- [x] Split database management routes into dedicated router and service.
- [x] Split query execution and generation orchestration into service layer.
- [x] Move provider selection and provider config out of `backend/utils/agent.py`.
- [x] Keep repository/CRUD layer focused on persistence only.

## Explicit Deferrals

- [x] Do not build admin UI in Phase 1.
- [x] Do not build workflow UI in Phase 1.
- [x] Do not add fine-grained `permission` table yet.
- [x] Do not build masking engine yet.
- [x] Do not build approval queue UI yet.
- [x] Do not build catalog generation yet.
- [x] Do not build multi-connector abstraction yet.

## Phase 1 Exit Criteria

- [x] Every protected request has tenant context.
- [ ] Existing users work through a default org/workspace. (Pending first run/backfill)
- [x] Audit writes exist for core auth and query actions.
- [x] JWT contract includes active workspace context.
- [x] MCP auth is no longer database-only in trust model.
- [x] Backend structure can support Phase 2 policy and RBAC without route-level sprawl.
