import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { catalogApi } from '@/api/catalog';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Panel } from '@/components/ui/Panel';
import { useSessionStore } from '@/store/session';

export function CatalogPage() {
  const queryClient = useQueryClient();
  const currentUser = useSessionStore((state) => state.currentUser);
  const workspaceId = currentUser?.workspace_id ?? null;
  const canEdit = currentUser?.role === 'admin' || currentUser?.role === 'compliance_admin';

  const [newTerm, setNewTerm] = useState({ term: '', definition: '', maps_to_table: '', maps_to_column: '' });
  const [newMetric, setNewMetric] = useState({ name: '', sql_expression: '', description: '' });

  const entriesQuery = useQuery({
    queryKey: ['catalog', workspaceId],
    enabled: Boolean(workspaceId),
    queryFn: async () => (await catalogApi.entries()).data,
  });
  const glossaryQuery = useQuery({
    queryKey: ['glossary', workspaceId],
    enabled: Boolean(workspaceId),
    queryFn: async () => (await catalogApi.glossary()).data,
  });
  const metricsQuery = useQuery({
    queryKey: ['metrics', workspaceId],
    enabled: Boolean(workspaceId),
    queryFn: async () => (await catalogApi.metrics()).data,
  });

  const createTerm = useMutation({
    mutationFn: async () => catalogApi.createGlossary(newTerm),
    onSuccess: async () => {
      setNewTerm({ term: '', definition: '', maps_to_table: '', maps_to_column: '' });
      await queryClient.invalidateQueries({ queryKey: ['glossary'] });
      toast.success('Business term added.');
    },
    onError: () => toast.error('Only compliance admins can create glossary terms.'),
  });

  const createMetric = useMutation({
    mutationFn: async () => catalogApi.createMetric(newMetric),
    onSuccess: async () => {
      setNewMetric({ name: '', sql_expression: '', description: '' });
      await queryClient.invalidateQueries({ queryKey: ['metrics'] });
      toast.success('Metric definition added.');
    },
    onError: () => toast.error('Only compliance admins can create metrics.'),
  });

  return (
    <div className="layout-two">
      <div className="stack">
        <Panel title="Published tables" subtitle="This semantic layer guides prompt-to-SQL translation and catalog trust.">
          {entriesQuery.data?.length ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Table</th>
                    <th>Description</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {entriesQuery.data.map((entry) => (
                    <tr key={entry.id}>
                      <td>{entry.table_name}</td>
                      <td>{entry.description ?? 'No description yet.'}</td>
                      <td>{entry.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState title="No published catalog entries." copy="Publish connector tables to feed the semantic layer." />
          )}
        </Panel>

        <Panel title="Business glossary" subtitle="Map business language to table and column intent.">
          {glossaryQuery.data?.length ? (
            <div className="stack">
              {glossaryQuery.data.map((term) => (
                <div className="metric-card" key={term.id}>
                  <strong>{term.term}</strong>
                  <p className="muted">{term.definition}</p>
                  <div className="split-inline muted">
                    <span>{term.maps_to_table ?? 'No table map'}</span>
                    <span>{term.maps_to_column ?? 'No column map'}</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No glossary entries." copy="Add governed business language for the AI layer to reference." />
          )}
        </Panel>
      </div>

      <div className="stack">
        <Panel title="Certified metrics" subtitle="Metrics create stable KPI semantics across workbench and reports.">
          {metricsQuery.data?.length ? (
            <div className="stack">
              {metricsQuery.data.map((metric) => (
                <div className="metric-card" key={metric.id}>
                  <strong>{metric.name}</strong>
                  <p className="muted">{metric.description ?? 'No description provided.'}</p>
                  <div className="code-box"><pre>{metric.sql_expression}</pre></div>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState title="No metrics yet." copy="Create certified metric expressions to keep KPI logic reusable." />
          )}
        </Panel>

        <Panel title="Add glossary term" subtitle="Only compliance-oriented roles should mutate semantic knowledge.">
          <form className="form-grid" onSubmit={(event) => { event.preventDefault(); createTerm.mutate(); }}>
            <input className="input" placeholder="Term" value={newTerm.term} onChange={(event) => setNewTerm((state) => ({ ...state, term: event.target.value }))} />
            <textarea className="textarea" placeholder="Definition" value={newTerm.definition} onChange={(event) => setNewTerm((state) => ({ ...state, definition: event.target.value }))} />
            <div className="mini-grid">
              <input className="input" placeholder="Maps to table" value={newTerm.maps_to_table} onChange={(event) => setNewTerm((state) => ({ ...state, maps_to_table: event.target.value }))} />
              <input className="input" placeholder="Maps to column" value={newTerm.maps_to_column} onChange={(event) => setNewTerm((state) => ({ ...state, maps_to_column: event.target.value }))} />
            </div>
            <Button disabled={!canEdit}>Add term</Button>
          </form>
        </Panel>

        <Panel title="Add metric" subtitle="Define the source-of-truth SQL expression behind a KPI.">
          <form className="form-grid" onSubmit={(event) => { event.preventDefault(); createMetric.mutate(); }}>
            <input className="input" placeholder="Metric name" value={newMetric.name} onChange={(event) => setNewMetric((state) => ({ ...state, name: event.target.value }))} />
            <textarea className="textarea" placeholder="SQL expression" value={newMetric.sql_expression} onChange={(event) => setNewMetric((state) => ({ ...state, sql_expression: event.target.value }))} />
            <textarea className="textarea" placeholder="Description" value={newMetric.description} onChange={(event) => setNewMetric((state) => ({ ...state, description: event.target.value }))} />
            <Button disabled={!canEdit}>Add metric</Button>
          </form>
        </Panel>
      </div>
    </div>
  );
}
