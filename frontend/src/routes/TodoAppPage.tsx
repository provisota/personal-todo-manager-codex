import { useCallback, useEffect, useMemo, useState } from 'react';
import { Menu } from 'lucide-react';
import { useNavigate, useParams } from 'react-router-dom';

import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { NotificationPanel } from '../features/notifications/NotificationPanel';
import { ListSidebar } from '../features/lists/ListSidebar';
import { TaskBoard } from '../features/tasks/TaskBoard';
import { useNotificationsSocket } from '../hooks/useNotificationsSocket';
import type { ProjectList } from '../types/domain';

export function TodoAppPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { listId } = useParams();
  const [lists, setLists] = useState<ProjectList[]>([]);
  const [selectedListId, setSelectedListId] = useState<string | null>(
    () => listId ?? localStorage.getItem('selected-list-id')
  );
  const [focusedTaskId, setFocusedTaskId] = useState<string | null>(null);
  const [loadingLists, setLoadingLists] = useState(true);
  const [listsLoaded, setListsLoaded] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const notifications = useNotificationsSocket(Boolean(user && listsLoaded));

  const selectedList = useMemo(
    () => lists.find((item) => item.id === selectedListId) ?? lists[0] ?? null,
    [lists, selectedListId]
  );

  useEffect(() => {
    if (listId) {
      setSelectedListId(listId);
      localStorage.setItem('selected-list-id', listId);
    }
  }, [listId]);

  const loadLists = useCallback(async () => {
    setLoadingLists(true);
    try {
      const result = await api.lists();
      setLists(result);
      setListsLoaded(true);
      const requestedListId = listId ?? selectedListId;
      if (result.length) {
        const nextListId =
          requestedListId && result.some((item) => item.id === requestedListId)
            ? requestedListId
            : result[0].id;
        setSelectedListId(nextListId);
        localStorage.setItem('selected-list-id', nextListId);
        if (listId !== nextListId) {
          navigate(`/app/lists/${nextListId}`, { replace: !listId });
        }
      }
      if (!result.length) {
        setSelectedListId(null);
        localStorage.removeItem('selected-list-id');
        if (listId) {
          navigate('/app', { replace: true });
        }
      }
    } catch (err) {
      setListsLoaded(false);
      throw err;
    } finally {
      setLoadingLists(false);
    }
  }, [listId, navigate, selectedListId]);

  useEffect(() => {
    void loadLists();
  }, [loadLists]);

  const selectList = (id: string) => {
    setSelectedListId(id);
    localStorage.setItem('selected-list-id', id);
    setSidebarOpen(false);
    navigate(`/app/lists/${id}`);
  };

  const navigateToNotification = (listId: string, taskId: string) => {
    setFocusedTaskId(taskId);
    selectList(listId);
  };

  const clearFocusedTask = useCallback(() => {
    setFocusedTaskId(null);
  }, []);

  return (
    <main className="app-shell">
      <button className="icon-button mobile-menu" type="button" onClick={() => setSidebarOpen(true)} aria-label="Open lists">
        <Menu size={20} />
      </button>
      <ListSidebar
        user={user}
        lists={lists}
        selectedListId={selectedList?.id ?? null}
        loading={loadingLists}
        open={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
        onSelect={selectList}
        onChanged={loadLists}
        onLogout={logout}
      />
      <TaskBoard
        lists={lists}
        selectedList={selectedList}
        focusedTaskId={focusedTaskId}
        onFocusHandled={clearFocusedTask}
        onTasksChanged={loadLists}
      />
      <NotificationPanel
        connected={notifications.connected}
        items={notifications.items}
        onAck={notifications.ack}
        onNavigate={navigateToNotification}
      />
    </main>
  );
}
