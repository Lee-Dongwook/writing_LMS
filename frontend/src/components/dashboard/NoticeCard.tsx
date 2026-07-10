import type { Notice } from '../../types'

interface Props {
  notices?: Notice[]
  loading: boolean
}

export default function NoticeCard({ notices, loading }: Props) {
  return (
    <div className="flex flex-col rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-slate-700">공지사항</h3>
        <a href="#" className="text-xs text-slate-400 hover:text-brand-600">
          더보기
        </a>
      </div>

      {loading || !notices ? (
        <div className="space-y-2">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="h-6 animate-pulse rounded bg-slate-100" />
          ))}
        </div>
      ) : (
        <ul className="space-y-2.5">
          {notices.map((n) => (
            <li key={n.id} className="flex items-center gap-2 text-sm">
              <span className="text-brand-400">📢</span>
              <span className="flex-1 truncate text-slate-600">
                <span className="text-slate-400">[{n.tag}]</span> {n.title}
              </span>
              <span className="shrink-0 text-xs text-slate-400">{n.author}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
