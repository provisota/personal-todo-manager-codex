import { Bell, Check, TriangleAlert } from 'lucide-react';

import type { NotificationItem } from '../../types/domain';

interface Props {
  connected: boolean;
  items: NotificationItem[];
  onAck: (id: string) => void;
  onNavigate: (listId: string, taskId: string) => void;
}

export function NotificationPanel({ connected, items, onAck, onNavigate }: Props) {
  return (
    <aside className="notification-panel" aria-label="Task notifications">
      <header>
        <div>
          <div className="eyebrow">Notifications</div>
          <strong>{connected ? 'Connected' : 'Reconnecting'}</strong>
        </div>
        <Bell size={20} />
      </header>
      {items.length === 0 ? <p className="muted">No urgent task notifications.</p> : null}
      <div className="notification-list">
        {items.map((item) => (
          <article className={`notification ${item.type}`} key={item.id}>
            <button
              className="notification-body"
              type="button"
              onClick={() => onNavigate(item.list_id, item.task_id)}
            >
              <TriangleAlert size={18} />
              <span>
                <strong>{item.title}</strong>
                <small>{item.message}{item.due_date ? ` - due ${item.due_date}` : ''}</small>
              </span>
            </button>
            <button className="icon-button" type="button" aria-label={`Acknowledge ${item.title}`} onClick={() => onAck(item.id)}>
              <Check size={16} />
            </button>
          </article>
        ))}
      </div>
    </aside>
  );
}
