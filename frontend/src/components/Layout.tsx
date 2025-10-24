/**
 * Main layout with navigation
 */

import { Box, AppBar, Toolbar, Typography, Drawer, List, ListItemButton, ListItemText } from '@mui/material';
import { Link, Outlet, useLocation } from 'react-router-dom';
import { useStore } from '../store';

const DRAWER_WIDTH = 240;

const navItems = [
  { path: '/', label: 'Playbooks' },
  { path: '/executions', label: 'Executions' },
  { path: '/credentials', label: 'Credentials' },
];

export function Layout() {
  const location = useLocation();
  const isWSConnected = useStore((state) => state.isWSConnected);

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Ignition Automation Toolkit
          </Typography>
          <Box
            sx={{
              width: 12,
              height: 12,
              borderRadius: '50%',
              bgcolor: isWSConnected ? 'success.main' : 'error.main',
              mr: 1,
            }}
          />
          <Typography variant="body2" color="inherit">
            {isWSConnected ? 'Connected' : 'Disconnected'}
          </Typography>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: DRAWER_WIDTH,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: DRAWER_WIDTH,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {navItems.map((item) => (
              <ListItemButton
                key={item.path}
                component={Link}
                to={item.path}
                selected={location.pathname === item.path}
              >
                <ListItemText primary={item.label} />
              </ListItemButton>
            ))}
          </List>
        </Box>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
}
