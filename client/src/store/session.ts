import { create } from 'zustand';

import { clearToken, getToken, setToken } from '@/lib/auth';
import type { CurrentUser, Membership } from '@/lib/types';

interface SessionState {
  token: string | null;
  currentUser: CurrentUser | null;
  memberships: Membership[];
  activeDatabaseId: number | null;
  setSessionToken: (token: string) => void;
  setCurrentUser: (user: CurrentUser | null) => void;
  setMemberships: (memberships: Membership[]) => void;
  setActiveDatabaseId: (databaseId: number | null) => void;
  resetSession: () => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  token: getToken(),
  currentUser: null,
  memberships: [],
  activeDatabaseId: null,
  setSessionToken: (token) => {
    setToken(token);
    set({ token });
  },
  setCurrentUser: (currentUser) => set({ currentUser }),
  setMemberships: (memberships) => set({ memberships }),
  setActiveDatabaseId: (activeDatabaseId) => set({ activeDatabaseId }),
  resetSession: () => {
    clearToken();
    set({
      token: null,
      currentUser: null,
      memberships: [],
      activeDatabaseId: null,
    });
  },
}));
