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
      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-xs text-gray-500 uppercase border-b border-gray-100">
            <th className="pb-2 pr-3 font-medium">When</th>
            <th className="pb-2 pr-3 font-medium">Changed By</th>
            <th className="pb-2 font-medium">Fields Changed</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {entries.map((entry) => (
            <tr
              key={entry.id}
              className="cursor-pointer hover:bg-gray-50"
              onClick={() => handleEntryClick(entry)}
            >
              <td className="py-3 pr-3 text-xs text-gray-400">
                {new Date(entry.created_at).toLocaleString()}
              </td>
              <td className="py-3 pr-3 text-sm font-medium text-gray-700">
                {entry.changed_by_name}
              </td>
              <td className="py-3 text-xs text-gray-500">
                {entry.fields.map((f) => f.field_name).join(', ')}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {selectedEntry && (
        <TaskHistoryModal entry={selectedEntry} onClose={() => setSelectedEntry(null)} />
      )}
    </>
  );
}
