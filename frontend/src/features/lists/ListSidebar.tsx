import { LogOut, Plus, Trash2, X } from 'lucide-react';
import { useState } from 'react';

import { api } from '../../api/client';
import type { ProjectList, User } from '../../types/domain';

interface Props {
  user: User | null;
  lists: ProjectList[];
  selectedListId: string | null;
  loading: boolean;
  open: boolean;
  onClose: () => void;
  onSelect: (id: string) => void;
  onChanged: () => Promise<void>;
  onLogout: () => Promise<void>;
}

export function ListSidebar({
  user,
  lists,
  selectedListId,
  loading,
  open,
  onClose,
  onSelect,
  onChanged,
  onLogout
}: Props) {
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingName, setEditingName] = useState('');

  async function createList() {
    const nextName = name.trim();
    if (!nextName) {
      setError('List name is required');
      return;
    }
    setError(null);
    await api.createList(nextName);
    setName('');
    await onChanged();
  }

  async function renameList(id: string) {
    const nextName = editingName.trim();
    if (!nextName) {
      setError('List name is required');
      return;
    }
    await api.renameList(id, nextName);
    setEditingId(null);
    setEditingName('');
    await onChanged();
  }

  async function deleteList(list: ProjectList) {
    const confirmed = window.confirm(
      `Delete "${list.name}" and all ${list.task_count} task(s) in it? This cannot be undone.`
    );
    if (!confirmed) return;
    await api.deleteList(list.id);
    await onChanged();
  }

  return (
    <>
      {open ? <button className="sidebar-backdrop" type="button" aria-label="Close lists" onClick={onClose} /> : null}
      <aside className={`sidebar ${open ? 'open' : ''}`}>
        <div className="sidebar-header">
          <div>
            <div className="eyebrow">Workspace</div>
            <strong>{user?.display_name ?? 'User'}</strong>
          </div>
          <button className="icon-button sidebar-close" type="button" onClick={onClose} aria-label="Close lists">
            <X size={18} />
          </button>
        </div>

        <form
          className="create-list"
          onSubmit={(event) => {
            event.preventDefault();
            void createList();
          }}
        >
          <input value={name} onChange={(event) => setName(event.target.value)} placeholder="New list" maxLength={100} />
          <button className="icon-button primary" type="submit" aria-label="Create list">
            <Plus size={18} />
          </button>
        </form>
        {error ? <div className="field-error">{error}</div> : null}

        <nav className="list-nav" aria-label="Project lists">
          {loading ? <div className="muted">Loading lists...</div> : null}
          {!loading && lists.length === 0 ? <div className="empty-state">No lists yet. Create one to start planning.</div> : null}
          {lists.map((list) => (
            <div className={`list-item ${list.id === selectedListId ? 'selected' : ''}`} key={list.id}>
              {editingId === list.id ? (
                <form
                  className="rename-form"
                  onSubmit={(event) => {
                    event.preventDefault();
                    void renameList(list.id);
                  }}
                >
                  <input value={editingName} onChange={(event) => setEditingName(event.target.value)} autoFocus />
                  <button className="small-button" type="submit">Save</button>
                </form>
              ) : (
                <button className="list-select" type="button" onClick={() => onSelect(list.id)}>
                  <span>{list.name}</span>
                  <small>{list.open_task_count}/{list.task_count}</small>
                </button>
              )}
              <div className="list-actions">
                <button
                  className="text-button"
                  type="button"
                  onClick={() => {
                    setEditingId(list.id);
                    setEditingName(list.name);
                  }}
                >
                  Rename
                </button>
                <button className="icon-button danger" type="button" aria-label={`Delete ${list.name}`} onClick={() => void deleteList(list)}>
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </nav>

        <button className="logout-button" type="button" onClick={() => void onLogout()}>
          <LogOut size={18} />
          Logout
        </button>
      </aside>
    </>
  );
}

