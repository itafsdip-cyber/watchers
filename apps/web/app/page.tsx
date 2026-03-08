import { DashboardClient } from '@/components/DashboardClient';
import { getIncidents } from '@/lib/api';
import { Incident } from '@/lib/types';

export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
  let incidents: Incident[] = [];
  let apiError: string | null = null;

  try {
    incidents = await getIncidents();
  } catch {
    apiError = 'Unable to reach API. Start backend service and seed data.';
  }

  return (
    <main className="mx-auto max-w-7xl px-4 py-8 md:px-8">
      {apiError ? (
        <p className="mt-6 rounded-xl border border-danger/40 bg-danger/10 p-4 text-sm text-rose-100">{apiError}</p>
      ) : <DashboardClient initialIncidents={incidents} />}
    </main>
  );
}
