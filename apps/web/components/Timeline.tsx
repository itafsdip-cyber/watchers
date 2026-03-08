import { IncidentTimelineEntry } from '@/lib/types';

export function Timeline({ entries }: { entries: IncidentTimelineEntry[] }) {
  if (entries.length === 0) {
    return <p className="text-sm text-mute">No timeline updates yet.</p>;
  }

  const sorted = [...entries].sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  );

  return (
    <ol className="space-y-3">
      {sorted.map((entry) => (
        <li key={entry.id} className="rounded-lg border border-white/10 bg-white/5 p-3">
          <p className="text-xs uppercase tracking-wide text-accent">{entry.event_type}</p>
          <p className="mt-1 text-sm text-ink">{entry.description}</p>
          <p className="mt-1 text-xs text-mute">{new Date(entry.timestamp).toLocaleString()}</p>
        </li>
      ))}
    </ol>
  );
}
