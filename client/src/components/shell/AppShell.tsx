import { startTransition, useEffect, useMemo } from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import {
  Activity,
  Archive,
  BookOpenText,
  LogOut,
  Radar,
  ShieldCheck,
  TableProperties,
  WandSparkles,
} from 'lucide-react';

import { databasesApi } from '@/api/databases';
import { tenancyApi } from '@/api/tenancy';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { EmptyState } from '@/components/ui/EmptyState';
import { clearToken } from '@/lib/auth';
import { formatDate, statusClass } from '@/lib/format';
import { getEffectiveAccessLevel, grantTone } from '@/lib/grants';
import { useSessionStore } from '@/store/session';

const navItems = [
  { to: '/workbench', label: 'Workbench', icon: WandSparkles },
  { to: '/databases', label: 'Databases', icon: TableProperties },
  { to: '/catalog', label: 'Catalog', icon: BookOpenText },
  { to: '/workflow', label: 'Workflow', icon: Archive },
  { to: '/reports', label: 'Reports', icon: Activity },
  { to: '/governance', label: 'Governance', icon: ShieldCheck },
];

const pageTitles: Record<string, { title: string; subtitle: string }> = {
  '/workbench': {
    title: 'Governed Workbench',
    subtitle: 'Generate, inspect, execute, and export SQL with visible grant boundaries and explainability.',
  },
  '/databases': {
    title: 'Connector Control',
    subtitle: 'Manage connectors, access grants, health posture, and workspace-scoped visibility.',
  },
  '/catalog': {
    title: 'Semantic Catalog',
    subtitle: 'Shape the glossary, metrics, and published table context that steers AI output.',
  },
  '/workflow': {
    title: 'Reusable Queries',
    subtitle: 'Capture governed SQL, promote it through review, and replay it against granted databases.',
  },
  '/reports': {
    title: 'Scheduled Delivery',
    subtitle: 'Bind saved queries to connectors and keep reporting inside the same governed path.',
  },
  '/governance': {
    title: 'Trust Surface',
    subtitle: 'Review policies, sensitivity rules, approvals, audit integrity, and connector health.',
  },
};

export function AppShell({ children }: { children: React.ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const currentUser = useSessionStore((state) => state.currentUser);
  const memberships = useSessionStore((state) => state.memberships);
  const activeDatabaseId = useSessionStore((state) => state.activeDatabaseId);
  const setSessionToken = useSessionStore((state) => state.setSessionToken);
  const setActiveDatabaseId = useSessionStore((state) => state.setActiveDatabaseId);
  const resetSession = useSessionStore((state) => state.resetSession);

  const workspaceId = currentUser?.workspace_id ?? null;

  const databasesQuery = useQuery({
    queryKey: ['databases', workspaceId],
    enabled: Boolean(workspaceId),
    queryFn: async () => (await databasesApi.list()).data,
  });

  const databases = useMemo(() => databasesQuery.data ?? [], [databasesQuery.data]);
  const activeDatabase = databases.find((database) => database.id === activeDatabaseId) ?? null;

  useEffect(() => {
    if (!databases.length) {
      setActiveDatabaseId(null);
      return;
    }

    const stillExists = databases.some((database) => database.id === activeDatabaseId);
    if (!activeDatabaseId || !stillExists) {
      setActiveDatabaseId(databases[0].id);
    }
  }, [activeDatabaseId, databases, setActiveDatabaseId]);

  const workspaceMutation = useMutation({
    mutationFn: async (nextWorkspaceId: number) => (await tenancyApi.switchWorkspace(nextWorkspaceId)).data,
    onSuccess: async (data) => {
      setSessionToken(data.access_token);
      startTransition(() => {
        setActiveDatabaseId(null);
      });
      await queryClient.invalidateQueries();
      toast.success('Workspace context switched.');
    },
    onError: () => {
      toast.error('Workspace switch failed.');
    },
  });

  const logout = () => {
    clearToken();
    resetSession();
    queryClient.clear();
    navigate('/login');
  };

  const currentPage = pageTitles[location.pathname] ?? pageTitles['/workbench'];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div>
            <div className="eyebrow">SpeakQL Enterprise</div>
            <strong>Grant-aware command center</strong>
          </div>
          <div className="brand-mark">SQ</div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(({ to, label, icon: Icon }) => (
            <NavLink key={to} to={to} className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.7rem' }}>
                <Icon size={16} />
                {label}
              </span>
              {to === '/workbench' && activeDatabase ? (
                <Badge className={grantTone(getEffectiveAccessLevel(activeDatabase, currentUser))}>
                  {getEffectiveAccessLevel(activeDatabase, currentUser)}
                </Badge>
              ) : null}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-section">
          <div className="eyebrow">Visible databases</div>
          <div className="database-list">
            {databasesQuery.isLoading ? (
              <div className="empty-state">Loading database visibility for this workspace...</div>
            ) : databases.length ? (
              databases.map((database) => {
                const level = getEffectiveAccessLevel(database, currentUser);
                return (
                  <button
                    key={database.id}
                    className={`database-item ${database.id === activeDatabaseId ? 'active' : ''}`}
                    onClick={() => setActiveDatabaseId(database.id)}
                    type="button"
                  >
                    <header>
                      <strong>{database.name ?? database.db_name}</strong>
                      <span className={`status-dot ${statusClass(database.connection_status)}`} />
                    </header>
                    <div className="database-meta">
                      <span>{database.host ?? 'managed connector'}</span>
                      <Badge className={grantTone(level)}>{level ?? 'restricted'}</Badge>
                    </div>
                  </button>
                );
              })
            ) : (
              <EmptyState
                title="No databases available in this workspace."
                copy="You may not have access to any databases here yet. Contact your workspace admin to request access."
              />
            )}
          </div>
        </div>

        <div className="sidebar-section panel" style={{ padding: '1rem' }}>
          <div className="eyebrow">Active actor</div>
          <strong>{currentUser?.username ?? 'Unknown user'}</strong>
          <p className="muted">
            {currentUser?.workspace_name ?? `Workspace ${currentUser?.workspace_id ?? '—'}`}
          </p>
          <p className="muted">
            Role: <strong>{currentUser?.role ?? 'unresolved'}</strong>
          </p>
          {activeDatabase ? (
            <p className="muted">Selected database updated {formatDate(activeDatabase.created_at)}</p>
          ) : null}
          <Button tone="ghost" onClick={logout} style={{ marginTop: '0.75rem' }}>
            <LogOut size={14} style={{ marginRight: 8 }} />
            Log out
          </Button>
        </div>
      </aside>

      <main className="main">
        <div className="topbar">
          <div>
            <div className="eyebrow">{currentUser?.org_name ?? 'Governed workspace'}</div>
            <h1 className="page-title">{currentPage.title}</h1>
            <p className="page-subtitle">{currentPage.subtitle}</p>
          </div>

          <div className="topbar-right">
            <select
              className="select workspace-switcher"
              value={currentUser?.workspace_id ?? ''}
              onChange={(event) => {
                const nextWorkspaceId = Number(event.target.value);
                if (nextWorkspaceId && nextWorkspaceId !== currentUser?.workspace_id) {
                  workspaceMutation.mutate(nextWorkspaceId);
                }
              }}
              disabled={workspaceMutation.isPending}
            >
              {memberships.map((membership) => (
                <option key={membership.id} value={membership.workspace_id}>
                  Workspace {membership.workspace_id} · {membership.role}
                </option>
              ))}
            </select>
            <Badge className="pill-neutral">
              <Radar size={14} />
              {currentUser?.role ?? 'role unknown'}
            </Badge>
          </div>
        </div>

        {children}
      </main>
    </div>
  );
}
