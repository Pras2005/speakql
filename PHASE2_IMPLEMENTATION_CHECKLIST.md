# SpeakQL Enterprise Phase 2 Checklist

This checklist covers Phase 2: policy engine and RBAC enforcement. It assumes Phase 1 tenancy, request context, audit, and workspace-scoped auth are complete and stable.

## Phase 2 Goal

Enforce governed access control so every query is evaluated against workspace policy before execution.

## RBAC Completion

- [x] Add explicit role guard utilities for `viewer`, `analyst`, `admin`, and `compliance_admin`. (Implemented in `auth/auth_guards.py`)
- [x] Ensure workspace role checks are reusable and not embedded ad hoc in route handlers.
- [x] Define which actions are role-gated at the service layer versus route layer.
- [x] Restrict SQL editing for `viewer`. (Blocked via `require_analyst` in `agent_routes.py`)
- [x] Restrict sensitive data access for `analyst` according to policy outcome. (Enforced via `GovernanceService` + `PolicyService`)
- [x] Reserve policy management, connector management, and audit export for `admin` and `compliance_admin` as appropriate.

## Policy Data Model

- [x] Add `policy` model and table.
- [x] Add `priority`, `active`, and `rules_json` fields.
- [x] Add repository for policy persistence.
- [x] Add service for policy loading and evaluation.
- [x] Define workspace default behavior when no policy matches.

## SQL Validation Engine

- [x] Introduce `sqlglot` for AST-based SQL parsing.
- [x] Replace regex-only SQL safety checks with AST validation.
- [x] Detect statement class from parsed AST.
- [x] Detect blocked DDL and destructive operations using AST nodes.
- [x] Extract referenced tables from AST.
- [x] Reject invalid SQL before execution.

## Policy Rule Enforcement

- [x] Enforce allowed SQL classes.
- [x] Enforce blocked keywords or blocked operation types.
- [x] Enforce allowed schemas. (Implemented in `PolicyService`)
- [x] Enforce allowed tables.
- [x] Enforce blocked tables.
- [x] Enforce row limit policy.
- [x] Enforce execution timeout policy. (Implemented in `GovernanceService`)
- [x] Enforce result size cap policy. (Implemented in `GovernanceService`)

## Approval Flow Foundation

- [x] Add `approval_request` model and table.
- [x] Add repository and service for approval requests.
- [x] Mark destructive or high-risk queries as approval-required instead of executing them.
- [x] Record approval-request audit events.
- [x] Define pending, approved, and denied states.
- [x] Complete the backend state machine. (Implemented in `GovernanceService` and `governance_routes.py`)

## Query Execution Pipeline

- [x] Refactor execution flow into explicit pipeline stages:
  - [x] policy check
  - [x] AST parse
  - [x] risk evaluation
  - [x] execution decision
  - [x] audit write
  - [x] query-history write
- [x] Ensure failures at intermediate stages still write audit events.
- [x] Ensure denied queries do not silently drop out of history.

## Denial and Audit Coverage

- [x] Write policy-denied audit events with explicit reason. (Implemented in `DatabaseService.log_query`)
- [x] Write approval-requested audit events.
- [x] Write approval-granted and approval-denied audit events. (Implemented in `governance_routes.py`)
- [x] Include policy result and denial reason in audit details.
- [x] Ensure `request_id`, `org_id`, `workspace_id`, and actor identity are present in all policy-related audit events.

## Risk and Governance Foundations

- [x] Add a first-pass risk scoring service for generated SQL.
- [x] Flag write operations as high-risk.
- [x] Flag full-table scans and `SELECT *` patterns.
- [x] Mark queries that require approval.
- [x] Expose risk metadata in service responses even before full UI support exists.

## MCP and Policy Integration

- [x] Ensure MCP requests pass through the same policy evaluation path as web requests. (Unified via `GovernanceService`)
- [x] Ensure MCP-denied requests produce the same audit semantics as web-denied requests.
- [x] Confirm workspace-scoped MCP credentials remain consistent with Phase 2 authorization behavior.

## Role-Safe API Surfaces

- [x] Review existing routes for role enforcement gaps.
- [x] Add admin-only protection to tenant and governance mutation endpoints as needed.
- [x] Prevent non-admin users from rotating credentials or changing governance state unless explicitly allowed.

## Testing

- [x] Add tests for AST parsing success and failure. (Verified in `test_phase2.py`)
- [x] Add tests for allowed and denied query classes. (Verified in `test_phase2.py`)
- [x] Add tests for workspace policy evaluation. (Verified in `test_phase2.py`)
- [x] Add tests for role-restricted actions. (Verified in `test_phase2.py`)
- [x] Add tests for approval-required queries. (Verified in `test_phase2.py`)
- [x] Add tests for denied-query audit writes. (Verified in `test_phase2.py`)
- [x] Add tests covering MCP policy enforcement. (Verified in `test_phase2.py`)

## Phase 2 Exit Criteria

- [x] Every query is evaluated by a workspace-aware policy path before execution.
- [x] Regex safety is no longer the primary enforcement mechanism.
- [x] Role restrictions are enforced consistently for web and MCP access.
- [x] Denied and approval-required queries are audited with explicit reasons.
- [x] High-risk queries can be identified and routed without direct execution.

## Verification Notes

- `backend/test_phase2.py` passes inside the repo-local venv at `backend/.venv`.
- PolicyService and GovernanceService now support schema allowlists, execution timeouts, and result size caps.
- Approval audit attribution fixed to use `org_id` from token.
- MCP Server and Agent routes share the same `GovernanceService` pipeline.
- `backend/test_phase2.py` now includes denied-audit coverage and an MCP governance-path test.
