import { useCallback, useEffect, useMemo, useState } from 'react';
import { Menu } from 'lucide-react';

import { api } from '../api/client';
import { useAuth } from '../auth/AuthContext';
import { NotificationPanel } from '../features/notifications/NotificationPanel';
import { ListSidebar } from '../features/lists/ListSidebar';
import { TaskBoard } from '../features/tasks/TaskBoard';
import { useNotificationsSocket } from '../hooks/useNotificationsSocket';
import type { ProjectList } from '../types/domain';

export function TodoAppPage() {
  const { user, logout } = useAuth();
  const [lists, setLists] = useState<ProjectList[]>([]);
  const [selectedListId, setSelectedListId] = useState<string | null>(() => localStorage.getItem('selected-list-id'));
  const [loadingLists, setLoadingLists] = useState(true);
  const [listsLoaded, setListsLoaded] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const notifications = useNotificationsSocket(Boolean(user && listsLoaded));

  const selectedList = useMemo(
    () => lists.find((item) => item.id === selectedListId) ?? lists[0] ?? null,
    [lists, selectedListId]
  );

  const loadLists = useCallback(async () => {
    setLoadingLists(true);
    try {
      const result = await api.lists();
      setLists(result);
      setListsLoaded(true);
      if (result.length && (!selectedListId || !result.some((item) => item.id === selectedListId))) {
        setSelectedListId(result[0].id);
        localStorage.setItem('selected-list-id', result[0].id);
      }
      if (!result.length) {
        setSelectedListId(null);
        localStorage.removeItem('selected-list-id');
      }
    } catch (err) {
      setListsLoaded(false);
      throw err;
    } finally {
      setLoadingLists(false);
    }
  }, [selectedListId]);

  useEffect(() => {
    void loadLists();
  }, [loadLists]);

  const selectList = (id: string) => {
    setSelectedListId(id);
    localStorage.setItem('selected-list-id', id);
    setSidebarOpen(false);
  };

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
      <TaskBoard lists={lists} selectedList={selectedList} onTasksChanged={loadLists} />
      <NotificationPanel
        connected={notifications.connected}
        items={notifications.items}
        onAck={notifications.ack}
        onNavigate={(listId) => selectList(listId)}
      />
    </main>
  );
}
