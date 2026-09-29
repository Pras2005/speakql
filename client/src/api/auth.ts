import api from '@/api/client';
import type { AuthTokenResponse, CurrentUser, LoginPayload, SignupPayload } from '@/lib/types';

export const authApi = {
  login(payload: LoginPayload, workspaceId?: number) {
    return api.post<AuthTokenResponse>('/login', payload, {
      params: workspaceId ? { workspace_id: workspaceId } : undefined,
    });
  },

  signup(payload: SignupPayload) {
    return api.post('/signup', payload);
  },

  me() {
    return api.get<CurrentUser>('/me');
  },
};
