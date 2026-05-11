import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import type { TaskHistoryEntry } from '../../types/domain';
import { TaskHistory } from './TaskHistory';

const apiMock = vi.hoisted(() => ({
  taskHistory: vi.fn()
}));

vi.mock('../../api/client', () => ({
  api: apiMock
}));

const entry1: TaskHistoryEntry = {
  id: 'h1',
  task_id: 'task-1',
  changed_by_name: 'Demo User',
  created_at: '2026-05-11T10:00:00Z',
  fields: [
    { field_name: 'Title', old_value: 'Old', new_value: 'New' },
    { field_name: 'Status', old_value: 'To Do', new_value: 'In Progress' }
  ]
};

const entry2: TaskHistoryEntry = {
  id: 'h2',
  task_id: 'task-1',
  changed_by_name: 'Demo User',
  created_at: '2026-05-10T08:00:00Z',
  fields: [{ field_name: 'Priority', old_value: 'Low', new_value: 'High' }]
};

describe('TaskHistory', () => {
  beforeEach(() => {
    apiMock.taskHistory.mockReset();
  });

  afterEach(() => {
    cleanup();
  });

  it('calls api.taskHistory on mount', async () => {
    apiMock.taskHistory.mockResolvedValue([]);
    render(<TaskHistory taskId="task-1" onEntryClick={vi.fn()} />);
    await waitFor(() => expect(apiMock.taskHistory).toHaveBeenCalledWith('task-1'));
  });

  it('renders a list of history entries with timestamp, author, field summary', async () => {
    apiMock.taskHistory.mockResolvedValue([entry1, entry2]);
    render(<TaskHistory taskId="task-1" onEntryClick={vi.fn()} />);
    await waitFor(() => expect(screen.getAllByText('Demo User')).toHaveLength(2));
    expect(screen.getByText(/Title, Status/i)).toBeInTheDocument();
    expect(screen.getByText(/Priority/i)).toBeInTheDocument();
  });

  it('shows empty-state message when history is empty', async () => {
    apiMock.taskHistory.mockResolvedValue([]);
    render(<TaskHistory taskId="task-1" onEntryClick={vi.fn()} />);
    await waitFor(() => expect(screen.getByText(/no history/i)).toBeInTheDocument());
  });

  it('calls onEntryClick when an entry is clicked', async () => {
    apiMock.taskHistory.mockResolvedValue([entry1]);
    const handleClick = vi.fn();
    render(<TaskHistory taskId="task-1" onEntryClick={handleClick} />);
    await waitFor(() => expect(screen.getByText('Demo User')).toBeInTheDocument());
    await userEvent.click(screen.getByText('Demo User'));
    expect(handleClick).toHaveBeenCalledWith(entry1);
  });
});
