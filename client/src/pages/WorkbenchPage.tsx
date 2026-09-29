import { useEffect, useMemo, useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { Download, Play, ScanSearch, WandSparkles } from 'lucide-react';
import { toast } from 'sonner';

import { agentApi } from '@/api/agent';
import { databasesApi } from '@/api/databases';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Panel } from '@/components/ui/Panel';
import { PermissionBanner } from '@/components/ui/PermissionBanner';
import { formatDate, prettyJson } from '@/lib/format';
import { canAccess, getEffectiveAccessLevel } from '@/lib/grants';
import { useSessionStore } from '@/store/session';

export function WorkbenchPage() {
  const currentUser = useSessionStore((state) => state.currentUser);
  const activeDatabaseId = useSessionStore((state) => state.activeDatabaseId);

  const [prompt, setPrompt] = useState('Show the five highest-risk audit events from the last 7 days.');
  const [sql, setSql] = useState('');
  const [result, setResult] = useState<Record<string, unknown>[] | null>(null);
  const [schemaPreview, setSchemaPreview] = useState<string>('');
  const [explainability, setExplainability] = useState<string>('');

  const workspaceId = currentUser?.workspace_id ?? null;
  const databasesQuery = useQuery({
    queryKey: ['databases', workspaceId],
    enabled: Boolean(workspaceId),
    queryFn: async () => (await databasesApi.list()).data,
  });

  const activeDatabase = (databasesQuery.data ?? []).find((item) => item.id === activeDatabaseId) ?? null;
  const accessLevel = getEffectiveAccessLevel(activeDatabase, currentUser);
  const canDiscover = canAccess(accessLevel, 'discover');
  const canQuery = canAccess(accessLevel, 'query');
  const canExport = canAccess(accessLevel, 'export');
  const canManage = canAccess(accessLevel, 'manage');

  const historyQuery = useQuery({
    queryKey: ['query-history', workspaceId, activeDatabaseId],
    enabled: Boolean(activeDatabaseId),
    queryFn: async () => (await databasesApi.history(activeDatabaseId!)).data,
  });

  const schemaQuery = useQuery({
    queryKey: ['schema', workspaceId, activeDatabaseId],
    enabled: Boolean(activeDatabaseId && canDiscover),
    queryFn: async () => (await agentApi.schema(activeDatabaseId!)).data,
  });

  useEffect(() => {
    if (!schemaQuery.data) {
      setSchemaPreview('');
      return;
    }
    setSchemaPreview(prettyJson(schemaQuery.data.tables));
  }, [schemaQuery.data]);

  const generateMutation = useMutation({
    mutationFn: async () => {
      return (
        await agentApi.generate({
          prompt,
          db_id: activeDatabaseId!,
          provider_type: 'gemini',
        })
      ).data;
    },
    onSuccess: (data) => {
      setSql(data.raw_sql);
      toast.success(data.message ?? 'SQL draft generated.');
    },
    onError: () => toast.error("You don't have query access for this database."),
  });

  const executeMutation = useMutation({
    mutationFn: async () => (await agentApi.execute({ raw_sql: sql, db_id: activeDatabaseId!, original_prompt: prompt })).data,
    onSuccess: (data) => {
      setResult(data.result ?? null);
      setExplainability(prettyJson(data.explainability));
      if (data.status === 'approval_required') {
        toast.message('This query moved into approval.');
      } else {
        toast.success('Query executed through the governed path.');
      }
    },
    onError: () => toast.error("You don't have query access for this database."),
  });

  const explainMutation = useMutation({
    mutationFn: async () => (await agentApi.explain({ raw_sql: sql, db_id: activeDatabaseId!, original_prompt: prompt })).data,
    onSuccess: (data) => {
      setResult(data.result ?? null);
      setExplainability(prettyJson(data.explainability));
      toast.success('Explain plan returned.');
    },
    onError: () => toast.error("You don't have query access for this database."),
  });

  const exportMutation = useMutation({
    mutationFn: async () => (await agentApi.exportCsv({ raw_sql: sql, db_id: activeDatabaseId!, original_prompt: prompt })).data,
    onSuccess: (blob) => {
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = `${activeDatabase?.name ?? 'export'}.csv`;
      anchor.click();
      window.URL.revokeObjectURL(url);
      toast.success('Export downloaded.');
    },
    onError: () => toast.error("You don't have export access for this database."),
  });

  const capabilityItems = useMemo(
    () => [
      { label: 'schema', active: canDiscover },
      { label: 'query', active: canQuery },
      { label: 'export', active: canExport },
      { label: 'manage', active: canManage },
    ],
    [canDiscover, canExport, canManage, canQuery],
  );

  return (
    <div className="content-grid">
      <Panel
        title="Capability bar"
        subtitle="This is derived from the selected database grant, not from workspace role alone."
      >
        <div className="capability-bar">
          {capabilityItems.map((item) => (
            <div key={item.label} className={`capability-chip ${item.active ? 'active' : ''}`}>
              <span className={`status-dot ${item.active ? 'status-ok' : 'status-unknown'}`} />
              {item.label}
            </div>
          ))}
        </div>
      </Panel>

      <div className="layout-two">
        <div className="stack">
          <Panel
            title="Intent to SQL"
            subtitle={activeDatabase ? `Targeting ${activeDatabase.name ?? activeDatabase.db_name}` : 'Select a database from the sidebar.'}
            actions={
              <div className="toolbar">
                <Button onClick={() => generateMutation.mutate()} disabled={!activeDatabaseId || !canQuery || generateMutation.isPending}>
                  <WandSparkles size={14} style={{ marginRight: 8 }} />
                  Generate
                </Button>
                <Button tone="secondary" onClick={() => executeMutation.mutate()} disabled={!activeDatabaseId || !canQuery || !sql}>
                  <Play size={14} style={{ marginRight: 8 }} />
                  Execute
                </Button>
                <Button tone="secondary" onClick={() => explainMutation.mutate()} disabled={!activeDatabaseId || !canQuery || !sql}>
                  <ScanSearch size={14} style={{ marginRight: 8 }} />
                  Explain
                </Button>
                <Button tone="secondary" onClick={() => exportMutation.mutate()} disabled={!activeDatabaseId || !canExport || !sql}>
                  <Download size={14} style={{ marginRight: 8 }} />
                  Export CSV
                </Button>
              </div>
            }
          >
            {!activeDatabase ? (
              <EmptyState
                title="No database selected."
                copy="Pick a visible database from the sidebar to activate the governed editor."
              />
            ) : null}
            {activeDatabase && !canQuery ? <PermissionBanner action="query" /> : null}
            {activeDatabase && canQuery && !canExport ? <PermissionBanner action="export" /> : null}
            <div className="stack" style={{ opacity: canQuery ? 1 : 0.55 }}>
              <div className="field">
                <label htmlFor="prompt">Prompt</label>
                <textarea id="prompt" className="textarea" value={prompt} onChange={(event) => setPrompt(event.target.value)} />
              </div>
              <div className="field">
                <label htmlFor="sql">SQL draft</label>
                <textarea id="sql" className="textarea" value={sql} onChange={(event) => setSql(event.target.value)} />
              </div>
            </div>
          </Panel>

          <Panel title="Query result" subtitle="The results panel preserves approval-required and explainability states.">
            {result?.length ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      {Object.keys(result[0]).map((key) => (
                        <th key={key}>{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.map((row, index) => (
                      <tr key={index}>
                        {Object.entries(row).map(([key, value]) => (
                          <td key={key}>{String(value)}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState
                title={canQuery ? 'No results yet.' : 'No query access for this database.'}
                copy={canQuery ? 'Run or explain SQL to populate this surface.' : 'Schema discovery may still be available if the grant level is discover.'}
              />
            )}
          </Panel>
        </div>

        <div className="stack">
          <Panel title="Explainability" subtitle="Policy outcome, risk metadata, and confidence stay visible in context.">
            <div className="code-box">
              <pre>{explainability || 'No explainability payload yet.'}</pre>
            </div>
          </Panel>

          <Panel title="Schema preview" subtitle="Discover grant keeps this panel alive even when query actions are disabled.">
            {canDiscover ? (
              <div className="code-box">
                <pre>{schemaQuery.isLoading ? 'Loading schema preview...' : schemaPreview || 'Schema is empty for this connector.'}</pre>
              </div>
            ) : (
              <PermissionBanner action="discover" />
            )}
          </Panel>

          <Panel title="Recent query history" subtitle="History remains workspace- and connector-scoped.">
            {historyQuery.isLoading ? (
              <div className="empty-state">Loading connector history...</div>
            ) : historyQuery.data?.length ? (
              <div className="stack">
                {historyQuery.data.slice(0, 5).map((item) => (
                  <div key={item.id} className="metric-card">
                    <strong>{item.status.toUpperCase()}</strong>
                    <p className="muted">{item.prompt ?? item.raw_sql ?? 'No text'}</p>
                    <div className="muted">{formatDate(item.timestamp)}</div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No query history." copy="Run queries on the active connector to populate this feed." />
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
