import type { AuthProviders, ProjectList, Task, TaskFilters, TaskHistoryEntry, TaskPriority, TaskStatus, User } from '../types/domain';

function defaultApiBaseUrl() {
  if (typeof window === 'undefined') {
    return 'http://localhost:8000';
  }
  return `${window.location.protocol}//${window.location.hostname}:8000`;
}

function normalizeLoopbackUrl(value: string, fallbackProtocol?: string) {
  if (typeof window === 'undefined') {
    return value;
  }
  const url = new URL(value);
  const currentHost = window.location.hostname;
  const loopbackHosts = new Set(['localhost', '127.0.0.1']);
  if (loopbackHosts.has(url.hostname) && loopbackHosts.has(currentHost)) {
    url.hostname = currentHost;
  }
  if (fallbackProtocol && !url.protocol) {
    url.protocol = fallbackProtocol;
  }
  return url.toString().replace(/\/$/, '');
}

export const API_BASE_URL = normalizeLoopbackUrl(import.meta.env.VITE_API_BASE_URL || defaultApiBaseUrl());
export const WS_BASE_URL = normalizeLoopbackUrl(
  import.meta.env.VITE_WS_BASE_URL || API_BASE_URL.replace(/^http/, 'ws')
);

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: 'include',
    headers: {
      'Content-Type': 'application/json',
      ...options.headers
    }
  });
  if (response.status === 401) {
    window.dispatchEvent(new CustomEvent('auth:expired'));
  }
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    const message = typeof body.detail === 'string' ? body.detail : body.detail?.message ?? response.statusText;
    throw new Error(message);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  me: () => request<User>('/auth/me'),
  providers: () => request<AuthProviders>('/auth/providers'),
  logout: () => request<{ ok: boolean }>('/auth/logout', { method: 'POST' }),
  loginUrl: (provider: 'google' | 'github') => `${API_BASE_URL}/auth/${provider}/login`,
  testLogin: () =>
    request<User>('/auth/test-login', {
      method: 'POST',
      body: JSON.stringify({
        provider: 'github',
        provider_user_id: 'local-demo',
        email: 'demo@example.com',
        display_name: 'Demo User'
      })
    }),
  lists: () => request<ProjectList[]>('/api/lists'),
  createList: (name: string) =>
    request<ProjectList>('/api/lists', { method: 'POST', body: JSON.stringify({ name }) }),
  renameList: (id: string, name: string) =>
    request<ProjectList>(`/api/lists/${id}`, { method: 'PATCH', body: JSON.stringify({ name }) }),
  deleteList: (id: string) => request<{ ok: boolean; deleted_tasks: number }>(`/api/lists/${id}`, { method: 'DELETE' }),
  tasks: (listId: string, filters: TaskFilters) => {
    const params = new URLSearchParams({ list_id: listId, due: filters.due });
    if (filters.search.trim()) params.set('search', filters.search.trim());
    if (filters.status) params.set('status', filters.status);
    if (filters.priority) params.set('priority', filters.priority);
    return request<Task[]>(`/api/tasks?${params}`);
  },
  createTask: (task: {
    list_id: string;
    title: string;
    description: string;
    status: TaskStatus;
    priority: TaskPriority;
    due_date: string | null;
  }) => request<Task>('/api/tasks', { method: 'POST', body: JSON.stringify(task) }),
  updateTask: (id: string, task: Partial<Task>) =>
    request<Task>(`/api/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(task) }),
  updateTaskStatus: (id: string, status: TaskStatus) =>
    request<Task>(`/api/tasks/${id}/status`, { method: 'PATCH', body: JSON.stringify({ status }) }),
  deleteTask: (id: string) => request<{ ok: boolean }>(`/api/tasks/${id}`, { method: 'DELETE' }),
  taskHistory: (taskId: string) => request<TaskHistoryEntry[]>(`/api/tasks/${taskId}/history`)
};
