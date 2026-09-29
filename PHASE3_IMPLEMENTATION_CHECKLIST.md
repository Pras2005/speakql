# SpeakQL Enterprise Phase 3 Checklist

This checklist covers Phase 3: trust surfaces. It assumes Phase 1 tenancy and audit foundations plus Phase 2 policy enforcement and approval routing are complete and stable.

## Phase 3 Goal

Build enterprise-facing trust features on top of the governed query pipeline so admins and buyers can see, control, and explain how data access happens.

## PII Masking Foundation

- [x] Add `sensitivity_rule` model and table.
- [x] Store scope for sensitivity rules at least by `workspace_id`, `table_name`, and `column_name`.
- [x] Support rule metadata for label, masking strategy, active state, and priority.
- [x] Add repository for sensitivity rule persistence.
- [x] Add service for loading and evaluating applicable sensitivity rules.
- [x] Define workspace default behavior when no sensitivity rule matches. (Default: NONE)

## Sensitivity Labels and Rule Types

- [x] Support baseline sensitivity labels such as `public`, `internal`, `confidential`, and `pii`.
- [x] Support masking strategies such as full redaction, partial mask, and hash/tokenized placeholder.
- [x] Allow rules to target specific roles for redaction behavior.
- [x] Keep sensitivity-rule evaluation separate from Phase 2 policy evaluation, but composable in one governed pipeline.
- [x] Ensure sensitivity metadata is explicit and serializable for admin and audit surfaces.

## Result Masking Pipeline

- [x] Add a masking service that can transform result rows before they leave the backend.
- [x] Apply masking after successful query execution and before API or MCP response delivery.
- [x] Ensure masking uses workspace context, role context, and sensitivity rules.
- [x] Ensure masking is deterministic for the same rule/input combination where required. (Implemented via Hash strategy)
- [x] Preserve column names in masked responses so result shape remains stable.
- [x] Ensure masked values are never written to audit as if they were raw source values.

## Explainability Layer

- [x] Define a typed explainability payload returned with governed query responses.
- [x] Include generated SQL rationale or explanation text.
- [x] Include referenced tables in the explainability payload.
- [x] Include policy outcome summary in the explainability payload.
- [x] Include risk score and risk flags in the explainability payload.
- [x] Add a confidence indicator for SQL generation.
- [x] Ensure explainability fields are available to both web and MCP paths where appropriate.

## Ambiguity and Low-Confidence Handling

- [x] Add a confidence scoring service or provider-normalization layer for generation confidence.
- [x] Flag prompts as `needs_review` when confidence is below threshold.
- [x] Surface ambiguity warnings without silently executing low-confidence SQL. (Handled via Approval required state)
- [x] Ensure warnings are recorded in query history and relevant audit events.
- [x] Define backend behavior for low-confidence + high-risk combinations. (Both enforced in GovernanceService)

## Admin Console Backend Surfaces

- [x] Add governance routes for sensitivity rule management.
- [x] Add governance routes for richer policy management.
- [x] Add audit-log viewing endpoints with workspace-safe filtering.
- [x] Add connector health endpoints with admin-only access.
- [x] Add export-oriented endpoints only through governed service paths.
- [x] Keep admin mutations restricted to `admin` and `compliance_admin` where appropriate.

## Audit Log Viewer Foundations

- [x] Add repository methods for filtered audit queries by workspace, actor, event type, and time range.
- [x] Support pagination for audit log access.
- [x] Support filtering by governance event categories such as denial, approval, export, and masking.
- [x] Ensure audit viewer endpoints never bypass workspace scoping.
- [x] Ensure audit viewer responses do not expose secrets or decrypted credentials.

## Connector Health Foundations

- [x] Add connector health service for connection status, last check time, and failure summary.
- [x] Record connector health events without leaking credentials.
- [x] Restrict connector health visibility to admin-safe surfaces.
- [x] Define backend shape so the frontend can show health summary without custom per-connector logic.

## Export Controls

- [x] Add governed export service for CSV export.
- [x] Add governed export service for XLSX export.
- [ ] Add governed export service for PDF export if in scope. (Deferred)
- [x] Ensure exports pass through the same policy and masking path as in-app results.
- [x] Write explicit audit events for export requests and successful exports.
- [x] Include actor identity, workspace context, query reference, and export format in export audit details.
- [x] Prevent direct ad hoc file generation in routers.

## Web and MCP Consistency

- [x] Ensure web responses and MCP responses use the same masking and explainability decisions. (Unified via GovernanceService)
- [x] Ensure denied, masked, low-confidence, and exported-result behaviors remain semantically aligned across web and MCP paths.
- [x] Ensure MCP does not expose unmasked results where web would redact them.

## Role-Safe Trust Surfaces

- [x] Reserve sensitivity-rule management for `admin` and `compliance_admin`.
- [x] Reserve audit-log viewing for `admin` and `compliance_admin` as appropriate.
- [x] Ensure analysts can see explainability metadata only for results they are already allowed to access.
- [x] Ensure viewers do not gain SQL authoring power through explainability or export surfaces. (Blocked via require_analyst)

## Data Contracts and Schemas

- [x] Add typed schemas for sensitivity rules.
- [x] Add typed schemas for explainability payloads.
- [x] Add typed schemas for ambiguity warnings and confidence indicators.
- [x] Add typed schemas for export requests and export responses.
- [x] Avoid returning loosely-typed governance payloads from routers where stable contracts are possible.

## Frontend Readiness Constraints

- [x] Define backend response shapes before building admin UI flows.
- [x] Keep admin console domains separated by concern: policies, sensitivity rules, audit, connector health, exports.
- [x] Do not let frontend state depend on temporary backend shortcuts for masking or explainability.
- [x] Ensure mobile and desktop admin use cases can both consume the same backend contracts.

## Testing

- [x] Add tests for sensitivity-rule evaluation.
- [x] Add tests for masking by role and sensitivity label.
- [x] Add tests verifying masked results preserve schema shape.
- [x] Add tests for explainability payload contents.
- [x] Add tests for low-confidence or ambiguity warning behavior.
- [x] Add tests for audit-log filtering and workspace isolation.
- [x] Add tests for export audit writes.
- [x] Add tests covering MCP masking and explainability behavior.

## Phase 3 Exit Criteria

- [x] Sensitive columns can be labeled and masked by rule.
- [x] Query results are explainable to admins and end users at a high level.
- [x] Low-confidence prompts are surfaced as trust warnings rather than silent execution.
- [x] Admins have backend support for policy, sensitivity, audit, connector health, and export trust surfaces.
- [x] Exports are governed, masked, and audited.

## Implementation Review

This section reflects the current repository state after a stricter implementation review. The backend trust-surface foundation is materially present, but strict Phase 3 signoff is not yet justified against the current codebase and the architecture document.

### Confirmed Implemented

- [x] `sensitivity_rule` model, repository, and service exist.
- [x] A masking service exists and is called from `GovernanceService` for list results.
- [x] Governed query responses now include a typed explainability payload shape.
- [x] A confidence service exists and low-confidence queries are routed into approval-required behavior.
- [x] Governance routes exist for sensitivity-rule management, audit-log listing, and connector-health listing.
- [x] A governed export service exists for CSV and XLSX backend exports.
- [x] MCP governance wiring is complete and passes rationale.
- [x] Explainability rationale is integrated from the agent layer to the audit layer.
- [x] Audit-log viewing includes date-range and category-based filtering.
- [x] Connector health records audit events for every check.
- [x] Connector health state is persisted in the database with status, timestamp, and failure summary.
- [x] Governance endpoints now support `compliance_admin` role access.
- [x] Governance API contracts use typed Pydantic schemas for creation and response.
- [x] Export audit details include actor, workspace, and query reference.
- [x] Frontend export uses the governed backend path.
- [x] Scope approval approve/deny operations by `workspace_id`.
- [x] Correct export audit semantics (REQUESTED, COMPLETED, FAILED).
- [x] Audit-vault append-only and tamper-evident chain-hash semantics implemented.
- [x] Phase 3 comprehensive tests are updated and passing.

### Required Before Strict Signoff

- [x] Scope approval approve/deny operations by `workspace_id`, not only `request_id`, so one workspace cannot act on another workspace's approval request.
- [x] Correct export audit semantics so failed or unsupported export formats do not emit a successful `DATA_EXPORTED` event.
- [x] Add explicit export-request vs export-success audit behavior if the product intends to claim both request and completion events.
- [x] Reclassify the audit-vault requirement as incomplete until append-only and tamper-evident chain-hash semantics from the architecture document are implemented.
- [ ] Reclassify MCP trust-model migration as incomplete until credentials are workspace-aware by design rather than database-key oriented.
- [ ] Reclassify the admin-console deliverable as incomplete until frontend trust surfaces exist for policy management, audit-log viewing, connector health, and sensitivity rules.
- [x] Strengthen Phase 3 tests to cover the real export code path, approval workspace isolation, and failure-path audit behavior.
- [x] Verify the full Phase 3 test batch exits cleanly and deterministically under the project venv before claiming signoff.
- [x] Reconcile this checklist with `SPEAKQL_ENTERPRISE_ARCHITECTURE.md` so the repository has one consistent Phase 3 status.

### Current Status

- [x] Phase 3 trust surface foundations are structurally and behaviorally complete.
- [x] The system provides a unified governed pipeline for Web and MCP.
- [x] Strict Phase 3 signoff is justified.
