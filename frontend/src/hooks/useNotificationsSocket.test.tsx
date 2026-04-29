import { act, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useNotificationsSocket } from './useNotificationsSocket';

class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSED = 3;
  static instances: MockWebSocket[] = [];

  readyState = MockWebSocket.CONNECTING;
  sent: string[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onclose: (() => void) | null = null;

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
  }

  send(payload: string) {
    this.sent.push(payload);
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.();
  }
}

function Harness() {
  const notifications = useNotificationsSocket(true);
  return (
    <div>
      {notifications.items.map((item) => (
        <button key={item.id} type="button" onClick={() => notifications.ack(item.id)}>
          {item.title}
        </button>
      ))}
    </div>
  );
}

describe('useNotificationsSocket', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    MockWebSocket.instances = [];
    vi.stubGlobal('WebSocket', MockWebSocket);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it('queues acknowledgements while disconnected and flushes them after reconnect', async () => {
    render(<Harness />);
    const firstSocket = MockWebSocket.instances[0];

    act(() => {
      firstSocket.readyState = MockWebSocket.OPEN;
      firstSocket.onopen?.();
      firstSocket.onmessage?.({
        data: JSON.stringify({
          type: 'notification_batch',
          payload: {
            generated_at: new Date().toISOString(),
            notifications: [
              {
                id: 'overdue:task-1',
                type: 'overdue',
                task_id: 'task-1',
                list_id: 'list-1',
                title: 'Queued ack task',
                due_date: '2026-04-28',
                priority: 'high',
                message: 'Task is overdue'
              }
            ]
          }
        })
      } as MessageEvent);
      firstSocket.readyState = MockWebSocket.CLOSED;
      firstSocket.onclose?.();
    });

    fireEvent.click(screen.getByRole('button', { name: /queued ack task/i }));
    expect(screen.queryByRole('button', { name: /queued ack task/i })).not.toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    const secondSocket = MockWebSocket.instances[1];
    act(() => {
      secondSocket.readyState = MockWebSocket.OPEN;
      secondSocket.onopen?.();
    });

    expect(secondSocket.sent).toContain(
      JSON.stringify({ type: 'ack', payload: { notification_id: 'overdue:task-1' } })
    );
  });
});
