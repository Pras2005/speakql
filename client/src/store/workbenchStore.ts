import { create } from 'zustand';

interface WorkbenchState {
  prompt: string;
  sql: string;
  status: 'idle' | 'generating' | 'executing' | 'success' | 'error' | 'approval_required';
  result: any[] | null;
  explainability: any | null;
  setPrompt: (prompt: string) => void;
  setSql: (sql: string) => void;
  setStatus: (status: WorkbenchState['status']) => void;
  setResult: (result: any[] | null) => void;
  setExplainability: (explainability: any | null) => void;
  clearWorkbench: () => void;
}

export const useWorkbenchStore = create<WorkbenchState>((set) => ({
  prompt: '',
  sql: '',
  status: 'idle',
  result: null,
  explainability: null,
  setPrompt: (prompt) => set({ prompt }),
  setSql: (sql) => set({ sql }),
  setStatus: (status) => set({ status }),
  setResult: (result) => set({ result }),
  setExplainability: (explainability) => set({ explainability }),
  clearWorkbench: () => set({ prompt: '', sql: '', status: 'idle', result: null, explainability: null }),
}));
