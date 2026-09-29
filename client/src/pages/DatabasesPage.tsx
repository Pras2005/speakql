import { useMemo, useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { KeyRound, RefreshCcw, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

import { databasesApi } from '@/api/databases';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Panel } from '@/components/ui/Panel';
import { PermissionBanner } from '@/components/ui/PermissionBanner';
import { formatDate } from '@/lib/format';
import { grantTone } from '@/lib/grants';
import type { AccessLevel } from '@/lib/types';
import { useSessionStore } from '@/store/session';

const accessLevels: AccessLevel[] = ['discover', 'query', 'export', 'manage'];

export function DatabasesPage() {
  const queryClient = useQueryClient();
  const currentUser = useSessionStore((state) => state.currentUser);
  const activeDatabaseId = useSessionStore((state) => state.activeDatabaseId);
  const workspaceId = currentUser?.workspace_id ?? null;

  const [newConnector, setNewConnector] = useState({
    db_name: '',
    host: '',
    port: 5432,
    db_user: '',
    db_password: '',
  });
  const [grantUserId, setGrantUserId] = useState('');
  const [grantLevel, setGrantLevel] = useState<AccessLevel>('query');

  const databasesQuery = useQuery({
    queryKey: ['databases', workspaceId],
    enabled: Boolean(workspaceId),
    queryFn: async () => (await databasesApi.list()).data,
  });

  const activeDatabase = useMemo(
    () => (databasesQuery.data ?? []).find((database) => database.id === activeDatabaseId) ?? null,
    [activeDatabaseId, databasesQuery.data],
  );

  const grantsQuery = useQuery({
    queryKey: ['grants', workspaceId, activeDatabaseId],
    enabled: Boolean(activeDatabaseId && currentUser?.role === 'admin'),
    queryFn: async () => (await databasesApi.listGrants(activeDatabaseId!)).data,
  });

  const invalidate = async () => {
    await queryClient.invalidateQueries({ queryKey: ['databases'] });
    await queryClient.invalidateQueries({ queryKey: ['grants'] });
  };

  const createConnector = useMutation({
    mutationFn: async () => databasesApi.create(newConnector),
    onSuccess: async () => {
      toast.success('Connector created. Creator seeded with manage grant.');
      setNewConnector({ db_name: '', host: '', port: 5432, db_user: '', db_password: '' });
      await invalidate();
    },
    onError: () => toast.error('Connector creation failed.'),
  });

  const rotateKey = useMutation({
    mutationFn: async (databaseId: number) => databasesApi.rotateKey(databaseId),
    onSuccess: () => toast.success('MCP key rotated.'),
    onError: () => toast.error('You need manage access for this database.'),
  });

  const refreshCatalog = useMutation({
    mutationFn: async (databaseId: number) => databasesApi.refreshCatalog(databaseId),
    onSuccess: () => toast.success('Catalog refresh triggered.'),
    onError: () => toast.error('You need manage access for this database.'),
  });

  const removeConnector = useMutation({
    mutationFn: async (databaseId: number) => databasesApi.remove(databaseId),
    onSuccess: async () => {
      toast.success('Connector removed.');
      await invalidate();
    },
    onError: () => toast.error('You need manage access for this database.'),
  });

  const createGrant = useMutation({
    mutationFn: async () => databasesApi.createGrant(activeDatabaseId!, {
      user_id: Number(grantUserId),
      access_level: grantLevel,
    }),
    onSuccess: async () => {
      toast.success('Grant level set.');
      setGrantUserId('');
      await invalidate();
    },
    onError: () => toast.error('Only workspace admins can manage grants.'),
  });

  const updateGrant = useMutation({
    mutationFn: async (payload: { userId: number; accessLevel: AccessLevel }) =>
      databasesApi.updateGrant(activeDatabaseId!, payload.userId, { access_level: payload.accessLevel }),
    onSuccess: async () => {
      toast.success('Grant updated.');
      await invalidate();
    },
    onError: () => toast.error('Only workspace admins can manage grants.'),
  });

  const deleteGrant = useMutation({
    mutationFn: async (userId: number) => databasesApi.deleteGrant(activeDatabaseId!, userId),
    onSuccess: async () => {
      toast.success('Access revoked.');
      await invalidate();
    },
    onError: () => toast.error('Only workspace admins can manage grants.'),
  });

  return (
    <div className="layout-two">
      <div className="stack">
        <Panel
          title="Visible connectors"
          subtitle="This list is the backend-filtered source of truth for workspace connector visibility."
        >
          {(databasesQuery.data ?? []).length ? (
            <div className="stack">
              {databasesQuery.data?.map((database) => (
                <div key={database.id} className="metric-card">
                  <div className="panel-header" style={{ marginBottom: '0.5rem' }}>
                    <div>
                      <strong>{database.name ?? database.db_name}</strong>
                      <p className="panel-subtitle">
                        {database.host ?? 'managed connector'} · created {formatDate(database.created_at)}
                      </p>
                    </div>
                    <span className={`pill ${grantTone(currentUser?.role === 'admin' ? 'manage' : database.access_level ?? null)}`}>
                      {currentUser?.role === 'admin' ? 'manage' : database.access_level ?? 'restricted'}
                    </span>
                  </div>
                  <div className="toolbar">
                    <Button tone="secondary" onClick={() => rotateKey.mutate(database.id)}>
                      <KeyRound size={14} style={{ marginRight: 8 }} />
                      Rotate key
                    </Button>
                    <Button tone="secondary" onClick={() => refreshCatalog.mutate(database.id)}>
                      <RefreshCcw size={14} style={{ marginRight: 8 }} />
                      Refresh catalog
                    </Button>
                    <Button tone="danger" onClick={() => removeConnector.mutate(database.id)}>
                      <Trash2 size={14} style={{ marginRight: 8 }} />
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState
              title="No databases available in this workspace."
              copy="You may not have access to any databases here yet. Contact your workspace admin to request access."
            />
          )}
        </Panel>

        <Panel title="Add connector" subtitle="New connectors automatically grant the creator manage access.">
          {currentUser?.role !== 'admin' ? <PermissionBanner action="manage" /> : null}
          <form
            className="form-grid"
            onSubmit={(event) => {
              event.preventDefault();
              createConnector.mutate();
            }}
          >
            <div className="mini-grid">
              <div className="field">
                <label>Database name</label>
                <input className="input" value={newConnector.db_name} onChange={(event) => setNewConnector((state) => ({ ...state, db_name: event.target.value }))} />
              </div>
              <div className="field">
                <label>Host</label>
                <input className="input" value={newConnector.host} onChange={(event) => setNewConnector((state) => ({ ...state, host: event.target.value }))} />
              </div>
            </div>
            <div className="mini-grid">
              <div className="field">
                <label>Port</label>
                <input className="input" type="number" value={newConnector.port} onChange={(event) => setNewConnector((state) => ({ ...state, port: Number(event.target.value) }))} />
              </div>
              <div className="field">
                <label>DB user</label>
                <input className="input" value={newConnector.db_user} onChange={(event) => setNewConnector((state) => ({ ...state, db_user: event.target.value }))} />
              </div>
            </div>
            <div className="field">
              <label>Password</label>
              <input className="input" type="password" value={newConnector.db_password} onChange={(event) => setNewConnector((state) => ({ ...state, db_password: event.target.value }))} />
            </div>
            <Button type="submit" disabled={createConnector.isPending || currentUser?.role !== 'admin'}>
              {createConnector.isPending ? 'Creating...' : 'Create connector'}
            </Button>
          </form>
        </Panel>
      </div>

      <div className="stack">
        <Panel title="Grant control" subtitle="Create and update per-database access levels as a single hierarchical value.">
          {currentUser?.role !== 'admin' ? (
            <PermissionBanner action="manage" />
          ) : !activeDatabase ? (
            <EmptyState title="No connector selected." copy="Pick a connector from the sidebar to inspect or edit its grants." />
          ) : (
            <>
              <div className="form-grid" style={{ marginBottom: '1rem' }}>
                <div className="mini-grid">
                  <div className="field">
                    <label>User ID</label>
                    <input className="input" value={grantUserId} onChange={(event) => setGrantUserId(event.target.value)} placeholder="42" />
                  </div>
                  <div className="field">
                    <label>Access level</label>
                    <select className="select" value={grantLevel} onChange={(event) => setGrantLevel(event.target.value as AccessLevel)}>
                      {accessLevels.map((level) => (
                        <option key={level} value={level}>{level}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <Button onClick={() => createGrant.mutate()} disabled={!grantUserId}>
                  Set access level
                </Button>
              </div>

              {grantsQuery.data?.length ? (
                <div className="table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>User</th>
                        <th>Grant</th>
                        <th>Granted by</th>
                        <th>Updated</th>
                        <th />
                      </tr>
                    </thead>
                    <tbody>
                      {grantsQuery.data.map((grant) => (
                        <tr key={grant.id}>
                          <td>User #{grant.user_id}</td>
                          <td>
                            <select
                              className="select"
                              value={grant.access_level}
                              onChange={(event) => updateGrant.mutate({ userId: grant.user_id, accessLevel: event.target.value as AccessLevel })}
                            >
                              {accessLevels.map((level) => (
                                <option key={level} value={level}>{level}</option>
                              ))}
                            </select>
                          </td>
                          <td>{grant.granted_by}</td>
                          <td>{formatDate(grant.updated_at)}</td>
                          <td>
                            <Button tone="ghost" onClick={() => deleteGrant.mutate(grant.user_id)}>Remove</Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState title="No explicit grants." copy="Add a user and set an access level for this connector." />
              )}
            </>
          )}
        </Panel>
      </div>
    </div>
  );
}
