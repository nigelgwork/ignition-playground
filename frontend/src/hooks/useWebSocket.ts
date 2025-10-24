/**
 * WebSocket hook for real-time execution updates
 */

import { useEffect, useRef, useCallback } from 'react';
import type { WebSocketMessage, ExecutionUpdate } from '../types/api';

const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:5000/ws/executions';
const WS_API_KEY = import.meta.env.VITE_WS_API_KEY || 'dev-key-change-in-production';

interface UseWebSocketOptions {
  onExecutionUpdate?: (update: ExecutionUpdate) => void;
  onError?: (error: Event) => void;
  onOpen?: () => void;
  onClose?: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<number | undefined>(undefined);
  const { onExecutionUpdate, onError, onOpen, onClose } = options;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    try {
      const ws = new WebSocket(`${WS_URL}?api_key=${WS_API_KEY}`);

      ws.onopen = () => {
        console.log('[WebSocket] Connected');
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);

          if (message.type === 'execution_update' && message.data) {
            onExecutionUpdate?.(message.data);
          } else if (message.type === 'error') {
            console.error('[WebSocket] Error:', message.error);
          }
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      ws.onerror = (event) => {
        console.error('[WebSocket] Error:', event);
        onError?.(event);
      };

      ws.onclose = () => {
        console.log('[WebSocket] Disconnected');
        onClose?.();

        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('[WebSocket] Reconnecting...');
          connect();
        }, 5000);
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error);
    }
  }, [onExecutionUpdate, onError, onOpen, onClose]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  return {
    isConnected: wsRef.current?.readyState === WebSocket.OPEN,
    disconnect,
    reconnect: connect,
  };
}
