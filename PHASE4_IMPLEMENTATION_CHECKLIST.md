# SpeakQL Enterprise Phase 4 Checklist

This checklist is the execution tracker for Phase 4: workflow + catalog. It assumes Phase 1 tenancy, Phase 2 policy enforcement, and Phase 3 trust surfaces are sufficiently stable to support repeatable workflows on governed data access.

## Phase 4 Goal

Make SpeakQL indispensable for repeat work by turning one-off governed queries into reusable, reviewable, shareable, and semantically enriched workspace assets.

## Saved Queries Foundation

- [x] Add `saved_query` model and table.
- [x] Scope saved queries by `workspace_id`.
- [x] Store creator identity and timestamps.
- [x] Support saved-query status or visibility metadata (`private`, `workspace_shared`, `template`).
- [x] Store prompt, SQL, title, optional description, and tags.
- [x] Preserve the governed query reference used to create the saved query where applicable.
- [x] Add repository for saved-query persistence and listing.
- [x] Add service layer for save, update, delete, and replay operations.

## Templates and Replay

- [x] Allow saved queries to be promoted to reusable templates.
- [x] Support replay from query history into saved-query creation flow.
- [x] Support replay of a saved query against the same governed execution path used for ad hoc execution.
- [x] Record whether replay uses the original SQL, regenerated SQL, or a template parameterization path.
- [x] Ensure replay writes audit events with actor, workspace, source query/template, and target database context.

## SQL Diff and Result Snapshot Comparison

- [x] Add typed schema for SQL diff output.
- [x] Compute structural SQL diff using parsed SQL, not string comparison only.
- [x] Capture table additions/removals between saved-query runs.
- [x] Capture meaningful clause changes such as `WHERE`, `GROUP BY`, `ORDER BY`, and limit changes.
- [x] Add result snapshot metadata for saved-query runs.
- [x] Support result snapshot comparison at least at summary level (row count, changed columns, changed values count, or equivalent).
- [x] Keep diff and snapshot comparison on governed executions only.
- [x] Ensure snapshot storage has workspace-safe retention rules.

## Query Comments and Collaboration

- [x] Add `query_comment` model and table.
- [x] Scope comments by `workspace_id` and saved query or query-history entity.
- [x] Store author identity, timestamps, and edited state.
- [x] Support basic threaded discussion or explicitly document flat comments as the initial scope.
- [x] Add service and routes for creating, listing, editing, and deleting comments.
- [x] Audit comment creation and deletion events where required by workspace policy.

## Team Sharing and Access Model

- [x] Define sharing rules for saved queries and templates.
- [x] Ensure viewers can consume shared assets only within existing role boundaries.
- [x] Ensure analysts can create and share only within allowed workspace scope.
- [x] Reserve destructive mutation of shared assets to owners or admins according to workspace rules.
- [x] Ensure shared assets never bypass policy evaluation at replay time.

## Analyst-to-Admin Review Workflow

- [x] Extend approval/review model beyond destructive-query approval into reusable workflow review.
- [x] Support submission of saved queries or templates for admin review.
- [x] Support review statuses such as `draft`, `submitted`, `approved`, `rejected`, and `archived`.
- [x] Store reviewer identity, timestamps, and decision reason.
- [x] Ensure review decisions are workspace-scoped and auditable.
- [x] Ensure an approved workflow artifact still executes through current policy, masking, and trust checks at run time.

## Data Catalog Foundation

- [x] Add `catalog_entry` model and table.
- [x] Scope catalog entries by `workspace_id` and database.
- [x] Support table-level and column-level descriptions.
- [x] Store owner, freshness, status, and provenance metadata.
- [x] Support draft vs published catalog state.
- [x] Add repository and service for catalog CRUD and publication flow.
- [x] Ensure catalog entries can be generated as draft content on connection or refresh.

## Business Glossary

- [x] Add `business_term` model and table.
- [x] Scope glossary terms by `workspace_id`.
- [x] Store term, definition, synonyms, and mapping metadata.
- [x] Support mapping to table, column, and aggregation semantics where applicable.
- [x] Support certification metadata (`certified_by`, `certified_at`) where applicable.
- [x] Add repository and service for glossary CRUD and lookup.
- [x] Ensure glossary lookup can be used before prompt dispatch so semantic mappings influence SQL generation.

## Certified Metrics

- [x] Add `metric_definition` model and table.
- [x] Scope metrics by `workspace_id`.
- [x] Store metric name, SQL expression, description, owner, and certification metadata.
- [x] Distinguish draft metrics from certified metrics.
- [x] Ensure metric definitions execute through governed SQL validation and policy checks.
- [x] Prevent uncertified metrics from being represented as certified in API responses or UI contracts.

## Catalog and Semantic Resolution Path

- [x] Add service for resolving saved glossary terms and certified metrics into prompt context.
- [x] Ensure semantic resolution is explicit in explainability metadata where feasible.
- [x] Ensure catalog and glossary data are workspace-isolated.
- [x] Ensure semantic-layer enrichment never bypasses policy restrictions or masking requirements.
- [x] Add fallback behavior when no glossary or metric match exists.

## Scheduled Reports

- [x] Add `report` model and table.
- [x] Scope reports by `workspace_id`.
- [x] Store schedule definition, delivery configuration, last-run metadata, and enabled state.
- [x] Support scheduling from a saved query or approved template rather than arbitrary raw SQL.
- [x] Ensure scheduled executions run through the same governed execution, masking, export, and audit path as interactive execution.
- [x] Record report-run audit events with actor or service principal identity, workspace, source asset, and delivery target.
- [x] Add delivery adapters for email and Slack if in scope.
- [x] Ensure delivery failures are surfaced and audited without leaking result content to unauthorized channels.

## API and Data Contracts

- [x] Add typed schemas for saved queries, templates, comments, review workflow, catalog entries, glossary terms, metrics, report definitions, report runs, SQL diffs, and result snapshots.
- [x] Avoid loosely typed workflow payloads where stable contracts are possible.
- [x] Keep API contracts separated by domain: workflows, catalog, glossary, metrics, reports.
- [x] Version contracts if workflow payload complexity grows materially.

## Admin and End-User Backend Surfaces

- [x] Add routes for saved-query management.
- [x] Add routes for template management.
- [x] Add routes for query comments and collaboration.
- [x] Add routes for review workflow submission and decisioning.
- [x] Add routes for catalog entry and glossary management.
- [x] Add routes for certified metric management.
- [x] Add routes for scheduled report management and report-run history.
- [x] Keep all mutation routes role-safe and workspace-scoped.

## Audit and Governance Requirements

- [x] Write audit events for saved-query creation, update, deletion, sharing, replay, review submission, review decision, catalog publication, metric certification, report scheduling, and report delivery outcome.
- [x] Ensure every workflow and catalog audit event carries actor, workspace, request or job context, and target asset reference.
- [x] Ensure replayed workflows and scheduled reports remain subject to current policy state, not historical policy state only.
- [x] Ensure masking and explainability continue to apply when queries are run from saved assets, templates, or scheduled reports.

## Search and Discoverability

- [x] Add search/filter support for saved queries by title, tag, owner, status, and workspace visibility.
- [x] Add search/filter support for catalog entries, glossary terms, and metrics.
- [x] Ensure discoverability respects workspace and role boundaries.

## Explicit Deferrals

- [x] Do not introduce cross-workspace sharing in Phase 4.
- [x] Do not add full document-management or wiki features beyond workflow comments and catalog descriptions.
- [x] Do not add broad BI dashboarding in Phase 4 unless it is directly required for report delivery.
- [x] Do not treat semantic enrichment as a replacement for policy validation.

## Testing

- [x] Add tests for saved-query CRUD and workspace isolation.
- [x] Add tests for template promotion and replay behavior.
- [x] Add tests for SQL diff generation.
- [x] Add tests for result snapshot comparison.
- [x] Add tests for comment permissions and workspace isolation.
- [x] Add tests for review workflow state transitions and reviewer scoping.
- [x] Add tests for catalog draft generation and publish flow.
- [x] Add tests for glossary term resolution and metric resolution.
- [x] Add tests ensuring semantic-layer enrichment does not bypass governance.
- [x] Add tests for scheduled report execution, delivery, and audit events.
- [x] Add tests covering governed replay and governed scheduled execution across web and MCP where applicable.

## Phase 4 Exit Criteria

- [x] Users can save, organize, replay, and share governed queries as workspace assets.
- [x] Teams can review and comment on query assets without bypassing RBAC or governance.
- [x] SQL changes and result changes between runs are understandable through typed diff and comparison outputs.
- [x] Catalog, glossary, and certified metric foundations exist and influence query generation safely.
- [x] Scheduled reports execute through governed paths and produce auditable delivery outcomes.
- [x] Workflow and catalog surfaces are strong enough that repeat usage depends on the product, not only one-off chat interactions.
