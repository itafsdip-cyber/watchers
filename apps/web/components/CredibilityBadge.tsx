type Props = {
  status: string;
  score: number;
};

const STATUS_CLASS: Record<string, string> = {
  noise: 'bg-slate-700/40 text-slate-200 border-slate-500/40',
  rumor: 'bg-orange-500/15 text-orange-200 border-orange-400/40',
  developing: 'bg-cyan-500/15 text-cyan-200 border-cyan-400/40',
  likely: 'bg-emerald-500/15 text-emerald-200 border-emerald-400/40',
  credible: 'bg-emerald-500/20 text-emerald-100 border-emerald-300/50',
  confirmed: 'bg-blue-500/20 text-blue-100 border-blue-300/50',
  officially_confirmed: 'bg-green-500/25 text-green-50 border-green-200/70',
  disputed: 'bg-amber-500/20 text-amber-100 border-amber-300/50',
  false: 'bg-rose-500/20 text-rose-100 border-rose-300/50'
};

export function CredibilityBadge({ status, score }: Props) {
  const label = status.replaceAll('_', ' ');
  const cls = STATUS_CLASS[status] ?? 'bg-slate-700/40 text-slate-100 border-slate-500/40';

  return (
    <div className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs uppercase tracking-wide ${cls}`}>
      <span>{label}</span>
      <span className="font-semibold">{Math.round(score * 100)}%</span>
    </div>
  );
}
