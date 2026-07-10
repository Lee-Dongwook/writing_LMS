import type { ScheduleItem } from '../../types'

interface Props {
  items?: ScheduleItem[]
  loading: boolean
}

export default function ScheduleList({ items, loading }: Props) {
  return (
    <div className="w-full lg:w-56 lg:shrink-0 lg:border-l lg:border-slate-100 lg:pl-6">
      <h4 className="mb-3 text-sm font-semibold text-slate-700">주요 학습일정</h4>
      {loading || !items ? (
        <div className="h-10 animate-pulse rounded bg-slate-100" />
      ) : items.length === 0 ? (
        <p className="text-xs text-slate-400">등록된 일정이 없습니다.</p>
      ) : (
        <ul className="space-y-2">
          {items.map((s) => (
            <li
              key={s.id}
              className="flex items-center gap-2 rounded-lg bg-rose-50/60 px-3 py-2 text-sm"
            >
              <span className="font-mono text-xs font-medium text-rose-500">{s.date}</span>
              <span className="text-slate-600">{s.title}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
