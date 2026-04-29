export type TaskStatus = 'todo' | 'in_progress' | 'done';
export type TaskPriority = 'low' | 'medium' | 'high';
export type DueFilter = 'overdue' | 'today' | 'next_7_days' | 'all';

export interface User {
  id: string;
  email: string | null;
  display_name: string;
  avatar_url: string | null;
}

export interface AuthProviders {
  google: boolean;
  github: boolean;
  test_auth: boolean;
}

export interface ProjectList {
  id: string;
  name: string;
  task_count: number;
  open_task_count: number;
  created_at: string;
  updated_at: string;
}

export interface Task {
  id: string;
  list_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
}

export interface TaskFilters {
  search: string;
  status: TaskStatus | '';
  priority: TaskPriority | '';
  due: DueFilter;
}

export interface NotificationItem {
  id: string;
  type: 'overdue' | 'due_soon';
  task_id: string;
  list_id: string;
  title: string;
  due_date: string | null;
  priority: TaskPriority;
  message: string;
}
