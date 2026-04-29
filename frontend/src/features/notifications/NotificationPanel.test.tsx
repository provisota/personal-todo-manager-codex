import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { NotificationPanel } from './NotificationPanel';

describe('NotificationPanel', () => {
  it('renders task title, due date, priority and acknowledges notifications', async () => {
    const onAck = vi.fn();
    render(
      <NotificationPanel
        connected
        items={[
          {
            id: 'overdue:task-1',
            type: 'overdue',
            task_id: 'task-1',
            list_id: 'list-1',
            title: 'Pay invoice',
            due_date: '2026-04-28',
            priority: 'high',
            message: 'Task is overdue'
          }
        ]}
        onAck={onAck}
        onNavigate={vi.fn()}
      />
    );

    expect(screen.getByText('Pay invoice')).toBeInTheDocument();
    expect(screen.getByText(/due 2026-04-28/i)).toBeInTheDocument();
    expect(screen.getByText(/high priority/i)).toBeInTheDocument();

    await userEvent.click(screen.getByRole('button', { name: /acknowledge pay invoice/i }));
    expect(onAck).toHaveBeenCalledWith('overdue:task-1');
  });
});
