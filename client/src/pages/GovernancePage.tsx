import { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { healthApi } from '@/api/databases';
import { governanceApi } from '@/api/governance';
import { Button } from '@/components/ui/Button';
import { EmptyState } from '@/components/ui/EmptyState';
import { Panel } from '@/components/ui/Panel';
import { PermissionBanner } from '@/components/ui/PermissionBanner';
import { formatDate, prettyJson } from '@/lib/format';
import { useSessionStore } from '@/store/session';

export function GovernancePage() {
  const queryClient = useQueryClient();
  const currentUser = useSessionStore((state) => state.currentUser);
  const workspaceId = currentUser?.workspace_id ?? null;
  const canGovern = currentUser?.role === 'admin' || currentUser?.role === 'compliance_admin';

  const [policyForm, setPolicyForm] = useState({
    name: 'Production guardrail',
    description: 'Block direct secrets access and limit ad hoc blast radius.',
    priority: 0,
    rules: '{\n  "blocked_tables": ["secrets"],\n  "row_limit": 250\n}',
  });

  const [ruleForm, setRuleForm] = useState({
    table_name: 'customers',
    column_name: 'email',
    label: 'pii',
    masking_strategy: 'redact',
    priority: 10,
    restricted_roles: 'viewer',
  });

  const policiesQuery = useQuery({
    queryKey: ['policies', workspaceId],
    enabled: Boolean(workspaceId && canGovern),
    queryFn: async () => (await governanceApi.policies()).data,
  });
  const rulesQuery = useQuery({
    queryKey: ['sensitivity-rules', workspaceId],
    enabled: Boolean(workspaceId && canGovern),
    queryFn: async () => (await governanceApi.sensitivityRules()).data,
  });
  const approvalsQuery = useQuery({
    queryKey: ['approvals', workspaceId],
    enabled: Boolean(workspaceId && canGovern),
    queryFn: async () => (await governanceApi.pendingApprovals()).data,
  });
  const auditQuery = useQuery({
    queryKey: ['audit', workspaceId],
    enabled: Boolean(workspaceId && canGovern),
    queryFn: async () => (await governanceApi.auditLogs()).data,
  });
  const verificationQuery = useQuery({
    queryKey: ['audit-verification', workspaceId],
    enabled: Boolean(workspaceId && canGovern),
    queryFn: async () => (await governanceApi.verifyAudit()).data,
  });
  const healthQuery = useQuery({
    queryKey: ['connector-health', workspaceId],
    enabled: Boolean(workspaceId && canGovern),
    queryFn: async () => (await healthApi.list()).data,
  });

  const createPolicy = useMutation({
    mutationFn: async () =>
      governanceApi.createPolicy({
        name: policyForm.name,
        description: policyForm.description,
        priority: policyForm.priority,
        rules: JSON.parse(policyForm.rules),
      }),
    onSuccess: async () => {
      toast.success('Policy created.');
      await queryClient.invalidateQueries({ queryKey: ['policies'] });
    },
    onError: () => toast.error('Policy creation failed.'),
  });

  const createRule = useMutation({
    mutationFn: async () =>
      governanceApi.createSensitivityRule({
        table_name: ruleForm.table_name,
        column_name: ruleForm.column_name,
        label: ruleForm.label,
        masking_strategy: ruleForm.masking_strategy,
        priority: ruleForm.priority,
        restricted_roles: ruleForm.restricted_roles.split(',').map((item) => item.trim()).filter(Boolean),
      }),
    onSuccess: async () => {
      toast.success('Sensitivity rule created.');
      await queryClient.invalidateQueries({ queryKey: ['sensitivity-rules'] });
    },
    onError: () => toast.error('Rule creation failed.'),
  });

  const approveMutation = useMutation({
    mutationFn: async (requestId: number) => governanceApi.approve(requestId),
    onSuccess: async () => {
      toast.success('Approval granted.');
      await queryClient.invalidateQueries({ queryKey: ['approvals'] });
    },
  });

  const denyMutation = useMutation({
    mutationFn: async (requestId: number) => governanceApi.deny(requestId, 'Denied from governance console'),
    onSuccess: async () => {
      toast.success('Approval denied.');
      await queryClient.invalidateQueries({ queryKey: ['approvals'] });
    },
  });

  if (!canGovern) {
    return (
      <Panel title="Governance surface" subtitle="This route is intentionally coarse-gated by compliance or admin role.">
        <PermissionBanner action="manage" />
      </Panel>
    );
  }

  return (
    <div className="content-grid">
      <div className="layout-three">
        <Panel title="Audit chain" subtitle="Tamper verification for the active workspace.">
          <div className="stat-card">
            <div className="eyebrow">Integrity</div>
            <div className="stat-value">{verificationQuery.data?.is_valid ? 'Valid' : 'Pending'}</div>
            <div className="muted">{verificationQuery.data ? formatDate(verificationQuery.data.timestamp) : 'Verification loading'}</div>
          </div>
        </Panel>
        <Panel title="Pending approvals" subtitle="Queries waiting for human governance intervention.">
          <div className="stat-card">
            <div className="eyebrow">Queue</div>
            <div className="stat-value">{approvalsQuery.data?.length ?? 0}</div>
          </div>
        </Panel>
        <Panel title="Connector health" subtitle="Current workspace connector posture.">
          <div className="stat-card">
            <div className="eyebrow">Connectors</div>
            <div className="stat-value">{healthQuery.data?.length ?? 0}</div>
          </div>
        </Panel>
      </div>

      <div className="layout-two">
        <div className="stack">
          <Panel title="Policies" subtitle="Row limits, blocked tables, and execution constraints live here.">
            {policiesQuery.data?.length ? (
              <div className="stack">
                {policiesQuery.data.map((policy) => (
                  <div key={policy.id} className="metric-card">
                    <strong>{policy.name}</strong>
                    <p className="muted">{policy.description ?? 'No description.'}</p>
                    <div className="code-box"><pre>{prettyJson(policy.rules_json)}</pre></div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No active policies." copy="Create explicit AST and risk boundaries for this workspace." />
            )}
          </Panel>

          <Panel title="Sensitivity rules" subtitle="Masking rules govern result transformation after execution.">
            {rulesQuery.data?.length ? (
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Table</th>
                      <th>Column</th>
                      <th>Mask</th>
                      <th>Roles</th>
                    </tr>
                  </thead>
                  <tbody>
                    {rulesQuery.data.map((rule) => (
                      <tr key={rule.id}>
                        <td>{rule.table_name}</td>
                        <td>{rule.column_name}</td>
                        <td>{rule.masking_strategy}</td>
                        <td>{rule.restricted_roles.join(', ') || 'all'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <EmptyState title="No sensitivity rules." copy="Add column-level masking requirements for sensitive datasets." />
            )}
          </Panel>

          <Panel title="Approvals queue" subtitle="Inline approve or deny actions keep review work close to query context.">
            {approvalsQuery.data?.length ? (
              <div className="stack">
                {approvalsQuery.data.map((approval) => (
                  <div key={approval.id} className="metric-card">
                    <strong>Request #{approval.id}</strong>
                    <p className="muted">{approval.original_prompt ?? approval.sql_query}</p>
                    <div className="split-inline muted">
                      <span>Risk: {approval.risk_score ?? 'n/a'}</span>
                      <span>{formatDate(approval.created_at)}</span>
                    </div>
                    <div className="toolbar" style={{ marginTop: '0.75rem' }}>
                      <Button onClick={() => approveMutation.mutate(approval.id)}>Approve</Button>
                      <Button tone="danger" onClick={() => denyMutation.mutate(approval.id)}>Deny</Button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No pending approvals." copy="High-risk and low-confidence queries will surface here automatically." />
            )}
          </Panel>
        </div>

        <div className="stack">
          <Panel title="Create policy" subtitle="Paste JSON rules exactly as the backend expects them.">
            <form className="form-grid" onSubmit={(event) => { event.preventDefault(); createPolicy.mutate(); }}>
              <input className="input" value={policyForm.name} onChange={(event) => setPolicyForm((state) => ({ ...state, name: event.target.value }))} />
              <textarea className="textarea" value={policyForm.description} onChange={(event) => setPolicyForm((state) => ({ ...state, description: event.target.value }))} />
              <input className="input" type="number" value={policyForm.priority} onChange={(event) => setPolicyForm((state) => ({ ...state, priority: Number(event.target.value) }))} />
              <textarea className="textarea" value={policyForm.rules} onChange={(event) => setPolicyForm((state) => ({ ...state, rules: event.target.value }))} />
              <Button type="submit">Create policy</Button>
            </form>
          </Panel>

          <Panel title="Create masking rule" subtitle="Define table, column, strategy, and role restrictions.">
            <form className="form-grid" onSubmit={(event) => { event.preventDefault(); createRule.mutate(); }}>
              <input className="input" value={ruleForm.table_name} onChange={(event) => setRuleForm((state) => ({ ...state, table_name: event.target.value }))} />
              <input className="input" value={ruleForm.column_name} onChange={(event) => setRuleForm((state) => ({ ...state, column_name: event.target.value }))} />
              <div className="mini-grid">
                <input className="input" value={ruleForm.label} onChange={(event) => setRuleForm((state) => ({ ...state, label: event.target.value }))} />
                <input className="input" value={ruleForm.masking_strategy} onChange={(event) => setRuleForm((state) => ({ ...state, masking_strategy: event.target.value }))} />
              </div>
              <input className="input" type="number" value={ruleForm.priority} onChange={(event) => setRuleForm((state) => ({ ...state, priority: Number(event.target.value) }))} />
              <input className="input" value={ruleForm.restricted_roles} onChange={(event) => setRuleForm((state) => ({ ...state, restricted_roles: event.target.value }))} />
              <Button type="submit">Create rule</Button>
            </form>
          </Panel>

          <Panel title="Audit feed" subtitle="Treat 403 and approval events as normal product outcomes, not exceptional edge cases.">
            {auditQuery.data?.events?.length ? (
              <div className="stack">
                {auditQuery.data.events.slice(0, 8).map((event) => (
                  <div key={event.id} className="metric-card">
                    <strong>{event.event_type}</strong>
                    <div className="muted">{formatDate(event.created_at)}</div>
                    <div className="code-box"><pre>{prettyJson(event.details ?? {})}</pre></div>
                  </div>
                ))}
              </div>
            ) : (
              <EmptyState title="No audit events returned." copy="Once governance actions run in this workspace, their ledger appears here." />
            )}
          </Panel>
        </div>
      </div>
    </div>
  );
}
