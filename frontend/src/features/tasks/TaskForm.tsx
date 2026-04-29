import { useEffect, useState } from 'react';

import type { ProjectList, Task, TaskPriority, TaskStatus } from '../../types/domain';

export interface TaskFormValue {
  list_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
}

interface Props {
  lists: ProjectList[];
  selectedList: ProjectList;
  task: Task | null;
  onCancel: () => void;
  onSubmit: (value: TaskFormValue) => Promise<void>;
}

const defaultStatus: TaskStatus = 'todo';
const defaultPriority: TaskPriority = 'medium';

export function TaskForm({ lists, selectedList, task, onCancel, onSubmit }: Props) {
  const [value, setValue] = useState<TaskFormValue>({
    list_id: selectedList.id,
    title: '',
    description: '',
    status: defaultStatus,
    priority: defaultPriority,
    due_date: null
  });
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setValue(
      task
        ? {
            list_id: task.list_id,
            title: task.title,
            description: task.description,
            status: task.status,
            priority: task.priority,
            due_date: task.due_date
          }
        : {
            list_id: selectedList.id,
            title: '',
            description: '',
            status: defaultStatus,
            priority: defaultPriority,
            due_date: null
          }
    );
    setError(null);
  }, [task, selectedList.id]);

  async function submit() {
    if (!value.title.trim()) {
      setError('Title is required');
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await onSubmit({ ...value, title: value.title.trim() });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save task');
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="modal-backdrop" role="presentation">
      <form
        className="task-modal"
        onSubmit={(event) => {
          event.preventDefault();
          void submit();
        }}
      >
        <header>
          <h2>{task ? 'Edit task' : 'Create task'}</h2>
          <p>{selectedList.name}</p>
        </header>
        <label>
          <span>Title</span>
          <input value={value.title} onChange={(event) => setValue({ ...value, title: event.target.value })} maxLength={200} autoFocus />
        </label>
        <label>
          <span>Description</span>
          <textarea value={value.description} onChange={(event) => setValue({ ...value, description: event.target.value })} rows={4} />
        </label>
        <div className="form-grid">
          <label>
            <span>Status</span>
            <select value={value.status} onChange={(event) => setValue({ ...value, status: event.target.value as TaskStatus })}>
              <option value="todo">To Do</option>
              <option value="in_progress">In Progress</option>
              <option value="done">Done</option>
            </select>
          </label>
          <label>
            <span>Priority</span>
            <select value={value.priority} onChange={(event) => setValue({ ...value, priority: event.target.value as TaskPriority })}>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </label>
          <label>
            <span>Due date</span>
            <input type="date" value={value.due_date ?? ''} onChange={(event) => setValue({ ...value, due_date: event.target.value || null })} />
          </label>
          <label>
            <span>List</span>
            <select value={value.list_id} onChange={(event) => setValue({ ...value, list_id: event.target.value })}>
              {lists.map((list) => (
                <option key={list.id} value={list.id}>{list.name}</option>
              ))}
            </select>
          </label>
        </div>
        {error ? <div className="field-error">{error}</div> : null}
        <footer>
          <button className="ghost-button" type="button" onClick={onCancel}>Cancel</button>
          <button className="primary-button" type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save task'}</button>
        </footer>
      </form>
    </div>
  );
}

