import api from '@/api/client';
import type {
  ExecuteSqlPayload,
  GenerateSqlPayload,
  GenerateSqlResponse,
  GovernedQueryResponse,
  SchemaVisualization,
} from '@/lib/types';

export const agentApi = {
  generate(payload: GenerateSqlPayload) {
    return api.post<GenerateSqlResponse>('/agent/generate-sql', payload);
  },

  execute(payload: ExecuteSqlPayload) {
    return api.post<GovernedQueryResponse>('/agent/execute-sql', payload);
  },

  explain(payload: ExecuteSqlPayload) {
    return api.post<GovernedQueryResponse>('/agent/explain-sql', payload);
  },

  schema(databaseId: number) {
    return api.get<SchemaVisualization>('/agent/visualize-schema', {
      params: { db_id: databaseId },
    });
  },

  exportCsv(payload: ExecuteSqlPayload) {
    return api.post('/agent/export-sql', payload, {
      params: { format: 'csv' },
      responseType: 'blob',
    });
  },
};
