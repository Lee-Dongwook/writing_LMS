import type { CourseOverview } from '../../types'

interface Props {
  data?: CourseOverview
  loading: boolean
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="inline-flex w-16 shrink-0 justify-center rounded-md bg-brand-50 px-2 py-1 text-xs font-medium text-brand-700">
        {label}
      </span>
      <span className="text-slate-600">{value}</span>
    </div>
  )
}

export default function WelcomeCard({ data, loading }: Props) {
  if (loading || !data) {
    return <div className="h-48 animate-pulse rounded-2xl bg-white" />
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <p className="text-sm text-slate-400">안녕하세요, 이동욱님 👋</p>
      <h2 className="mt-1 text-lg font-bold text-slate-800">
        {data.title} {data.round}
      </h2>

      <div className="mt-4 space-y-2">
        <Row label="훈련기간" value={data.trainingPeriod} />
        <Row label="모집기간" value={data.examPeriod} />
        <Row label="훈련일수" value={data.totalHours} />
      </div>

      <p className="mt-5 border-t border-slate-100 pt-4 text-sm italic text-slate-400">
        “{data.quote}”
        <span className="ml-1 not-italic text-slate-300">- {data.quoteAuthor}</span>
      </p>
    </div>
  )
}
