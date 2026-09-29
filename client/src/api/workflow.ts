import api from '@/api/client';
import type { GovernedQueryResponse, SavedQuery, SavedQueryPayload } from '@/lib/types';

export const workflowApi = {
  list() {
    return api.get<SavedQuery[]>('/workflow/queries');
  },

  create(payload: SavedQueryPayload) {
    return api.post<SavedQuery>('/workflow/queries', payload);
  },

  submit(queryId: number) {
    return api.post<SavedQuery>(`/workflow/queries/${queryId}/submit`);
  },

  replay(queryId: number, dbId: number, bypassApproval = false) {
    return api.post<GovernedQueryResponse>(`/workflow/queries/${queryId}/replay`, {
      db_id: dbId,
      bypass_approval: bypassApproval,
    });
  },
};
