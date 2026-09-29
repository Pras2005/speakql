import api from '@/api/client';
import type {
  ConnectorHealth,
  CreateGrantPayload,
  Database,
  DatabaseCreatePayload,
  DatabaseGrant,
  DatabaseUpdatePayload,
  QueryHistoryItem,
  UpdateGrantPayload,
} from '@/lib/types';

export const databasesApi = {
  list() {
    return api.get<Database[]>('/databases');
  },

  create(payload: DatabaseCreatePayload) {
    return api.post<{ msg: string; db_id: number; mcp_api_key?: string }>('/databases', payload);
  },

  update(databaseId: number, payload: DatabaseUpdatePayload) {
    return api.put<{ msg: string; db_id: number }>(`/databases/${databaseId}`, payload);
  },

  remove(databaseId: number) {
    return api.delete(`/databases/${databaseId}`);
  },

  rotateKey(databaseId: number) {
    return api.post<{ mcp_api_key: string }>(`/databases/${databaseId}/rotate-mcp-key`);
  },

  refreshCatalog(databaseId: number) {
    return api.post<{ msg: string }>(`/databases/${databaseId}/refresh-catalog`);
  },

  history(databaseId: number) {
    return api.get<QueryHistoryItem[]>(`/databases/${databaseId}/query-history`);
  },

  listGrants(databaseId: number) {
    return api.get<DatabaseGrant[]>(`/databases/${databaseId}/grants`);
  },

  createGrant(databaseId: number, payload: CreateGrantPayload) {
    return api.post<DatabaseGrant>(`/databases/${databaseId}/grants`, payload);
  },

  updateGrant(databaseId: number, userId: number, payload: UpdateGrantPayload) {
    return api.patch<DatabaseGrant>(`/databases/${databaseId}/grants/${userId}`, payload);
  },

  deleteGrant(databaseId: number, userId: number) {
    return api.delete(`/databases/${databaseId}/grants/${userId}`);
  },
};

export const healthApi = {
  list() {
    return api.get<ConnectorHealth[]>('/governance/connector-health');
  },

  refresh(databaseId: number) {
    return api.post<ConnectorHealth>(`/governance/connector-health/${databaseId}/refresh`);
  },
};
