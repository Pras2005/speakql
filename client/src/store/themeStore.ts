import { create } from 'zustand';

type Theme = 'dark' | 'light';

interface ThemeState {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

export const useThemeStore = create<ThemeState>((set) => ({
  theme: (document.documentElement.getAttribute('data-theme') as Theme) || 'dark',
  toggleTheme: () =>
    set((state) => {
      const newTheme = state.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', newTheme);
      return { theme: newTheme };
    }),
  setTheme: (theme: Theme) => {
    document.documentElement.setAttribute('data-theme', theme);
    set({ theme });
  },
}));
