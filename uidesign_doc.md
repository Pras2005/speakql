# SpeakQL frontend engineering & design guide

**Version:** 1.0  
**Audience:** Frontend engineers and AI agents building against the SpeakQL backend  
**Source:** `explainer.md` + interactive UI mockup  
**Status:** Active — reflects Phase 1 grant system

---

## Table of contents

1. [Mental model](#1-mental-model)
2. [Permission layers in detail](#2-permission-layers-in-detail)
3. [API reference for the frontend](#3-api-reference-for-the-frontend)
4. [State management strategy](#4-state-management-strategy)
5. [Component design patterns](#5-component-design-patterns)
6. [Empty states and error messaging](#6-empty-states-and-error-messaging)
7. [Workspace switching behaviour](#7-workspace-switching-behaviour)
8. [Grant management UI](#8-grant-management-ui)
9. [TypeScript types](#9-typescript-types)
10. [Implementation checklist](#10-implementation-checklist)

---

## 1. Mental model

SpeakQL uses **two independent permission layers** that must both be satisfied before a user can act on a database. Neither layer alone is sufficient.

```
┌─────────────────────────────────────────┐
│         Workspace membership role        │  → controls: route access, admin UI
│  admin | compliance_admin | analyst | viewer │
└───────────────────┬─────────────────────┘
                    │ AND
┌───────────────────▼─────────────────────┐
│         Per-database access grant        │  → controls: visibility, actions
│   discover | query | export | manage    │
└─────────────────────────────────────────┘
```

### The single most important rule

> The frontend must **never reconstruct grant logic locally**. Always use backend-returned data as the source of truth.

This means:

- Use `GET /databases` to determine which databases a user can see — do not derive visibility from role alone.
- Use `403` responses to determine whether an action is permitted — do not pre-check client-side.
- Treat an empty database list as a valid permission state, not a loading error.

---

## 2. Permission layers in detail

### 2.1 Workspace membership roles

| Role | Description |
|---|---|
| `admin` | Full workspace access. Bypasses per-database grant checks — sees all databases. |
| `compliance_admin` | Elevated for compliance surfaces. Still subject to database grants. |
| `analyst` | Standard data user. Subject to database grants. |
| `viewer` | Read-only workspace presence. Subject to database grants. |

Roles govern **coarse route access** (e.g. whether the admin panel is visible in the nav) and some UI exposure decisions. They do not replace database grants for data access.

### 2.2 Per-database grant levels

Grants are **additive upward** — each level includes everything below it.

| Grant | Capabilities |
|---|---|
| `discover` | Inspect schema surfaces (`GET /agent/visualize-schema`) |
| `query` | Generate SQL, execute SQL, explain SQL — includes `discover` |
| `export` | Export query results — includes `query` |
| `manage` | Administer the connector and edit grants — includes `export` |

**Critical:** `export` is not implied by `query`. A user may have `query` but not `export`. Never assume upward.

### 2.3 Admin override

A user with the `admin` workspace role behaves as if they have `manage` grant on every database in the workspace. `GET /databases` returns all databases for admins. The frontend should not hardcode this assumption — it is enforced on the backend and reflected in the response.

---

## 3. API reference for the frontend

### 3.1 Tenancy

#### `GET /tenancy/memberships`
Returns the current user's workspace memberships and their role in each.

**Use for:** populating the workspace switcher, determining role for coarse UI decisions.

#### `POST /tenancy/switch-workspace/{workspace_id}`
Switches the active workspace and returns a new access token.

**After this call, the frontend must:**
1. Replace the stored access token.
2. Clear all workspace-scoped cached queries (React Query: invalidate by workspace key prefix).
3. Refetch: `databases`, workflow lists, catalog views, approvals, reports, audit data.
4. Drop any selected active database that no longer appears in the new database list.

---

### 3.2 Database listing

#### `GET /databases`
Returns databases the current user is permitted to access.

- `admin` → all workspace databases
- non-admin → only databases with an explicit grant

**This endpoint doubles as both data source and permission filter.** It is the canonical list. Do not fetch all databases and filter client-side.

**React Query key:** `['databases', workspaceId]`

**Empty response handling:**
```ts
if (databases.length === 0) {
  // Valid state — show empty state copy, not a loading spinner or error
}
```

---

### 3.3 Connector management

These require both `admin` role **and** `manage` grant on the specific database.

| Endpoint | Action |
|---|---|
| `PUT /databases/{db_id}` | Update connector config |
| `DELETE /databases/{db_id}` | Remove connector |
| `POST /databases/{db_id}/rotate-mcp-key` | Rotate MCP key |
| `POST /databases/{db_id}/refresh-catalog` | Refresh schema catalog |

Even when the user has an admin shell view, these can return `403` if the `manage` grant is missing. Handle these failures explicitly — see [§6 Error messaging](#6-empty-states-and-error-messaging).

---

### 3.4 Query and schema surfaces

| Endpoint | Required grant | Notes |
|---|---|---|
| `POST /agent/generate-sql` | `query` | |
| `POST /agent/execute-sql` | `query` | |
| `POST /agent/explain-sql` | `query` | |
| `POST /agent/export-sql` | `export` | Not implied by `query` |
| `GET /agent/visualize-schema` | `discover` | Available to all grant levels |

---

### 3.5 Grant management

Phase 1: all grant management endpoints are protected by `require_admin`.

| Endpoint | Action |
|---|---|
| `GET /databases/{db_id}/grants` | List all grants for a database |
| `POST /databases/{db_id}/grants` | Create a grant |
| `PATCH /databases/{db_id}/grants/{user_id}` | Update a grant |
| `DELETE /databases/{db_id}/grants/{user_id}` | Revoke a grant |

#### Create grant payload
```json
{
  "user_id": 42,
  "access_level": "query"
}
```

#### Update grant payload
```json
{
  "access_level": "manage"
}
```

#### Grant read shape
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

---

## 4. State management strategy

### 4.1 Query key structure

Organise React Query keys around workspace and database scope so workspace switching invalidates the right queries automatically.

```ts
// Workspace-scoped
['databases', workspaceId]
['workflows', workspaceId]
['catalog', workspaceId]
['reports', workspaceId]
['approvals', workspaceId]

// Database-scoped
['grants', workspaceId, databaseId]
['schema', workspaceId, databaseId]
```

### 4.2 On workspace switch

```ts
async function handleWorkspaceSwitch(workspaceId: string) {
  const { token } = await switchWorkspace(workspaceId);
  setAccessToken(token);

  // Invalidate all workspace-scoped data
  queryClient.invalidateQueries({ queryKey: ['databases'] });
  queryClient.invalidateQueries({ queryKey: ['workflows'] });
  queryClient.invalidateQueries({ queryKey: ['catalog'] });
  queryClient.invalidateQueries({ queryKey: ['reports'] });
  queryClient.invalidateQueries({ queryKey: ['approvals'] });

  // Drop stale selected database
  const newDatabases = await queryClient.fetchQuery(['databases', workspaceId]);
  const currentDb = getSelectedDatabase();
  if (currentDb && !newDatabases.find(db => db.id === currentDb.id)) {
    clearSelectedDatabase();
  }
}
```

### 4.3 Deriving capabilities from the selected database

Do not derive capabilities from the workspace role. Derive them from the `access_level` field on the database grant returned by `GET /databases`.

```ts
const GRANT_RANK: Record<AccessLevel, number> = {
  discover: 1,
  query:    2,
  export:   3,
  manage:   4,
};

function can(userGrant: AccessLevel, required: AccessLevel): boolean {
  return GRANT_RANK[userGrant] >= GRANT_RANK[required];
}

// Usage
const grant = selectedDatabase?.access_level;
const canQuery  = grant ? can(grant, 'query')  : false;
const canExport = grant ? can(grant, 'export') : false;
const canManage = grant ? can(grant, 'manage') : false;
```

Use these flags to **disable controls proactively** in the UI. They should never be the authoritative source for server-side enforcement — that remains the backend. They exist to prevent user confusion, not to enforce security.

---

## 5. Component design patterns

### 5.1 Sidebar database list

The sidebar database picker renders the filtered list from `GET /databases`. Each item shows:

- Connection status dot (green = healthy, amber = degraded)
- Database name
- Grant level pill (`discover` / `query` / `export` / `manage`)

```tsx
<DatabaseItem
  db={db}
  isActive={db.id === selectedDb?.id}
  onClick={() => setSelectedDatabase(db)}
>
  <StatusDot status={db.connection_status} />
  <span>{db.name}</span>
  <GrantPill level={db.access_level} />
</DatabaseItem>
```

**Grant pill colour mapping:**

| Level | Background | Text colour |
|---|---|---|
| `discover` | `#EEEDFE` (purple-50) | `#3C3489` (purple-800) |
| `query` | `#E1F5EE` (teal-50) | `#085041` (teal-800) |
| `export` | `#FAEEDA` (amber-50) | `#633806` (amber-800) |
| `manage` | `#E6F1FB` (blue-50) | `#0C447C` (blue-800) |

### 5.2 Capability bar

Render a persistent capability bar at the top of the Workbench editor area. It should update whenever `selectedDatabase` changes.

```tsx
<CapabilityBar database={selectedDatabase}>
  <Capability label="schema"  active={can(grant, 'discover')} />
  <Capability label="query"   active={can(grant, 'query')}    />
  <Capability label="export"  active={can(grant, 'export')}   />
  <Capability label="manage"  active={can(grant, 'manage')}   />
</CapabilityBar>
```

Active capabilities use a filled green dot + green background pill. Inactive capabilities use a muted dot + neutral background. This gives users a persistent affordance so they are never surprised by a 403 mid-workflow.

### 5.3 Action buttons

Disable (not hide) action buttons when the required grant is absent. Hiding removes discoverability — the user should understand what is possible with higher grants.

```tsx
<button
  onClick={handleRun}
  disabled={!canQuery}
  aria-disabled={!canQuery}
>
  Run query
</button>

<button
  onClick={handleExport}
  disabled={!canExport}
  aria-disabled={!canExport}
  title={!canExport ? 'You need export access for this database' : undefined}
>
  Export CSV
</button>
```

### 5.4 Database picker in views other than Workbench

Workflow, Reports, and Catalog all contain database selectors. All of them must source their list from `['databases', workspaceId]`. Never hardcode a full list and filter locally.

```tsx
const { data: databases = [] } = useQuery({
  queryKey: ['databases', workspaceId],
  queryFn: fetchDatabases,
});

// Pass the filtered list directly — no local filtering by role
<DatabaseSelect options={databases} />
```

---

## 6. Empty states and error messaging

### 6.1 Empty database list

When `GET /databases` returns an empty array, show a permission-aware empty state. Do not show a loading spinner, a retry button, or anything that implies backend failure.

**Preferred copy:**
> "No databases available in this workspace."
> "You may not have access to any databases here yet. Contact your workspace admin to request access."

**Avoid:**
> "Failed to load databases." ✗  
> "Something went wrong." ✗

### 6.2 403 error mapping

Map `403` responses to action-specific messages. A 403 is a valid business outcome, not an exception.

| Endpoint group | User-facing message |
|---|---|
| `generate-sql`, `execute-sql`, `explain-sql` | "You don't have query access for this database." |
| `export-sql` | "You don't have export access for this database." |
| `PUT`, `DELETE`, `rotate-mcp-key`, `refresh-catalog` | "You need manage access for this database." |
| Grant management endpoints | "Only workspace admins can manage grants." |

**Error banner component:**

```tsx
function PermissionBanner({ action }: { action: 'query' | 'export' | 'manage' }) {
  const messages = {
    query:  "You don't have query access for this database.",
    export: "You don't have export access for this database.",
    manage: "You need manage access for this database.",
  };
  return (
    <Banner variant="error" icon="lock">
      {messages[action]}
    </Banner>
  );
}
```

Render the banner **inline** near the action that triggered it, not in a global toast. A toast disappears — the user needs to see it in context.

### 6.3 Workbench with no query access

When `selectedDatabase.access_level === 'discover'`, the editor should visually communicate the restriction:

- Query input field opacity reduced to 50%
- Run query button disabled
- Results area shows: "No query access for this database."
- Schema tab remains fully active (discover grant covers it)

---

## 7. Workspace switching behaviour

Workspace switching is a **full context reset** for all database-scoped state. Treat it like a partial re-mount of the data layer.

### Checklist on `POST /tenancy/switch-workspace/{id}` success

1. Store the new access token returned in the response.
2. Invalidate all workspace-scoped React Query keys (see §4.2).
3. Compare the currently selected database against the new `GET /databases` response.
4. If the selected database is not present in the new list, clear `selectedDatabase` in `WorkbenchView` and any other views that hold it.
5. Refetch: databases, workflows, catalog, reports, approvals, audit log.
6. Do not attempt to restore the previously selected database by name — names are not unique across workspaces.

### Why step 4 matters

`WorkbenchView` stores the active database in local state (or a URL param). After switching workspace, that reference becomes stale — the database ID from workspace A does not exist in workspace B. If not cleared, the user sees a Workbench that appears to have a database selected, but all queries return errors.

---

## 8. Grant management UI

Phase 1: this surface is only visible to `admin` users.

### 8.1 Where it lives

Add a grant management section to the database detail / admin surface. It should not be accessible from Workbench — keep it in the admin area to avoid cognitive overload for non-admin users.

### 8.2 Design principles

**Model grant level as a single select, not a stack of toggles.**

The grant levels are a strict hierarchy (`discover < query < export < manage`). Representing them as independent checkboxes implies they are orthogonal — they are not. Use a `<select>` or segmented control with the four options.

```tsx
<GrantLevelSelect
  value={grant.access_level}
  onChange={(level) => updateGrant(grant.user_id, level)}
  options={['discover', 'query', 'export', 'manage']}
/>
```

**Treat create and update as "set access level."**

There is no meaningful distinction between creating a grant and updating one from the admin's perspective. The UI should say "give access" or "set level", not "create grant" (jargon) or "add permission" (ambiguous).

**Delete means full revocation.** Use destructive confirmation copy:
> "Remove {name}'s access to {database}? They will no longer be able to see or query this database."

### 8.3 Grant list layout

```
┌─────────────────────────────────────────────────────────┐
│ analytics_prod · Grants                 [+ Add user]    │
├─────────────────────────────────────────────────────────┤
│ Arjun Kulkarni      analyst    [query  ▾]   [Remove]   │
│ Priya Sharma        analyst    [export ▾]   [Remove]   │
│ Dev Iyer            viewer     [discover▾]  [Remove]   │
└─────────────────────────────────────────────────────────┘
```

Each row renders: user display name, workspace role (for context), grant level selector, remove button. On select change, fire `PATCH /databases/{db_id}/grants/{user_id}` immediately. On remove, show confirmation then fire `DELETE`.

---

## 9. TypeScript types

Add these to `client/src/lib/types.ts`.

```ts
export type WorkspaceRole =
  | 'admin'
  | 'compliance_admin'
  | 'analyst'
  | 'viewer';

export type AccessLevel =
  | 'discover'
  | 'query'
  | 'export'
  | 'manage';

export interface DatabaseGrant {
  id: number;
  workspace_id: number;
  database_id: number;
  user_id: number;
  access_level: AccessLevel;
  granted_by: number;
  created_at: string;
  updated_at: string;
}

export interface Database {
  id: number;
  name: string;
  connection_status: 'ok' | 'degraded' | 'offline';
  access_level: AccessLevel;      // present for non-admin; for admin, synthesise 'manage'
  workspace_id: number;
}

export interface CreateGrantPayload {
  user_id: number;
  access_level: AccessLevel;
}

export interface UpdateGrantPayload {
  access_level: AccessLevel;
}
```

### API helpers

Add to `client/src/api/databases.ts` or a new `client/src/api/grants.ts`:

```ts
import type { DatabaseGrant, CreateGrantPayload, UpdateGrantPayload } from '@/lib/types';

export async function listGrants(databaseId: number): Promise<DatabaseGrant[]> {
  const res = await api.get(`/databases/${databaseId}/grants`);
  return res.data;
}

export async function createGrant(
  databaseId: number,
  payload: CreateGrantPayload
): Promise<DatabaseGrant> {
  const res = await api.post(`/databases/${databaseId}/grants`, payload);
  return res.data;
}

export async function updateGrant(
  databaseId: number,
  userId: number,
  payload: UpdateGrantPayload
): Promise<DatabaseGrant> {
  const res = await api.patch(`/databases/${databaseId}/grants/${userId}`, payload);
  return res.data;
}

export async function revokeGrant(
  databaseId: number,
  userId: number
): Promise<void> {
  await api.delete(`/databases/${databaseId}/grants/${userId}`);
}
```

---

## 10. Implementation checklist

Use this as a task list when implementing or reviewing the grant-aware frontend.

### Data layer

- [ ] `GET /databases` is the single source of truth for database visibility — no local filtering by role
- [ ] React Query keys are scoped to `[resource, workspaceId]`
- [ ] Workspace switch invalidates all workspace-scoped keys and drops stale selected database
- [ ] Grant API helpers exist in `api/databases.ts` or `api/grants.ts`
- [ ] TypeScript types for `AccessLevel`, `DatabaseGrant`, `Database` are in `lib/types.ts`

### UI components

- [ ] Sidebar database list renders grant pill per item
- [ ] Capability bar in Workbench reflects `selectedDatabase.access_level`
- [ ] Run query button disabled (not hidden) when grant < `query`
- [ ] Export button disabled (not hidden) when grant < `export`
- [ ] Schema / visualize-schema surface active for `discover` grant and above
- [ ] Database pickers in Workflow, Reports, Catalog use filtered backend list
- [ ] No hardcoded admin-style visibility assumptions in any selector

### Empty states

- [ ] Empty `GET /databases` shows permission-aware copy, not an error or spinner
- [ ] Workbench with `discover`-only grant shows restricted state, schema tab still functional
- [ ] No database selected state is handled gracefully in all views

### Error handling

- [ ] `403` on `generate/execute/explain-sql` → inline "no query access" banner
- [ ] `403` on `export-sql` → inline "no export access" banner (not the same as query 403)
- [ ] `403` on connector admin actions → "need manage access" message
- [ ] All 403s are treated as valid business outcomes, not exceptions

### Grant management (admin only)

- [ ] Grant section visible on database admin surface for `admin` role
- [ ] Access level rendered as single select, not checkboxes
- [ ] Create and update both map to "set access level" UX
- [ ] Delete shows confirmation with destructive copy before firing `DELETE`
- [ ] Grant list shows user display name, workspace role, and current level

### Workspace switching

- [ ] New access token stored on switch
- [ ] All workspace-scoped queries invalidated
- [ ] Selected database cleared if not present in new workspace
- [ ] No attempt to restore prior database by name across workspaces

---

*This document was generated from `explainer.md` and the SpeakQL UI mockup. Update it whenever the backend grant model changes or new surfaces are added.*
