import api from '@/api/client';
import type { Report, ReportPayload } from '@/lib/types';

export const reportsApi = {
  list() {
    return api.get<Report[]>('/reports');
  },

  create(payload: ReportPayload) {
    return api.post<Report>('/reports', payload);
  },

  run(reportId: number, dbId: number) {
    return api.post(`/reports/${reportId}/run`, { db_id: dbId });
  },
};
