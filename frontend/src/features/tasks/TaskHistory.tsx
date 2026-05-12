import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import type { TaskHistoryEntry } from '../../types/domain';

interface Props {
  taskId: string;
  onEntryClick: (entry: TaskHistoryEntry) => void;
}

export function TaskHistory({ taskId, onEntryClick }: Props) {
  const [entries, setEntries] = useState<TaskHistoryEntry[] | null>(null);

  useEffect(() => {
    api.taskHistory(taskId).then(setEntries).catch(() => setEntries([]));
  }, [taskId]);

  if (entries === null) {
    return <div className="p-4 text-sm text-gray-500">Loading…</div>;
  }

  if (entries.length === 0) {
    return <div className="p-4 text-sm text-gray-500">No history yet.</div>;
  }

  return (
    <div className="history-table-wrapper">
      <table className="history-table">
        <thead className="history-table-head">
          <tr>
            <th>When</th>
            <th>Changed By</th>
            <th>Fields Changed</th>
          </tr>
        </thead>
        <tbody className="history-table-body">
          {entries.map((entry) => (
            <tr
              key={entry.id}
              className="history-table-row"
              onClick={() => onEntryClick(entry)}
            >
              <td>{new Date(entry.created_at).toLocaleString()}</td>
              <td>{entry.changed_by_name}</td>
              <td>{entry.fields.map((f) => f.field_name).join(', ')}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
