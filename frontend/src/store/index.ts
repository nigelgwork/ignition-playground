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

interface ScreenshotFrame {
  executionId: string;
  screenshot: string; // base64 encoded JPEG
  timestamp: string;
}

interface AppState {
  // Execution updates from WebSocket
  executionUpdates: Map<string, ExecutionUpdate>;
  setExecutionUpdate: (executionId: string, update: ExecutionUpdate) => void;

  // Screenshot frames from WebSocket
  currentScreenshots: Map<string, ScreenshotFrame>;
  setScreenshotFrame: (executionId: string, frame: ScreenshotFrame) => void;

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

  currentScreenshots: new Map(),
  setScreenshotFrame: (executionId, frame) =>
    set((state) => {
      const newScreenshots = new Map(state.currentScreenshots);
      newScreenshots.set(executionId, frame);
      return { currentScreenshots: newScreenshots };
    }),

  isWSConnected: false,
  setWSConnected: (connected) => set({ isWSConnected: connected }),

  theme: getInitialTheme(),
  setTheme: (theme) => {
    localStorage.setItem('theme', theme);
    set({ theme });
  },
}));
