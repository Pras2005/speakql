import axios from 'axios';
import type { AxiosError } from 'axios';

import { API_URL } from '@/constants';
import { authStorage } from '@/lib/auth';
import type {
  ExecuteSqlRequest,
  ExecuteSqlResponse,
  ExplainSqlResponse,
  GenerateSqlRequest,
  GenerateSqlResponse,
  QueryHistoryItem,
  SchemaVisualization,
  UserDatabase,
  UserDatabaseCreate,
} from '@/lib/types';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = authStorage.getToken();
  if (!token) {
    return config;
  }

  return {
    ...config,
    headers: {
      ...config.headers,
      Authorization: `Bearer ${token}`,
    },
  };
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      authStorage.clearToken();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  },
);

export const apiClient = {
  login(username: string, password: string) {
    return api.post<{ access_token: string }>('/login', { username, password });
  },

  signup(username: string, password: string) {
    return api.post('/signup', { username, password });
  },

  getDatabases() {
    return api.get<UserDatabase[]>('/get_databases');
  },

  addDatabase(payload: UserDatabaseCreate) {
    return api.post<{ msg: string; db_id: number; mcp_api_key?: string }>('/databases', payload);
  },

  deleteDatabase(dbId: number) {
    return api.delete(`/databases/${dbId}`);
  },

  rotateMcpKey(dbId: number) {
    return api.post<{ mcp_api_key: string }>(`/databases/${dbId}/rotate-mcp-key`);
  },

  getQueryHistory(dbId: number) {
    return api.get<QueryHistoryItem[]>(`/query-history/${dbId}`);
  },

  generateSql(payload: GenerateSqlRequest) {
    return api.post<GenerateSqlResponse>('/agent/generate-sql', payload);
  },

  executeSql(payload: ExecuteSqlRequest) {
    return api.post<ExecuteSqlResponse>('/agent/execute-sql', payload);
  },

  explainSql(payload: ExecuteSqlRequest) {
    return api.post<ExplainSqlResponse>('/agent/explain-sql', payload);
  },

  exportSql(payload: ExecuteSqlRequest, format: string = 'csv') {
    return api.post(`/agent/export-sql?format=${format}`, payload, {
      responseType: 'blob',
    });
  },

  async getSchema(dbId: number): Promise<SchemaVisualization> {
    const response = await api.get<string | SchemaVisualization>(`/agent/visualize-schema?db_id=${dbId}`);
    const payload = response.data;

    if (typeof payload === 'string') {
      return JSON.parse(payload) as SchemaVisualization;
    }

    return payload;
  },
};

export const getErrorMessage = (error: unknown) => {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data as { detail?: string; message?: string } | undefined;
    return detail?.detail || detail?.message || error.message || 'Request failed';
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Something went wrong';
};

export default api;
