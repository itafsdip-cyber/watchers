import { DashboardClient } from '@/components/DashboardClient';
import { getIncidents, getIngestionStats } from '@/lib/api';
import { Incident, IngestionStats } from '@/lib/types';

export const dynamic = 'force-dynamic';

const EMPTY_INGESTION_STATS: IngestionStats = {
  total_incidents: 0,
  incidents_created_today: 0,
  duplicate_claims_merged_today: 0,
  latest_ingest_run_timestamp: null
};

export default async function DashboardPage() {
  let incidents: Incident[] = [];
  let ingestionStats: IngestionStats = EMPTY_INGESTION_STATS;
  let apiError: string | null = null;

  try {
    [incidents, ingestionStats] = await Promise.all([getIncidents(), getIngestionStats()]);
  } catch {
    apiError = 'Unable to reach API. Start backend service and seed data.';
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 md:px-8">
      {apiError ? (
        <p className="mt-6 rounded-xl border border-danger/40 bg-danger/10 p-4 text-sm text-rose-100">{apiError}</p>
      ) : (
        <DashboardClient initialIncidents={incidents} initialIngestionStats={ingestionStats} />
      )}
    </main>
  );
}
