import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { TaskForm } from './TaskForm';

const selectedList = {
  id: 'list-1',
  name: 'Work',
  task_count: 0,
  open_task_count: 0,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
};

describe('TaskForm', () => {
  it('validates required title', async () => {
    const onSubmit = vi.fn();
    render(
      <TaskForm
        lists={[selectedList]}
        selectedList={selectedList}
        task={null}
        onCancel={vi.fn()}
        onSubmit={onSubmit}
      />
    );

    await userEvent.click(screen.getByRole('button', { name: /save task/i }));
    expect(screen.getByText(/title is required/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});

