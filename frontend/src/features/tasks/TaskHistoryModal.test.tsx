import { cleanup, render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, describe, expect, it, vi } from 'vitest';

import type { TaskHistoryEntry } from '../../types/domain';
import { TaskHistoryModal } from './TaskHistoryModal';

const entry: TaskHistoryEntry = {
  id: 'h1',
  task_id: 'task-1',
  changed_by_name: 'Demo User',
  created_at: '2026-05-11T14:32:00Z',
  fields: [
    { field_name: 'Status', old_value: 'To Do', new_value: 'In Progress' },
    { field_name: 'Priority', old_value: null, new_value: 'High' }
  ]
};

describe('TaskHistoryModal', () => {
  afterEach(() => cleanup());

  it('renders the modal with correct author and timestamp', () => {
    render(<TaskHistoryModal entry={entry} onClose={vi.fn()} />);
    expect(screen.getByText('Demo User')).toBeInTheDocument();
  });

  it('renders a row per FieldChange with field_name, old_value (WAS), new_value (BECAME)', () => {
    render(<TaskHistoryModal entry={entry} onClose={vi.fn()} />);
    expect(screen.getByText('Status')).toBeInTheDocument();
    expect(screen.getByText('To Do')).toBeInTheDocument();
    expect(screen.getByText('In Progress')).toBeInTheDocument();
    expect(screen.getByText('Priority')).toBeInTheDocument();
    expect(screen.getByText('High')).toBeInTheDocument();
  });

  it('displays em-dash for null old_value or new_value', () => {
    render(<TaskHistoryModal entry={entry} onClose={vi.fn()} />);
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThan(0);
  });

  it('calls onClose when the close button is clicked', async () => {
    const handleClose = vi.fn();
    render(<TaskHistoryModal entry={entry} onClose={handleClose} />);
    await userEvent.click(screen.getByRole('button', { name: /close/i }));
    expect(handleClose).toHaveBeenCalledOnce();
  });

  it('calls onClose when the backdrop is clicked', async () => {
    const handleClose = vi.fn();
    render(<TaskHistoryModal entry={entry} onClose={handleClose} />);
    await userEvent.click(screen.getByTestId('modal-backdrop'));
    expect(handleClose).toHaveBeenCalledOnce();
  });
});
