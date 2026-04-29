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
  const pendingAckIdsRef = useRef<Set<string>>(new Set());

  const sendAck = useCallback((socket: WebSocket, notificationId: string) => {
    socket.send(JSON.stringify({ type: 'ack', payload: { notification_id: notificationId } }));
  }, []);

  const flushPendingAcks = useCallback((socket: WebSocket) => {
    pendingAckIdsRef.current.forEach((notificationId) => sendAck(socket, notificationId));
  }, [sendAck]);

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
      flushPendingAcks(socket);
    };

    socket.onmessage = (event) => {
      let message: ServerMessage;
      try {
        message = JSON.parse(event.data) as ServerMessage;
      } catch {
        return;
      }
      if (message.type === 'notification_batch') {
        setItems(
          message.payload.notifications.filter((item) => !pendingAckIdsRef.current.has(item.id))
        );
      }
      if (message.type === 'ack_ok') {
        pendingAckIdsRef.current.delete(message.payload.notification_id);
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
  }, [enabled, flushPendingAcks]);

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
    pendingAckIdsRef.current.add(notificationId);
    setItems((current) => current.filter((item) => item.id !== notificationId));
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return;
    }
    sendAck(socket, notificationId);
  }, [sendAck]);

  return { connected, items, ack };
}
