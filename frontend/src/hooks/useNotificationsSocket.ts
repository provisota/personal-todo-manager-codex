import { useCallback, useEffect, useRef, useState } from 'react';

import { WS_BASE_URL } from '../api/client';
import type { NotificationItem } from '../types/domain';

interface NotificationBatchMessage {
  type: 'notification_batch';
  payload: {
    generated_at: string;
    notifications: NotificationItem[];
  };
}

interface AckOkMessage {
  type: 'ack_ok';
  payload: {
    notification_id: string;
  };
}

interface ErrorMessage {
  type: 'error';
  payload: {
    code: string;
    message: string;
  };
}

type ServerMessage = NotificationBatchMessage | AckOkMessage | ErrorMessage;

export function useNotificationsSocket(enabled: boolean) {
  const [connected, setConnected] = useState(false);
  const [items, setItems] = useState<NotificationItem[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const reconnectDelayRef = useRef(1000);

  const connect = useCallback(() => {
    if (!enabled || socketRef.current) return;
    const socket = new WebSocket(`${WS_BASE_URL}/ws/notifications`);
    socketRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
      reconnectDelayRef.current = 1000;
      socket.send(
        JSON.stringify({
          type: 'subscribe',
          payload: {
            enabled_types: ['overdue', 'due_soon'],
            interval_seconds: 60,
            include_acknowledged: false
          }
        })
      );
    };

    socket.onmessage = (event) => {
      const message = JSON.parse(event.data) as ServerMessage;
      if (message.type === 'notification_batch') {
        setItems(message.payload.notifications);
      }
      if (message.type === 'ack_ok') {
        setItems((current) => current.filter((item) => item.id !== message.payload.notification_id));
      }
    };

    socket.onclose = () => {
      setConnected(false);
      socketRef.current = null;
      if (enabled) {
        reconnectTimerRef.current = window.setTimeout(connect, reconnectDelayRef.current);
        reconnectDelayRef.current = Math.min(reconnectDelayRef.current * 2, 30000);
      }
    };
  }, [enabled]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [connect]);

  const ack = useCallback((notificationId: string) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      setItems((current) => current.filter((item) => item.id !== notificationId));
      return;
    }
    socket.send(JSON.stringify({ type: 'ack', payload: { notification_id: notificationId } }));
  }, []);

  return { connected, items, ack };
}

