import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { reportsApi } from '@/api/reports';
import { workflowApi } from '@/api/workflow';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Panel } from '@/components/ui/Panel';
import { formatDate } from '@/lib/format';
import { useSessionStore } from '@/store/session';

export function ReportsPage() {
  const queryClient = useQueryClient();
  const currentUser = useSessionStore((state) => state.currentUser);
  const activeDatabaseId = useSessionStore((state) => state.activeDatabaseId);
  const workspaceId = currentUser?.workspace_id ?? null;

  const [payload, setPayload] = useState({
    name: 'Daily audit digest',
    saved_query_id: 0,
    database_id: activeDatabaseId ?? 0,
    schedule_cron: '0 9 * * *',
    delivery_config: '{"channel":"email"}',
    is_enabled: true,
  });

  const reportsQuery = useQuery({
    queryKey: ['reports', workspaceId],
    enabled: Boolean(workspaceId),
    queryFn: async () => (await reportsApi.list()).data,
  });

  const queriesQuery = useQuery({
    queryKey: ['workflows', workspaceId],
    enabled: Boolean(workspaceId),
    queryFn: async () => (await workflowApi.list()).data,
  });

  const createReport = useMutation({
    mutationFn: async () =>
      reportsApi.create({
        name: payload.name,
        saved_query_id: Number(payload.saved_query_id),
        database_id: Number(payload.database_id),
        schedule_cron: payload.schedule_cron,
        delivery_config: JSON.parse(payload.delivery_config),
        is_enabled: payload.is_enabled,
      }),
    onSuccess: async () => {
      toast.success('Report created.');
      await queryClient.invalidateQueries({ queryKey: ['reports'] });
    },
    onError: () => toast.error('Report creation failed.'),
  });

  const runReport = useMutation({
    mutationFn: async (reportId: number) => reportsApi.run(reportId, activeDatabaseId!),
    onSuccess: () => toast.success('Report run triggered.'),
    onError: () => toast.error('Report run failed.'),
  });

  return (
    <div className="layout-two">
      <div className="stack">
        <Panel title="Scheduled reports" subtitle="Reports stay tied to saved queries and granted connectors.">
          {reportsQuery.data?.length ? (
            <div className="stack">
              {reportsQuery.data.map((report) => (
                <div key={report.id} className="metric-card">
                  <strong>{report.name}</strong>
                  <p className="muted">Connector #{report.database_id} · Query #{report.saved_query_id}</p>
                  <div className="split-inline muted">
                    <span>{report.schedule_cron}</span>
                    <span>{report.is_enabled ? 'enabled' : 'disabled'}</span>
                    <span>{formatDate(report.last_ran_at)}</span>
                  </div>
                  <div className="toolbar" style={{ marginTop: '0.75rem' }}>
                    <Button tone="secondary" onClick={() => runReport.mutate(report.id)} disabled={!activeDatabaseId}>
                      Run now
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No reports configured." copy="Promote a saved query into a scheduled report to automate delivery." />
          )}
        </Panel>
      </div>

      <div className="stack">
        <Panel title="Create report" subtitle="Use a saved query and the active connector to define a delivery schedule.">
          <form className="form-grid" onSubmit={(event) => { event.preventDefault(); createReport.mutate(); }}>
            <input className="input" value={payload.name} onChange={(event) => setPayload((state) => ({ ...state, name: event.target.value }))} />
            <select className="select" value={payload.saved_query_id} onChange={(event) => setPayload((state) => ({ ...state, saved_query_id: Number(event.target.value) }))}>
              <option value={0}>Select saved query</option>
              {queriesQuery.data?.map((query) => (
                <option key={query.id} value={query.id}>{query.name}</option>
              ))}
            </select>
            <input className="input" value={payload.database_id || ''} onChange={(event) => setPayload((state) => ({ ...state, database_id: Number(event.target.value) }))} placeholder="Database ID" />
            <input className="input" value={payload.schedule_cron} onChange={(event) => setPayload((state) => ({ ...state, schedule_cron: event.target.value }))} />
            <textarea className="textarea" value={payload.delivery_config} onChange={(event) => setPayload((state) => ({ ...state, delivery_config: event.target.value }))} />
            <Button type="submit" disabled={createReport.isPending}>Create report</Button>
          </form>
        </Panel>
      </div>
    </div>
  );
}
