import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { workflowApi } from '@/api/workflow';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Panel } from '@/components/ui/Panel';
import { formatDate, prettyJson } from '@/lib/format';
import { useSessionStore } from '@/store/session';

export function WorkflowPage() {
  const queryClient = useQueryClient();
  const currentUser = useSessionStore((state) => state.currentUser);
  const activeDatabaseId = useSessionStore((state) => state.activeDatabaseId);
  const workspaceId = currentUser?.workspace_id ?? null;

  const [draft, setDraft] = useState({
    name: 'New governed query',
    sql: 'SELECT id, event_type, created_at FROM auditevent ORDER BY created_at DESC LIMIT 25;',
    prompt: 'Show recent audit events.',
    description: 'Starter draft for governed replay.',
    tags: 'audit,starter',
  });
  const [replayOutput, setReplayOutput] = useState('');

  const queriesQuery = useQuery({
    queryKey: ['workflows', workspaceId],
    enabled: Boolean(workspaceId),
    queryFn: async () => (await workflowApi.list()).data,
  });

  const createMutation = useMutation({
    mutationFn: async () => workflowApi.create(draft),
    onSuccess: async () => {
      toast.success('Saved query created.');
      await queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
    onError: () => toast.error('Could not save the query draft.'),
  });

  const submitMutation = useMutation({
    mutationFn: async (queryId: number) => workflowApi.submit(queryId),
    onSuccess: async () => {
      toast.success('Query submitted for review.');
      await queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });

  const replayMutation = useMutation({
    mutationFn: async (queryId: number) => (await workflowApi.replay(queryId, activeDatabaseId!)).data,
    onSuccess: (data) => {
      setReplayOutput(prettyJson(data));
      toast.success('Replay completed through governance.');
    },
    onError: () => toast.error('Replay failed. Check connector access and workflow state.'),
  });

  return (
    <div className="layout-two">
      <div className="stack">
        <Panel title="Saved query library" subtitle="These assets survive beyond a single workbench session and replay through governance.">
          {queriesQuery.data?.length ? (
            <div className="stack">
              {queriesQuery.data.map((query) => (
                <div key={query.id} className="metric-card">
                  <div className="panel-header" style={{ marginBottom: '0.5rem' }}>
                    <div>
                      <strong>{query.name}</strong>
                      <p className="panel-subtitle">{query.description ?? 'No description provided.'}</p>
                    </div>
                    <span className="pill pill-neutral">{query.status}</span>
                  </div>
                  <div className="code-box"><pre>{query.sql}</pre></div>
                  <div className="split-inline muted" style={{ marginTop: '0.6rem' }}>
                    <span>{query.visibility}</span>
                    <span>{formatDate(query.updated_at)}</span>
                  </div>
                  <div className="toolbar" style={{ marginTop: '0.8rem' }}>
                    <Button tone="secondary" onClick={() => submitMutation.mutate(query.id)}>
                      Submit for review
                    </Button>
                    <Button onClick={() => replayMutation.mutate(query.id)} disabled={!activeDatabaseId}>
                      Replay on active database
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No saved queries." copy="Capture useful SQL here so it can move into reports and governed replay." />
          )}
        </Panel>
      </div>

      <div className="stack">
        <Panel title="Create draft" subtitle="Store a query with prompt context, tags, and review-ready metadata.">
          <form className="form-grid" onSubmit={(event) => { event.preventDefault(); createMutation.mutate(); }}>
            <input className="input" value={draft.name} onChange={(event) => setDraft((state) => ({ ...state, name: event.target.value }))} />
            <textarea className="textarea" value={draft.prompt} onChange={(event) => setDraft((state) => ({ ...state, prompt: event.target.value }))} />
            <textarea className="textarea" value={draft.sql} onChange={(event) => setDraft((state) => ({ ...state, sql: event.target.value }))} />
            <textarea className="textarea" value={draft.description} onChange={(event) => setDraft((state) => ({ ...state, description: event.target.value }))} />
            <input className="input" value={draft.tags} onChange={(event) => setDraft((state) => ({ ...state, tags: event.target.value }))} />
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Saving...' : 'Save query'}
            </Button>
          </form>
        </Panel>

        <Panel title="Replay output" subtitle="Replay responses surface the same explainability and approval behavior as direct execution.">
          <div className="code-box"><pre>{replayOutput || 'Replay a saved query to inspect the governed response payload.'}</pre></div>
        </Panel>
      </div>
    </div>
  );
}
