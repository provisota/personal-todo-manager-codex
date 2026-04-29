import { cleanup, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { TaskBoard } from './TaskBoard';

const apiMock = vi.hoisted(() => ({
  tasks: vi.fn(),
  updateTaskStatus: vi.fn(),
  createTask: vi.fn(),
  updateTask: vi.fn(),
  deleteTask: vi.fn()
}));

vi.mock('../../api/client', () => ({
  api: apiMock
}));

const selectedList = {
  id: 'list-1',
  name: 'Work',
  task_count: 1,
  open_task_count: 1,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
};

const task = {
  id: 'task-1',
  list_id: 'list-1',
  title: 'Write tests',
  description: 'Cover task board',
  status: 'todo' as const,
  priority: 'high' as const,
  due_date: '2026-05-01',
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString(),
  completed_at: null
};

describe('TaskBoard', () => {
  beforeEach(() => {
    apiMock.tasks.mockReset();
    apiMock.updateTaskStatus.mockReset();
    apiMock.tasks.mockResolvedValue([task]);
    apiMock.updateTaskStatus.mockResolvedValue({ ...task, status: 'done', completed_at: new Date().toISOString() });
  });

  afterEach(() => {
    cleanup();
  });

  it('reloads tasks with selected filters', async () => {
    const user = userEvent.setup();
    render(
      <TaskBoard
        lists={[selectedList]}
        selectedList={selectedList}
        onTasksChanged={vi.fn()}
      />
    );

    await screen.findByText('Write tests');
    await user.selectOptions(screen.getByDisplayValue('Any priority'), 'high');

    await waitFor(() => {
      expect(apiMock.tasks).toHaveBeenLastCalledWith(
        'list-1',
        expect.objectContaining({ priority: 'high' })
      );
    });
  });

  it('updates task status from the quick status control', async () => {
    const onTasksChanged = vi.fn().mockResolvedValue(undefined);
    const user = userEvent.setup();
    render(
      <TaskBoard
        lists={[selectedList]}
        selectedList={selectedList}
        onTasksChanged={onTasksChanged}
      />
    );

    await screen.findByText('Write tests');
    await user.selectOptions(screen.getAllByLabelText(/change status for write tests/i)[0], 'done');

    expect(apiMock.updateTaskStatus).toHaveBeenCalledWith('task-1', 'done');
    await waitFor(() => expect(onTasksChanged).toHaveBeenCalled());
  });
});
