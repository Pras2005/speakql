# SpeakQL Frontend Explainer

This document is for the frontend engineer building against the current backend.

The most important change is that database access is no longer workspace-wide by default. The UI must now treat database visibility and database actions as grant-driven.

## 1. Mental Model

There are two separate permission layers:

1. Workspace membership role
2. Per-database access grant

### Workspace membership role

Current roles returned through tenancy/workspace context:

- `admin`
- `compliance_admin`
- `analyst`
- `viewer`

These still matter for coarse route access and admin UI exposure.

### Per-database access grant

A user may only see or use a database if they have a grant for it, unless they are an `admin`.

Grant levels:

- `discover`
- `query`
- `export`
- `manage`

Interpret them like this:

- `discover`: user can inspect schema-oriented surfaces
- `query`: user can generate SQL, execute SQL, and explain SQL
- `export`: user can export query results
- `manage`: user can administer the database connector and grants

`admin` currently behaves as an override and can access all workspace databases.

## 2. What Changes In The UI

The old assumption was:

- if a user is in a workspace, they can see every database in that workspace

That assumption is now wrong.

The new assumption is:

- `GET /databases` returns only databases the current user can access
- if the list is empty, that may be a real permission state, not a loading error

Frontend implications:

- Database pickers in Workbench, Workflow, Reports, Catalog, and other views must use the filtered backend list as the source of truth.
- Do not hardcode admin-style visibility assumptions into selectors or empty states.
- “No databases available” may mean “you do not have any grants in this workspace.”
- Workspace switching should refetch database-backed queries immediately.

## 3. Endpoint Behavior The Frontend Must Respect

### Tenancy

- `GET /tenancy/memberships`
- `POST /tenancy/switch-workspace/{workspace_id}`

After workspace switch:

- replace the access token
- clear or invalidate workspace-scoped cached queries
- refetch `databases`, workflow lists, catalog views, approvals, reports, and audit data tied to the active workspace

### Database listing

- `GET /databases`

Returns:

- all workspace databases for `admin`
- only granted databases for non-admin users

This endpoint now doubles as both a data source and a permission filter.

### Connector management

These still require admin role, and now also require `manage` grant on the specific database:

- `PUT /databases/{db_id}`
- `DELETE /databases/{db_id}`
- `POST /databases/{db_id}/rotate-mcp-key`
- `POST /databases/{db_id}/refresh-catalog`

UI implication:

- even if the user has an admin-like shell view, a specific connector action can still fail with `403`
- handle those failures explicitly and show permission-oriented messaging

### Query and schema surfaces

Required grant levels:

- `POST /agent/generate-sql`: `query`
- `POST /agent/execute-sql`: `query`
- `POST /agent/explain-sql`: `query`
- `POST /agent/export-sql`: `export`
- `GET /agent/visualize-schema`: `discover`

UI implication:

- if export fails with `403`, that does not necessarily mean query access is missing; it may mean the user has `query` but not `export`
- the frontend should avoid assuming “can run query” implies “can export”

## 4. New Grant Management API

These endpoints exist for database grant management:

- `GET /databases/{db_id}/grants`
- `POST /databases/{db_id}/grants`
- `PATCH /databases/{db_id}/grants/{user_id}`
- `DELETE /databases/{db_id}/grants/{user_id}`

Current Phase 1 guard:

- backend protects them with `require_admin`

Payloads:

### Create grant

```json
{
  "user_id": 42,
  "access_level": "query"
}
```

### Update grant

```json
{
  "access_level": "manage"
}
```

Grant read shape:

```json
{
  "id": 7,
  "workspace_id": 3,
  "database_id": 12,
  "user_id": 42,
  "access_level": "query",
  "granted_by": 1,
  "created_at": "2026-04-27T01:23:45.000000",
  "updated_at": "2026-04-27T01:23:45.000000"
}
```

UI guidance:

- add a grant-management section on the database detail/admin surface
- model grant level as a single select, not a stack of booleans
- treat create and update as “set access level”
- delete means full revocation

## 5. Recommended Frontend States

### Empty states

For database-driven screens, prefer copy like:

- “No databases available in this workspace.”
- “You may not have access to any databases here yet.”

That is better than implying backend failure.

### Permission errors

Map `403` responses to action-specific messages:

- generate/execute/explain: “You do not have query access for this database.”
- export: “You do not have export access for this database.”
- connector admin actions: “You need manage access for this database.”

### Workspace switch behavior

On workspace switch:

- invalidate `databases`
- invalidate views that derive their options from `databases`
- clear any previously selected active database if it is no longer present in the new list

This matters especially for `WorkbenchView`, where the selected database can become invalid across workspaces.

## 6. Practical Implementation Notes

The existing frontend already centralizes database fetching through `client/src/api/databases.ts` and uses `['databases']` query keys in multiple views. That is good. Keep using the backend-filtered list as the canonical source rather than trying to infer permissions client-side.

Recommended next frontend tasks:

1. Add grant API helpers in `client/src/api/databases.ts` or a dedicated `client/src/api/grants.ts`.
2. Add TypeScript types for database grants and access levels in `client/src/lib/types.ts`.
3. Update database admin UI to show and edit grants.
4. Improve empty-state and `403` messaging in Workbench, Catalog, Workflow, and Reports.
5. On workspace switch, ensure stale selected database state is dropped if the new workspace does not include that database.

## 7. Important Constraint

The frontend should not try to reconstruct grant logic locally from role alone.

The safe rule is:

- use returned database lists for visibility
- use backend responses for authorization truth
- treat `403` as a valid business outcome, not just an exception path
