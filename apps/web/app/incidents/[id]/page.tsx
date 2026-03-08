import Link from "next/link";
import { notFound } from "next/navigation";

import { CredibilityBadge } from "@/components/CredibilityBadge";
import { Timeline } from "@/components/Timeline";
import { getIncident, getIncidentCredibility } from "@/lib/api";

type PageProps = {
  params: {
    id: string;
  };
};

export default async function IncidentDetailPage({ params }: PageProps) {
  const id = Number(params.id);

  if (Number.isNaN(id)) {
    notFound();
  }

  try {
    const [incident, credibility] = await Promise.all([
      getIncident(id),
      getIncidentCredibility(id),
    ]);

    return (
      <main className="mx-auto max-w-5xl px-4 py-8 md:px-8">
        <Link href="/" className="text-sm text-accent hover:underline">
          ← Back to dashboard
        </Link>

        <section className="mt-6 rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl">
          <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
            <div>
              <p className="text-xs uppercase tracking-[0.3em] text-accent">
                Incident Detail
              </p>
              <h1 className="mt-2 text-3xl font-semibold text-white">
                {incident.title}
              </h1>
              <p className="mt-3 max-w-3xl text-sm text-slate-300">
                {incident.summary}
              </p>
            </div>

            <div className="flex flex-col gap-3">
              <CredibilityBadge
                status={incident.status}
                score={incident.credibility_score}
              />
              <div className="rounded-2xl border border-white/10 bg-slate-950/40 p-4 text-sm text-slate-300">
                <div>Occurred: {incident.occurred_at ?? "Unknown"}</div>
                <div>Updated: {incident.updated_at}</div>
                <div>
                  Coordinates:{" "}
                  {incident.latitude != null && incident.longitude != null
                    ? `${incident.latitude}, ${incident.longitude}`
                    : "Unknown"}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl">
            <h2 className="text-xl font-semibold text-white">
              Credibility Breakdown
            </h2>

            <div className="mt-4 space-y-3">
              {Object.entries(credibility.dimensions).map(([key, value]) => (
                <div key={key}>
                  <div className="mb-1 flex items-center justify-between text-sm text-slate-300">
                    <span className="capitalize">
                      {key.replace(/_/g, " ")}
                    </span>
                    <span>{Number(value).toFixed(3)}</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-800">
                    <div
                      className="h-2 rounded-full bg-emerald-400"
                      style={{ width: `${Math.max(0, Math.min(100, value * 100))}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-2xl border border-white/10 bg-slate-950/40 p-4">
              <h3 className="text-sm font-medium text-white">Scoring Notes</h3>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-300">
                {credibility.notes.map((note, index) => (
                  <li key={index}>{note}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="space-y-6">
            <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl">
              <h2 className="text-xl font-semibold text-white">Sources</h2>
              <div className="mt-4 space-y-3">
                {incident.sources.length > 0 ? (
                  incident.sources.map((source) => (
                    <div
                      key={source.id}
                      className="rounded-2xl border border-white/10 bg-slate-950/40 p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <div>
                          <p className="font-medium text-white">
                            {source.source_name}
                          </p>
                          <p className="text-xs uppercase tracking-wide text-slate-400">
                            {source.source_type}
                          </p>
                        </div>
                        <div className="text-sm text-slate-300">
                          {(source.reliability_score * 100).toFixed(0)}%
                        </div>
                      </div>

                      {source.source_url ? (
                        <a
                          href={source.source_url}
                          target="_blank"
                          rel="noreferrer"
                          className="mt-2 block text-sm text-accent hover:underline"
                        >
                          View source
                        </a>
                      ) : null}
                    </div>
                  ))
                ) : (
                  <p className="text-sm text-slate-400">No sources available.</p>
                )}
              </div>
            </div>

            <div className="rounded-3xl border border-white/10 bg-white/5 p-6 shadow-2xl">
              <h2 className="text-xl font-semibold text-white">Timeline</h2>
              <div className="mt-4">
                <Timeline entries={incident.timeline_entries} />
              </div>
            </div>
          </div>
        </section>
      </main>
    );
  } catch {
    notFound();
  }
}