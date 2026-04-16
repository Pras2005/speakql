import { create } from 'zustand';

interface User {
  id: number;
  email: string;
  role: string;
}

interface Workspace {
  id: number;
  name: string;
}

interface Database {
  id: number;
  name: string;
}

interface SessionState {
  user: User | null;
  workspace: Workspace | null;
  activeDatabase: Database | null;
  setUser: (user: User | null) => void;
  setWorkspace: (workspace: Workspace | null) => void;
  setActiveDatabase: (db: Database | null) => void;
}

export const useSessionStore = create<SessionState>((set) => ({
  user: null,
  workspace: null,
  activeDatabase: null,
  setUser: (user) => set({ user }),
  setWorkspace: (workspace) => set({ workspace }),
  setActiveDatabase: (activeDatabase) => set({ activeDatabase }),
}));
