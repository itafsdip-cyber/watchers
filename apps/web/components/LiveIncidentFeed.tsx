import Link from 'next/link';

import { Incident } from '@/lib/types';
import { CredibilityBadge } from './CredibilityBadge';

export function LiveIncidentFeed({ incidents }: { incidents: Incident[] }) {
  if (incidents.length === 0) {
    return <p className="text-sm text-mute">No incidents available. Seed data from API first.</p>;
  }

  return (
    <div className="space-y-3">
      {incidents.map((incident) => (
        <Link
          key={incident.id}
          href={`/incidents/${incident.id}`}
          className="block rounded-xl border border-white/10 bg-white/5 p-3 transition hover:border-accent/50 hover:bg-white/10"
        >
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-semibold text-ink">{incident.title}</h3>
            <CredibilityBadge status={incident.status} score={incident.credibility_score} />
          </div>
          <p className="mt-2 overflow-hidden text-sm text-mute">{incident.summary}</p>
          <p className="mt-2 text-xs text-mute">Updated {new Date(incident.updated_at).toLocaleString()}</p>
        </Link>
      ))}
    </div>
  );
}
