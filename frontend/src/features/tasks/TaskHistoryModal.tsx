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
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between mb-4">
          <div>
            <p className="text-sm font-semibold text-gray-900">{entry.changed_by_name}</p>
            <p className="text-xs text-gray-400">{new Date(entry.created_at).toLocaleString()}</p>
          </div>
          <button
            aria-label="Close"
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl leading-none"
          >
            ×
          </button>
        </div>
        <table className="w-full text-sm border-collapse">
          <thead>
            <tr className="text-left text-xs text-gray-500 uppercase">
              <th className="pb-2 pr-3 font-medium">Field</th>
              <th className="pb-2 pr-3 font-medium">Was</th>
              <th className="pb-2 font-medium">Became</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {entry.fields.map((f, i) => (
              <tr key={i}>
                <td className="py-1.5 pr-3 font-medium text-gray-700">{f.field_name}</td>
                <td className="py-1.5 pr-3 text-gray-500">{f.old_value ?? '—'}</td>
                <td className="py-1.5 text-gray-900">{f.new_value ?? '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
