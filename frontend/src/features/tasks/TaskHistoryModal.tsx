import { useEffect } from 'react';
import type { TaskHistoryEntry } from '../../types/domain';

interface Props {
  entry: TaskHistoryEntry;
  onClose: () => void;
}

export function TaskHistoryModal({ entry, onClose }: Props) {
  useEffect(() => {
    function handler(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [onClose]);

  return (
    <div
      data-testid="modal-backdrop"
      className="history-modal-backdrop"
      onClick={onClose}
    >
      <div
        className="history-modal"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="history-modal-header">
          <div>
            <div className="history-modal-title">{entry.changed_by_name}</div>
            <div className="history-modal-subtitle">{new Date(entry.created_at).toLocaleString()}</div>
          </div>
          <button
            aria-label="Close"
            onClick={onClose}
          >
            ×
          </button>
        </div>
        <div className="history-table-wrapper">
          <table className="history-table">
            <thead className="history-table-head">
              <tr>
                <th>Field</th>
                <th>Was</th>
                <th>Became</th>
              </tr>
            </thead>
            <tbody className="history-table-body">
              {entry.fields.map((f, i) => (
                <tr key={i} className="history-table-row">
                  <td>{f.field_name}</td>
                  <td>{f.old_value ?? '—'}</td>
                  <td>{f.new_value ?? '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
