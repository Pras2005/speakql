import api from '@/api/client';
import type {
  ApprovalRequest,
  AuditLogResponse,
  AuditVerification,
  Policy,
  PolicyPayload,
  SensitivityRule,
  SensitivityRulePayload,
} from '@/lib/types';

export const governanceApi = {
  policies() {
    return api.get<Policy[]>('/governance/policies');
  },

  createPolicy(payload: PolicyPayload) {
    return api.post<Policy>('/governance/policies', payload);
  },

  sensitivityRules() {
    return api.get<SensitivityRule[]>('/governance/sensitivity-rules');
  },

  createSensitivityRule(payload: SensitivityRulePayload) {
    return api.post<SensitivityRule>('/governance/sensitivity-rules', payload);
  },

  pendingApprovals() {
    return api.get<ApprovalRequest[]>('/governance/approvals/pending');
  },

  approve(requestId: number) {
    return api.post(`/governance/approvals/${requestId}/approve`);
  },

  deny(requestId: number, reason: string) {
    return api.post(`/governance/approvals/${requestId}/deny`, null, {
      params: { reason },
    });
  },

  auditLogs() {
    return api.get<AuditLogResponse>('/governance/audit-logs');
  },

  verifyAudit() {
    return api.get<AuditVerification>('/governance/audit-logs/verify');
  },
};
