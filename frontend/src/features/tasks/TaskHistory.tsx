import { useEffect, useState } from 'react';
import { api } from '../../api/client';
import type { TaskHistoryEntry } from '../../types/domain';
import { TaskHistoryModal } from './TaskHistoryModal';

interface Props {
  taskId: string;
  onEntryClick: (entry: TaskHistoryEntry) => void;
}

export function TaskHistory({ taskId, onEntryClick }: Props) {
  const [entries, setEntries] = useState<TaskHistoryEntry[] | null>(null);
  const [selectedEntry, setSelectedEntry] = useState<TaskHistoryEntry | null>(null);

  useEffect(() => {
    api.taskHistory(taskId).then(setEntries).catch(() => setEntries([]));
  }, [taskId]);

  function handleEntryClick(entry: TaskHistoryEntry) {
    setSelectedEntry(entry);
    onEntryClick(entry);
  }

  if (entries === null) {
    return <div className="p-4 text-sm text-gray-500">Loading…</div>;
  }

  if (entries.length === 0) {
    return <div className="p-4 text-sm text-gray-500">No history yet.</div>;
  }

  return (
    <>
      <ul className="divide-y divide-gray-100">
        {entries.map((entry) => (
          <li
            key={entry.id}
            className="flex flex-col gap-0.5 px-4 py-3 cursor-pointer hover:bg-gray-50"
            onClick={() => handleEntryClick(entry)}
          >
            <span className="text-xs text-gray-400">
              {new Date(entry.created_at).toLocaleString()}
            </span>
            <span className="text-sm font-medium text-gray-700">{entry.changed_by_name}</span>
            <span className="text-xs text-gray-500">
              {entry.fields.map((f) => f.field_name).join(', ')}
            </span>
          </li>
        ))}
      </ul>
      {selectedEntry && (
        <TaskHistoryModal entry={selectedEntry} onClose={() => setSelectedEntry(null)} />
      )}
    </>
  );
}
