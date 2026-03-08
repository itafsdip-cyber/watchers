'use client';

import { useEffect, useMemo, useState } from 'react';

import { getIncidents, getIncidentStreamUrl } from '@/lib/api';
import { Incident } from '@/lib/types';
import { IncidentMap } from './IncidentMap';
import { LiveIncidentFeed } from './LiveIncidentFeed';

export function DashboardClient({ initialIncidents }: { initialIncidents: Incident[] }) {
  const [incidents, setIncidents] = useState<Incident[]>(initialIncidents);

  useEffect(() => {
    const eventSource = new EventSource(getIncidentStreamUrl());
    const refresh = async () => {
      const next = await getIncidents();
      setIncidents(next);
    };

    eventSource.addEventListener('incident_changed', () => {
      void refresh();
    });

    return () => {
      eventSource.close();
    };
  }, []);

  const geoIncidents = useMemo(() => incidents.filter((i) => i.latitude != null && i.longitude != null), [incidents]);
  const confirmedCount = useMemo(
    () => incidents.filter((i) => ['confirmed', 'officially_confirmed'].includes(i.status)).length,
    [incidents]
  );

  return (
    <>
      <section className="rounded-3xl border border-white/10 bg-panel/75 p-6 shadow-glow backdrop-blur">
        <p className="text-xs uppercase tracking-[0.24em] text-accent">Watchers</p>
        <h1 className="mt-2 [font-family:var(--font-heading)] text-3xl font-semibold md:text-4xl">Public Incident Intelligence</h1>
        <p className="mt-3 max-w-3xl text-sm text-mute">
          Local-first incident monitoring for public awareness. Scores are transparent and uncertainty is always visible.
        </p>

        <div className="mt-6 grid gap-3 md:grid-cols-3">
          <div className="rounded-xl border border-white/10 bg-white/5 p-3">
            <p className="text-xs uppercase tracking-wide text-mute">Active incidents</p>
            <p className="mt-1 text-2xl font-semibold">{incidents.length}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/5 p-3">
            <p className="text-xs uppercase tracking-wide text-mute">Geolocated</p>
            <p className="mt-1 text-2xl font-semibold">{geoIncidents.length}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-white/5 p-3">
            <p className="text-xs uppercase tracking-wide text-mute">Confirmed+</p>
            <p className="mt-1 text-2xl font-semibold">{confirmedCount}</p>
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-6 lg:grid-cols-[2fr_1fr]">
        <div className="rounded-2xl border border-white/10 bg-panel/80 p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="[font-family:var(--font-heading)] text-xl font-semibold">Incident Map</h2>
            <span className="text-xs uppercase tracking-wider text-mute">MapLibre GL</span>
          </div>
          <IncidentMap incidents={geoIncidents} />
        </div>

        <aside className="rounded-2xl border border-white/10 bg-panel/80 p-4">
          <h2 className="mb-3 [font-family:var(--font-heading)] text-xl font-semibold">Live Feed</h2>
          <LiveIncidentFeed incidents={incidents} />
        </aside>
      </section>
    </>
  );
}
