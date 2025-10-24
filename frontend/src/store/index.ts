/**
 * Zustand store for global state management
 */

import { create } from 'zustand';
import type { ExecutionUpdate } from '../types/api';

// Initialize theme from localStorage or default to 'dark'
const getInitialTheme = (): 'dark' | 'light' => {
  const stored = localStorage.getItem('theme');
  return (stored === 'light' || stored === 'dark') ? stored : 'dark';
};

interface AppState {
  // Execution updates from WebSocket
  executionUpdates: Map<string, ExecutionUpdate>;
  setExecutionUpdate: (executionId: string, update: ExecutionUpdate) => void;

  // WebSocket connection status
  isWSConnected: boolean;
  setWSConnected: (connected: boolean) => void;

  // Theme mode
  theme: 'dark' | 'light';
  setTheme: (theme: 'dark' | 'light') => void;
}

export const useStore = create<AppState>((set) => ({
  executionUpdates: new Map(),
  setExecutionUpdate: (executionId, update) =>
    set((state) => {
      const newUpdates = new Map(state.executionUpdates);
      newUpdates.set(executionId, update);
      return { executionUpdates: newUpdates };
    }),

  isWSConnected: false,
  setWSConnected: (connected) => set({ isWSConnected: connected }),

  theme: getInitialTheme(),
  setTheme: (theme) => {
    localStorage.setItem('theme', theme);
    set({ theme });
  },
}));
