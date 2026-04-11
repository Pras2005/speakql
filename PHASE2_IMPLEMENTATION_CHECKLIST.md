# SpeakQL Enterprise Phase 2 Checklist

This checklist covers Phase 2: policy engine and RBAC enforcement. It assumes Phase 1 tenancy, request context, audit, and workspace-scoped auth are complete and stable.

## Phase 2 Goal

Enforce governed access control so every query is evaluated against workspace policy before execution.

## RBAC Completion

- [ ] Add explicit role guard utilities for `viewer`, `analyst`, `admin`, and `compliance_admin`.
- [ ] Ensure workspace role checks are reusable and not embedded ad hoc in route handlers.
- [ ] Define which actions are role-gated at the service layer versus route layer.
- [ ] Restrict SQL editing for `viewer`.
- [ ] Restrict sensitive data access for `analyst` according to policy outcome.
- [ ] Reserve policy management, connector management, and audit export for `admin` and `compliance_admin` as appropriate.

## Policy Data Model

- [ ] Add `policy` model and table.
- [ ] Add `priority`, `active`, and `rules_json` fields.
- [ ] Add repository for policy persistence.
- [ ] Add service for policy loading and evaluation.
- [ ] Define workspace default behavior when no policy matches.

## SQL Validation Engine

- [ ] Introduce `sqlglot` for AST-based SQL parsing.
- [ ] Replace regex-only SQL safety checks with AST validation.
- [ ] Detect statement class from parsed AST.
- [ ] Detect blocked DDL and destructive operations using AST nodes.
- [ ] Extract referenced tables from AST.
- [ ] Reject invalid SQL before execution.

## Policy Rule Enforcement

- [ ] Enforce allowed SQL classes.
- [ ] Enforce blocked keywords or blocked operation types.
- [ ] Enforce allowed schemas.
- [ ] Enforce allowed tables.
- [ ] Enforce blocked tables.
- [ ] Enforce row limit policy.
- [ ] Enforce execution timeout policy.
- [ ] Enforce result size cap policy.

## Approval Flow Foundation

- [ ] Add `approval_request` model and table.
- [ ] Add repository and service for approval requests.
- [ ] Mark destructive or high-risk queries as approval-required instead of executing them.
- [ ] Record approval-request audit events.
- [ ] Define pending, approved, and denied states.
- [ ] Keep UI deferred if needed, but complete the backend state machine.

## Query Execution Pipeline

- [ ] Refactor execution flow into explicit pipeline stages:
- [ ] policy check
- [ ] AST parse
- [ ] risk evaluation
- [ ] execution decision
- [ ] audit write
- [ ] query-history write
- [ ] Ensure failures at intermediate stages still write audit events.
- [ ] Ensure denied queries do not silently drop out of history.

## Denial and Audit Coverage

- [ ] Write policy-denied audit events with explicit reason.
- [ ] Write approval-requested audit events.
- [ ] Write approval-granted and approval-denied audit events when workflow exists.
- [ ] Include policy result and denial reason in audit details.
- [ ] Ensure `request_id`, `org_id`, `workspace_id`, and actor identity are present in all policy-related audit events.

## Risk and Governance Foundations

- [ ] Add a first-pass risk scoring service for generated SQL.
- [ ] Flag write operations as high-risk.
- [ ] Flag full-table scans and `SELECT *` patterns.
- [ ] Mark queries that require approval.
- [ ] Expose risk metadata in service responses even before full UI support exists.

## MCP and Policy Integration

- [ ] Ensure MCP requests pass through the same policy evaluation path as web requests.
- [ ] Ensure MCP-denied requests produce the same audit semantics as web-denied requests.
- [ ] Confirm workspace-scoped MCP credentials remain consistent with Phase 2 authorization behavior.

## Role-Safe API Surfaces

- [ ] Review existing routes for role enforcement gaps.
- [ ] Add admin-only protection to tenant and governance mutation endpoints as needed.
- [ ] Prevent non-admin users from rotating credentials or changing governance state unless explicitly allowed.

## Testing

- [ ] Add tests for AST parsing success and failure.
- [ ] Add tests for allowed and denied query classes.
- [ ] Add tests for workspace policy evaluation.
- [ ] Add tests for role-restricted actions.
- [ ] Add tests for approval-required queries.
- [ ] Add tests for denied-query audit writes.
- [ ] Add tests covering MCP policy enforcement.

## Phase 2 Exit Criteria

- [ ] Every query is evaluated by a workspace-aware policy path before execution.
- [ ] Regex safety is no longer the primary enforcement mechanism.
- [ ] Role restrictions are enforced consistently for web and MCP access.
- [ ] Denied and approval-required queries are audited with explicit reasons.
- [ ] High-risk queries can be identified and routed without direct execution.
