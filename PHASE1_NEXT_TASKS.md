# SpeakQL Phase 1 Next Tasks

This document captures the next concrete task set for Phase 1 based on the current implementation state. The goal is to close the gap between what is structurally present in the codebase and what is actually complete in behavior.

## Implementation Review Summary

Phase 1 is partially implemented, but several checklist items are currently marked complete based on structure rather than end-to-end behavior.

The main pattern is:
- core files and service/repository boundaries now exist,
- tenant models and audit models exist,
- but token issuance, tenant enforcement, backfill, auth audit, and MCP credential semantics are not fully complete.

## Confirmed Gaps and Corrections

### 1. JWT tenant context is not actually implemented end to end

The checklist marks the JWT payload contract as done, but `AuthService.create_user_token()` still only emits `sub`.

References:
- [backend/services/auth_service.py](/home/admin/Desktop/speakql/backend/services/auth_service.py)
- [PHASE1_IMPLEMENTATION_CHECKLIST.md](/home/admin/Desktop/speakql/PHASE1_IMPLEMENTATION_CHECKLIST.md)

Why this matters:
- `org_id`, `workspace_id`, `membership_id`, `role`, and `token_version` are required for actual active-workspace RBAC context.
- Current request context enrichment depends on fields that are not yet present in the token.

Action:
- Reclassify JWT payload implementation as incomplete until token issuance includes the full Phase 1 claim set.

### 2. Request context middleware currently handles request IDs, not tenant enforcement

The checklist says request context is attached and decode is implemented, but tenant rejection behavior is still incomplete.

References:
- [backend/middleware/request_context_middleware.py](/home/admin/Desktop/speakql/backend/middleware/request_context_middleware.py)
- [backend/auth/auth_bearer.py](/home/admin/Desktop/speakql/backend/auth/auth_bearer.py)

Why this matters:
- request IDs are being generated,
- JWT decoding happens in `JWTBearer`,
- but protected-route tenant enforcement is still distributed and incomplete.

Action:
- Treat “reject protected requests with invalid tenant context” as a first-class remaining Phase 1 task.

### 3. Backfill is still conceptual, not operational

The checklist correctly leaves backfill items open, but these are now the main blockers for a true Phase 1 exit.

References:
- [backend/services/tenant_service.py](/home/admin/Desktop/speakql/backend/services/tenant_service.py)
- [backend/models/tenant_model.py](/home/admin/Desktop/speakql/backend/models/tenant_model.py)

Why this matters:
- current tenant setup creates a default tenant for new signups,
- but existing users and existing resources are not yet backfilled,
- and tenant columns remain optional in key models such as [backend/models/db_model.py](/home/admin/Desktop/speakql/backend/models/db_model.py) and [backend/models/query_model.py](/home/admin/Desktop/speakql/backend/models/query_model.py).

Action:
- Backfill and constraint-tightening must become the top migration workstream.

### 4. Audit exists, but core auth audit is still missing

The audit model and service exist, but auth audit events are still not being written for login success and login failure.

References:
- [backend/services/audit_service.py](/home/admin/Desktop/speakql/backend/services/audit_service.py)
- [backend/routers/auth_routes.py](/home/admin/Desktop/speakql/backend/routers/auth_routes.py)

Why this matters:
- Phase 1 exit requires audit coverage for core auth and query actions,
- and auth is the biggest missing event family right now.

Action:
- Add login success and login failure audit writes before marking Phase 1 audit complete.

### 5. MCP is workspace-aware in shape, but not yet resolved at the principal model level

The checklist correctly leaves the principal decision open.

References:
- [backend/mcp_server.py](/home/admin/Desktop/speakql/backend/mcp_server.py)
- [backend/repositories/database_repository.py](/home/admin/Desktop/speakql/backend/repositories/database_repository.py)

Why this matters:
- the server now resolves requests through database records carrying tenant columns,
- but the actual credential model is still effectively database-key driven,
- and that is weaker than a workspace principal or service-account style model.

Action:
- Decide and document the Phase 1 MCP credential model before Phase 1 is declared complete.

### 6. Logging is still the largest missing infrastructure primitive

The checklist is accurate that logging is still pending.

References:
- [backend/core/config.py](/home/admin/Desktop/speakql/backend/core/config.py)
- [backend/main.py](/home/admin/Desktop/speakql/backend/main.py)

Why this matters:
- request IDs exist,
- audit exists,
- but there is not yet one encapsulated operational logging layer that binds request context consistently.

Action:
- Implement `backend/core/logging.py` and bind request-scoped fields through one logger path.

## Next Phase 1 Task Set

The next task set should focus on correctness and closure, not more structural scaffolding.

## Task Group A — Finish JWT and active workspace flow

- [ ] Update token issuance to include `sub`, `org_id`, `workspace_id`, `membership_id`, `role`, and `token_version`.
- [ ] Decide how login selects the initial active workspace.
- [ ] Add workspace-switch token reissue flow.
- [ ] Add token version support for future revocation.
- [ ] Update checklist items that currently overstate JWT completion.

## Task Group B — Enforce tenant context on protected routes

- [ ] Define which routes require tenant context versus user-only auth.
- [ ] Add a reusable tenant guard or dependency for protected workspace routes.
- [ ] Reject requests where JWT is valid but workspace claims are missing or inconsistent.
- [ ] Ensure request context population and protected-route enforcement use one consistent path.
- [ ] Stop relying on implicit “optional” tenant context for tenant-owned operations.

## Task Group C — Execute the actual backfill path

- [ ] Implement default organization creation for legacy users.
- [ ] Implement default workspace creation for legacy users.
- [ ] Backfill memberships for existing users.
- [ ] Backfill `org_id` and `workspace_id` for existing `user_database` rows.
- [ ] Backfill `org_id` and `workspace_id` for existing `query_history` rows.
- [ ] Add the Alembic migration sequence instead of leaving it deferred.
- [ ] Tighten nullable tenant columns only after backfill is verified.

## Task Group D — Close auth audit coverage

- [ ] Write audit event for login success.
- [ ] Write audit event for login failure.
- [ ] Confirm signup/default-tenant creation path emits the required audit trail or explicitly defer it.
- [ ] Re-check Phase 1 exit criteria once auth audit is in place.

## Task Group E — Finish encapsulated logging

- [ ] Add `backend/core/logging.py`.
- [ ] Bind `request_id`, `user_id`, `org_id`, `workspace_id`, and `membership_id` into logs.
- [ ] Replace ad hoc logging patterns with the central logger path.
- [ ] Ensure no sensitive values are emitted by default.

## Task Group F — Finalize MCP credential semantics

- [ ] Decide between workspace-scoped API keys and service-account style principals.
- [ ] Record that decision in the architecture docs and checklist.
- [ ] Align `mcp_server.py` behavior with the chosen principal model.
- [ ] Ensure audit events reflect the MCP actor identity model clearly.

## Task Group G — Reconcile the checklist with reality

- [ ] Review every `[x]` item and confirm it is behaviorally complete, not just structurally started.
- [ ] Downgrade any overstated items in [PHASE1_IMPLEMENTATION_CHECKLIST.md](/home/admin/Desktop/speakql/PHASE1_IMPLEMENTATION_CHECKLIST.md).
- [ ] Add small verification notes to completed items where useful.

## Recommended Execution Order

1. Finish JWT issuance and active workspace semantics.
2. Add protected-route tenant enforcement.
3. Implement auth audit writes.
4. Add centralized logging.
5. Execute data backfill plus Alembic migration path.
6. Finalize MCP principal model.
7. Reconcile the checklist and re-evaluate Phase 1 exit criteria.

## Proposed Definition of “Phase 1 Done”

Phase 1 should only be considered done when all of the following are true:

- every protected request carries valid tenant context,
- access tokens include active workspace claims,
- existing users and legacy resources are backfilled,
- auth and query actions write audit events,
- the backend has one centralized logging path,
- MCP trust model is explicitly defined,
- and the checklist reflects behavioral truth rather than structural intent.
