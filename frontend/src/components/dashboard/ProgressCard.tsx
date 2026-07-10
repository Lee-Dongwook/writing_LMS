interface Props {
  title: string
  percent: number
  count: string
  loading: boolean
}

function Ring({ percent }: { percent: number }) {
  const r = 46
  const c = 2 * Math.PI * r
  const offset = c - (percent / 100) * c

  return (
    <svg viewBox="0 0 120 120" className="h-32 w-32 -rotate-90">
      <circle cx="60" cy="60" r={r} fill="none" stroke="#eef0f4" strokeWidth="12" />
      <circle
        cx="60"
        cy="60"
        r={r}
        fill="none"
        stroke="#6567d4"
        strokeWidth="12"
        strokeLinecap="round"
        strokeDasharray={c}
        strokeDashoffset={offset}
        className="transition-all duration-700"
      />
    </svg>
  )
}

export default function ProgressCard({ title, percent, count, loading }: Props) {
  if (loading) {
    return <div className="h-48 animate-pulse rounded-2xl bg-white" />
  }

  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      <div className="relative mt-2 flex flex-1 items-center justify-center">
        <Ring percent={percent} />
        <div className="absolute flex flex-col items-center">
          <span className="text-xl font-bold text-brand-600">{percent}%</span>
          <span className="text-xs text-slate-400">{count}</span>
        </div>
      </div>
    </div>
  )
}
