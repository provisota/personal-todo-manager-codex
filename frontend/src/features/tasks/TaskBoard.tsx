import { CalendarDays, CheckCircle2, Circle, Clock3, History, Pencil, Plus, Search, Trash2 } from 'lucide-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { api } from '../../api/client';
import type { DueFilter, ProjectList, Task, TaskFilters, TaskHistoryEntry, TaskPriority, TaskStatus } from '../../types/domain';
import { TaskForm, type TaskFormValue } from './TaskForm';
import { TaskHistory } from './TaskHistory';
import { TaskHistoryModal } from './TaskHistoryModal';

interface Props {
  lists: ProjectList[];
  selectedList: ProjectList | null;
  focusedTaskId?: string | null;
  onFocusHandled?: () => void;
  onTasksChanged: () => Promise<void>;
}

const defaultFilters: TaskFilters = { search: '', status: '', priority: '', due: 'all' };

const statusLabels: Record<TaskStatus, string> = {
  todo: 'To Do',
  in_progress: 'In Progress',
  done: 'Done'
};

const priorityLabels: Record<TaskPriority, string> = {
  low: 'Low',
  medium: 'Medium',
  high: 'High'
};

export function TaskBoard({
  lists,
  selectedList,
  focusedTaskId,
  onFocusHandled,
  onTasksChanged
}: Props) {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [filters, setFilters] = useState<TaskFilters>(defaultFilters);
  const [highlightedTaskId, setHighlightedTaskId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formTask, setFormTask] = useState<Task | null>(null);
  const [formOpen, setFormOpen] = useState(false);
  const [historyTask, setHistoryTask] = useState<Task | null>(null);
  const [selectedHistoryEntry, setSelectedHistoryEntry] = useState<TaskHistoryEntry | null>(null);

  const loadTasks = useCallback(async () => {
    if (!selectedList) {
      setTasks([]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setTasks(await api.tasks(selectedList.id, filters));
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load tasks');
    } finally {
      setLoading(false);
    }
  }, [selectedList, filters]);

  useEffect(() => {
    void loadTasks();
  }, [loadTasks]);

  useEffect(() => {
    if (focusedTaskId) {
      setFilters(defaultFilters);
    }
  }, [focusedTaskId]);

  useEffect(() => {
    if (!focusedTaskId || loading) {
      return undefined;
    }
    const taskElement = document.getElementById(`task-${focusedTaskId}`);
    if (!taskElement) {
      return undefined;
    }
    taskElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
    setHighlightedTaskId(focusedTaskId);
    onFocusHandled?.();
    const timeout = window.setTimeout(() => setHighlightedTaskId(null), 2600);
    return () => window.clearTimeout(timeout);
  }, [focusedTaskId, loading, onFocusHandled, tasks]);

  const hasActiveFilters = useMemo(
    () => Boolean(filters.search || filters.status || filters.priority || filters.due !== 'all'),
    [filters]
  );

  async function saveTask(value: TaskFormValue) {
    if (formTask) {
      await api.updateTask(formTask.id, value);
    } else {
      await api.createTask(value);
    }
    setFormOpen(false);
    setFormTask(null);
    await loadTasks();
    await onTasksChanged();
  }

  async function changeStatus(task: Task, status: TaskStatus) {
    await api.updateTaskStatus(task.id, status);
    await loadTasks();
    await onTasksChanged();
  }

  async function deleteTask(task: Task) {
    if (!window.confirm(`Delete "${task.title}"?`)) return;
    await api.deleteTask(task.id);
    await loadTasks();
    await onTasksChanged();
  }

  if (!selectedList) {
    return (
      <section className="task-board">
        <div className="empty-main">
          <h1>No list selected</h1>
          <p>Create a list from the sidebar to start adding tasks.</p>
        </div>
      </section>
    );
  }

  return (
    <section className="task-board">
      <header className="board-header">
        <div>
          <div className="eyebrow">Selected list</div>
          <h1>{selectedList.name}</h1>
        </div>
        <button className="primary-button" type="button" onClick={() => { setFormTask(null); setFormOpen(true); }}>
          <Plus size={18} />
          New task
        </button>
      </header>

      <div className="filters-bar">
        <label className="search-field">
          <Search size={18} />
          <input
            value={filters.search}
            onChange={(event) => setFilters({ ...filters, search: event.target.value })}
            placeholder="Search title or description"
          />
        </label>
        <select value={filters.status} onChange={(event) => setFilters({ ...filters, status: event.target.value as TaskStatus | '' })}>
          <option value="">Any status</option>
          <option value="todo">To Do</option>
          <option value="in_progress">In Progress</option>
          <option value="done">Done</option>
        </select>
        <select value={filters.priority} onChange={(event) => setFilters({ ...filters, priority: event.target.value as TaskPriority | '' })}>
          <option value="">Any priority</option>
          <option value="low">Low</option>
          <option value="medium">Medium</option>
          <option value="high">High</option>
        </select>
        <select value={filters.due} onChange={(event) => setFilters({ ...filters, due: event.target.value as DueFilter })}>
          <option value="all">All due dates</option>
          <option value="overdue">Overdue</option>
          <option value="today">Today</option>
          <option value="next_7_days">Next 7 days</option>
        </select>
      </div>

      {error ? <div className="alert">{error}</div> : null}
      {loading ? <div className="task-loading">Loading tasks...</div> : null}
      {!loading && tasks.length === 0 ? (
        <div className="empty-main">
          <h2>{hasActiveFilters ? 'No matching tasks' : 'No tasks yet'}</h2>
          <p>{hasActiveFilters ? 'Adjust search or filters to broaden the result.' : 'Create the first task for this list.'}</p>
        </div>
      ) : null}

      <div className="task-list">
        {tasks.map((task) => (
          <article
            className={`task-card priority-${task.priority} ${task.id === highlightedTaskId ? 'highlighted' : ''}`}
            id={`task-${task.id}`}
            key={task.id}
          >
            <div className="task-status-icon" aria-hidden="true">
              {task.status === 'done' ? <CheckCircle2 size={22} /> : task.status === 'in_progress' ? <Clock3 size={22} /> : <Circle size={22} />}
            </div>
            <div className="task-content">
              <div className="task-title-row">
                <h2>{task.title}</h2>
                <span className={`pill ${task.status}`}>{statusLabels[task.status]}</span>
                <span className={`pill priority ${task.priority}`}>{priorityLabels[task.priority]}</span>
              </div>
              {task.description ? <p>{task.description}</p> : null}
              <div className="task-meta">
                <CalendarDays size={16} />
                {task.due_date ? <span>Due {task.due_date}</span> : <span>No due date</span>}
              </div>
            </div>
            <div className="task-actions">
              <select value={task.status} onChange={(event) => void changeStatus(task, event.target.value as TaskStatus)} aria-label={`Change status for ${task.title}`}>
                <option value="todo">To Do</option>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
              </select>
              <button className="icon-button" type="button" aria-label={`Edit ${task.title}`} onClick={() => { setFormTask(task); setFormOpen(true); }}>
                <Pencil size={17} />
              </button>
              <button className="icon-button" type="button" aria-label={`History for ${task.title}`} onClick={() => setHistoryTask(historyTask?.id === task.id ? null : task)}>
                <History size={17} />
              </button>
              <button className="icon-button danger" type="button" aria-label={`Delete ${task.title}`} onClick={() => void deleteTask(task)}>
                <Trash2 size={17} />
              </button>
            </div>
          </article>
        ))}
      </div>

      {historyTask && (
        <aside className="history-panel">
          <div className="history-panel-header">
            <span className="history-panel-title">History: {historyTask.title}</span>
            <button className="icon-button" type="button" aria-label="Close history" onClick={() => setHistoryTask(null)}>×</button>
          </div>
          <TaskHistory taskId={historyTask.id} onEntryClick={(entry) => setSelectedHistoryEntry(entry)} />
        </aside>
      )}

      {formOpen ? (
        <TaskForm
          lists={lists}
          selectedList={selectedList}
          task={formTask}
          onCancel={() => {
            setFormOpen(false);
            setFormTask(null);
          }}
          onSubmit={saveTask}
        />
      ) : null}

      {selectedHistoryEntry && (
        <TaskHistoryModal entry={selectedHistoryEntry} onClose={() => setSelectedHistoryEntry(null)} />
      )}
    </section>
  );
}
