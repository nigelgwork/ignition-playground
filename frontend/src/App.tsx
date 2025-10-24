/**
 * Main App component with routing and providers
 */

import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { CssBaseline, ThemeProvider, createTheme } from '@mui/material';
import { Layout } from './components/Layout';
import { Playbooks } from './pages/Playbooks';
import { Executions } from './pages/Executions';
import { Credentials } from './pages/Credentials';
import { useWebSocket } from './hooks/useWebSocket';
import { useStore } from './store';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Create Material-UI theme
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function AppContent() {
  const setWSConnected = useStore((state) => state.setWSConnected);
  const setExecutionUpdate = useStore((state) => state.setExecutionUpdate);

  // Connect to WebSocket for real-time updates
  useWebSocket({
    onOpen: () => setWSConnected(true),
    onClose: () => setWSConnected(false),
    onExecutionUpdate: (update) => setExecutionUpdate(update.execution_id, update),
  });

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Playbooks />} />
        <Route path="executions" element={<Executions />} />
        <Route path="credentials" element={<Credentials />} />
      </Route>
    </Routes>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <AppContent />
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
