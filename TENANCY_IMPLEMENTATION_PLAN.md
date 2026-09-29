# SpeakQL Enterprise: Tenancy & Access Control Implementation Plan

## Overview

This document defines the corrected implementation plan for enterprise tenancy and access control in SpeakQL.

The current system has:

- `Organization`
- `Workspace`
- `Membership`
- coarse workspace roles
- workspace-wide database visibility

That is not enough for enterprise collaboration. We need:

- ownership semantics
- workspace-scoped member management
- per-database grants
- a clean separation between org-level roles and workspace-level roles

This revised plan is intentionally aligned with the current codebase. It does **not** introduce disruptive identifier changes and does **not** push volatile access state into JWTs.

## Guiding Principles

1. Keep the migration additive where possible.
2. Do not replace integer primary keys during this rollout.
3. Separate org-level administration from workspace-level administration.
4. Treat database access as a resource grant, not as a side effect of membership.
5. Resolve database access at request time on the server.

---

## Current Problems

The current architecture has the following gaps:

- no `owner_user_id` on `Organization`
- no `owner_user_id` on `Workspace`
- no workspace member management API
- no org-level membership model
- no per-database access control
- `admin` is overloaded
- visibility and execution rights are workspace-wide instead of grant-based

This means the system cannot yet support common enterprise scenarios like:

- workspace admins granting one analyst query access to one database but not another
- compliance admins managing governance without owning infrastructure
- org administrators overseeing multiple workspaces

---

## Target Model

We will implement two separate authorization layers:

1. `Role-based authority`
2. `Resource-level grants`

### Role-based authority

This answers:

- who can manage members
- who can manage workspace settings
- who can manage governance
- who can administer databases

### Resource-level grants

This answers:

- which databases a user can see
- which databases a user can query
- which databases a user can export from
- which databases a user can manage

---

## Phase 1 — Ownership + Database Access Grants

**Goal:** Introduce ownership fields and per-database grants while preserving the current role model and current integer IDs.

This is the highest-value and lowest-risk phase.

### 1.1 Schema changes

#### Extend `Organization`

```python
class Organization(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    owner_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
```

#### Extend `Workspace`

```python
class Workspace(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    owner_user_id: Optional[int] = Field(default=None, foreign_key="user.id")
```

#### Add `DatabaseAccessGrant`

```python
class DatabaseAccessLevel(str, Enum):
    DISCOVER = "discover"
    QUERY = "query"
    EXPORT = "export"
    MANAGE = "manage"

class DatabaseAccessGrant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    database_id: int = Field(foreign_key="userdatabase.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    access_level: DatabaseAccessLevel
    granted_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

#### Recommended uniqueness constraint

Add a uniqueness constraint on:

- `(workspace_id, database_id, user_id)`

That prevents duplicate grants for the same user/database pair.

### 1.2 Backfill strategy

On migration:

- `organization.owner_user_id` = oldest current `admin` member in the org
- `workspace.owner_user_id` = oldest current `admin` member in the workspace
- for each current workspace database:
  - grant `manage` access to every current `admin` member
  - optionally grant `query` access to current `analyst` members if you want to preserve current analyst behavior immediately

The exact analyst backfill policy should be chosen explicitly:

- conservative: only admins get grants initially
- compatibility mode: analysts get `query`, admins get `manage`

For least disruption, compatibility mode is better.

### 1.3 New repository

Add `backend/repositories/database_grant_repository.py`

```python
class DatabaseGrantRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_grant(self, workspace_id: int, database_id: int, user_id: int) -> Optional[DatabaseAccessGrant]:
        ...

    async def list_grants_for_database(self, workspace_id: int, database_id: int) -> list[DatabaseAccessGrant]:
        ...

    async def list_database_ids_for_user(self, workspace_id: int, user_id: int) -> list[int]:
        ...

    async def upsert_grant(self, grant: DatabaseAccessGrant) -> DatabaseAccessGrant:
        ...

    async def revoke_grant(self, workspace_id: int, database_id: int, user_id: int) -> None:
        ...
```

### 1.4 New service

Add `backend/services/grant_service.py`

Responsibilities:

- grant access
- revoke access
- list grants
- validate that grant operations happen inside the active workspace
- audit grant changes

```python
class GrantService:
    async def grant_access(self, database_id: int, target_user_id: int, access_level: DatabaseAccessLevel) -> DatabaseAccessGrant:
        ...

    async def revoke_access(self, database_id: int, target_user_id: int) -> None:
        ...

    async def list_grants(self, database_id: int) -> list[DatabaseAccessGrant]:
        ...
```

### 1.5 Service updates

#### `DatabaseService.get_databases()`

Today it returns every database in the workspace. That must change.

New behavior:

- admins may still see all databases if you want explicit admin visibility
- otherwise return only databases where the caller has a grant

Recommended implementation:

```python
async def get_databases(self, user_id: int) -> list[UserDatabase]:
    context = get_request_context()
    granted_ids = await self.grant_repo.list_database_ids_for_user(context.workspace_id, context.user_id)
    return await self.db_repo.list_by_ids(context.workspace_id, granted_ids)
```

Add `list_by_ids()` to `DatabaseRepository`.

#### `GovernanceService.execute_governed_query()`

Before governance execution begins, verify the caller has at least:

- `query` or `export` or `manage`

Rules:

- `discover`: schema/metadata only
- `query`: query execution allowed
- `export`: query execution + export allowed
- `manage`: full database operations allowed

#### Agent routes

Apply grant checks to:

- `/agent/generate-sql`
- `/agent/execute-sql`
- `/agent/explain-sql`
- `/agent/export-sql`
- `/agent/visualize-schema`

Recommended behavior:

- `generate-sql`: requires `query` or above
- `execute-sql`: requires `query` or above
- `explain-sql`: requires `query` or above
- `export-sql`: requires `export` or `manage`
- `visualize-schema`: requires `discover` or above

#### Database management routes

Apply `manage` grant check in addition to admin role requirements for:

- update database
- delete database
- rotate MCP key
- refresh catalog

### 1.6 New API endpoints

Add grant endpoints:

```
GET    /databases/{database_id}/grants
POST   /databases/{database_id}/grants
PATCH  /databases/{database_id}/grants/{user_id}
DELETE /databases/{database_id}/grants/{user_id}
```

For Phase 1, keep these guarded by current admin authority:

- current `require_admin`

Later they will move to workspace-owner/workspace-admin guards.

### 1.7 Audit events

Add:

- `DATABASE_ACCESS_GRANTED`
- `DATABASE_ACCESS_REVOKED`
- `DATABASE_ACCESS_UPDATED`

---

## Phase 2 — Workspace Role Cleanup + Workspace Member Management

**Goal:** Cleanly split workspace roles and add the API surface for managing workspace members.

This phase should happen only after Phase 1 is stable.

### 2.1 Replace current workspace role enum

Update `MembershipRole` in `tenant_model.py` to workspace-only roles:

```python
class MembershipRole(str, Enum):
    VIEWER = "viewer"
    ANALYST = "analyst"
    COMPLIANCE_ADMIN = "compliance_admin"
    WORKSPACE_ADMIN = "workspace_admin"
    WORKSPACE_OWNER = "workspace_owner"
```

### 2.2 Migration strategy

Existing roles migrate as:

- `admin` -> `workspace_admin`
- one designated oldest `workspace_admin` per workspace -> `workspace_owner`
- `analyst` -> unchanged
- `compliance_admin` -> unchanged
- `viewer` -> unchanged

### 2.3 New auth guards

Replace current admin guard model with workspace-specific guards:

```python
require_workspace_owner
require_workspace_admin
require_compliance
require_analyst
require_member_read
```

Suggested semantics:

- `require_workspace_owner`
  - workspace owner only

- `require_workspace_admin`
  - workspace owner
  - workspace admin

- `require_compliance`
  - workspace owner
  - workspace admin
  - compliance admin

- `require_analyst`
  - workspace owner
  - workspace admin
  - compliance admin
  - analyst

- `require_member_read`
  - every workspace member including viewer

### 2.4 Why `require_member_read` is necessary

If viewers are supposed to access read-only product surfaces, there must be an explicit read guard.

Use `require_member_read` for:

- read-only catalog views if desired
- report listing if desired
- other member-readable surfaces

Do not rely on `require_analyst` for viewer access.

### 2.5 New workspace member management endpoints

Add to `tenant_routes.py` or a new workspace admin router:

```
GET    /workspaces/{workspace_id}/members
POST   /workspaces/{workspace_id}/members
PATCH  /workspaces/{workspace_id}/members/{user_id}
DELETE /workspaces/{workspace_id}/members/{user_id}
POST   /workspaces/{workspace_id}/transfer-ownership
PATCH  /workspaces/{workspace_id}/owner
```

Permissions:

- list members: workspace admin or owner
- add member: workspace admin or owner
- update role: workspace admin or owner
- remove member: workspace admin or owner
- transfer ownership: workspace owner only

Constraints:

- cannot remove workspace owner without transfer
- cannot demote workspace owner without transfer
- cannot assign multiple workspace owners unless explicitly allowed

### 2.6 Audit events

Add:

- `MEMBERSHIP_CREATED`
- `MEMBERSHIP_ROLE_CHANGED`
- `MEMBERSHIP_REMOVED`
- `WORKSPACE_OWNERSHIP_TRANSFERRED`

---

## Phase 3 — Org-Level Membership and Cross-Workspace Administration

**Goal:** Introduce a proper org-level role system instead of overloading workspace membership for org authority.

This must be a separate model, not additional values inside `MembershipRole`.

### 3.1 New `OrgMembership` model

Add a new model:

```python
class OrgMembershipRole(str, Enum):
    ORG_OWNER = "org_owner"
    ORG_ADMIN = "org_admin"
    ORG_AUDITOR = "org_auditor"

class OrgMembership(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    org_id: int = Field(foreign_key="organization.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    role: OrgMembershipRole
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### 3.2 Ownership rule

The first creator of an org becomes:

- `organization.owner_user_id`
- `OrgMembership(role=ORG_OWNER)`

These are related but not identical:

- `owner_user_id` is the canonical ownership field
- `OrgMembership` is the operational authorization record

### 3.3 Org-level endpoints

Add:

```
GET    /org/members
POST   /org/members
PATCH  /org/members/{user_id}
DELETE /org/members/{user_id}

GET    /org/workspaces
POST   /org/workspaces

POST   /org/transfer-ownership
GET    /org/audit
```

Permissions:

- org owner: everything
- org admin: member/workspace operations except ownership transfer
- org auditor: org-wide audit visibility only

### 3.4 Route behavior

Org roles should not replace workspace roles. They complement them.

Examples:

- org admin can create a workspace
- workspace admin manages that workspace day to day
- org auditor can inspect org-wide audit but not edit governance rules

### 3.5 Audit events

Add:

- `ORG_MEMBER_ADDED`
- `ORG_MEMBER_ROLE_CHANGED`
- `ORG_MEMBER_REMOVED`
- `ORG_WORKSPACE_CREATED`
- `ORG_OWNERSHIP_TRANSFERRED`

---

## Phase 4 — Groups and Team-Based Grants

**Goal:** Scale database access management beyond per-user grants.

This is a scale optimization, not a correctness prerequisite.

### 4.1 Add groups

```python
class UserGroup(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    name: str
    created_by: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class GroupMembership(SQLModel, table=True):
    group_id: int = Field(foreign_key="usergroup.id", primary_key=True)
    user_id: int = Field(foreign_key="user.id", primary_key=True)
```

### 4.2 Extend grants to support principals

At that point, evolve `DatabaseAccessGrant` from user-only to principal-based:

```python
class PrincipalType(str, Enum):
    USER = "user"
    GROUP = "group"

class DatabaseAccessGrant(SQLModel, table=True):
    ...
    principal_type: PrincipalType = PrincipalType.USER
    principal_id: int
```

Grant resolution then becomes:

- direct user grants
- group grants expanded via group membership

### 4.3 New endpoints

```
GET    /groups
POST   /groups
PATCH  /groups/{group_id}
DELETE /groups/{group_id}

GET    /groups/{group_id}/members
POST   /groups/{group_id}/members
DELETE /groups/{group_id}/members/{user_id}
```

---

## Access Check Flow After Implementation

Every sensitive action should pass these gates:

### 1. Workspace membership check

Is the user a member of the active workspace?

### 2. Role authority check

Does their workspace role permit this kind of action?

Examples:

- member-read
- analyst execution
- compliance governance
- workspace admin operations
- workspace owner transfer actions

### 3. Resource grant check

Does the user have the required grant on this database?

Grant rules:

- `discover` -> visible, schema inspection only
- `query` -> generate/execute/explain
- `export` -> query + export
- `manage` -> connection administration and full operational control

### 4. Governance check

Even if the grant allows the action, the existing governance pipeline still decides whether the query is:

- allowed
- denied
- approval-required
- masked
- size-capped
- timed out

This preserves the current execution architecture.

---

## JWT Guidance

Do **not** encode per-database access levels in JWTs.

Reason:

- grants are resource-specific
- grants can change independently of token issuance
- server-side checks are already the current architectural pattern

JWT should continue to carry:

- user identity
- active org/workspace context
- membership role

Resource grants should be resolved from the database at request time.

---

## What Not To Do

- Do not change primary keys from `int` to `uuid` in this rollout.
- Do not mix org roles into workspace role enums.
- Do not overload `admin` further before Phase 2.
- Do not store database access levels in JWTs.
- Do not skip the grant backfill migration.
- Do not promise viewer access to surfaces unless you add explicit viewer-readable guards.

---

## File Change Summary

| File | Change |
|---|---|
| `backend/models/tenant_model.py` | Add `owner_user_id`; later update `MembershipRole` to workspace-only roles |
| `backend/models/grant_model.py` | New file for `DatabaseAccessGrant`, `DatabaseAccessLevel` |
| `backend/models/org_membership_model.py` | New file in Phase 3 for `OrgMembership`, `OrgMembershipRole` |
| `backend/repositories/database_grant_repository.py` | New file |
| `backend/repositories/org_membership_repository.py` | New file in Phase 3 |
| `backend/services/grant_service.py` | New file |
| `backend/services/database_service.py` | Filter visible databases by grants |
| `backend/services/governance_service.py` | Enforce grants before execution/export |
| `backend/auth/auth_guards.py` | Replace coarse admin guard with role-specific workspace guards |
| `backend/routers/tenant_routes.py` | Add workspace member management endpoints |
| `backend/routers/grant_routes.py` | New file for grant CRUD |
| `backend/routers/org_routes.py` | New file in Phase 3 |
| `backend/models/audit_model.py` | Add new event types or ensure audit event string constants are supported |
| `alembic/versions/*` | Migration for owner fields, grant tables, role migration, org membership tables |

---

## Recommended Implementation Order

1. Add owner fields and `DatabaseAccessGrant`
2. Backfill grants and ownership
3. Update visible database filtering and grant enforcement
4. Add grant CRUD API
5. Split workspace roles and add member management
6. Add org-level memberships and org admin APIs
7. Add groups if scale requires them

---

## Final Position

The enterprise target architecture should be:

- ownership for `Organization` and `Workspace`
- workspace roles for operational authority
- org roles for cross-workspace authority
- database grants for resource access
- governance pipeline for execution control

That structure fits the current SpeakQL backend much better than the existing shallow role model, and this phased plan gets there without forcing a high-risk ID migration or mixing incompatible role concepts.
