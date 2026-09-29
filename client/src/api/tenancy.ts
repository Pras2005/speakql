import api from '@/api/client';
import type { AuthTokenResponse, Membership } from '@/lib/types';

export const tenancyApi = {
  memberships() {
    return api.get<Membership[]>('/tenancy/memberships');
  },

  switchWorkspace(workspaceId: number) {
    return api.post<AuthTokenResponse>(`/tenancy/switch-workspace/${workspaceId}`);
  },
};
