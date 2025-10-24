/**
 * Zustand store for global state management
 */

import { create } from 'zustand';
import type { ExecutionUpdate } from '../types/api';

interface AppState {
  // Execution updates from WebSocket
  executionUpdates: Map<string, ExecutionUpdate>;
  setExecutionUpdate: (executionId: string, update: ExecutionUpdate) => void;

  // WebSocket connection status
  isWSConnected: boolean;
  setWSConnected: (connected: boolean) => void;
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
}));
