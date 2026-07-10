import { useUiStore, APP_ROLES } from '../../store/uiStore'
import { useCourseOverview } from '../../api/hooks'

export default function Header() {
  const { toggleSidebar, role, setRole } = useUiStore()
  const { data } = useCourseOverview()

  const title = data ? `${data.title} ${data.round}` : '강의실'

  return (
    <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-slate-200 bg-white px-4 sm:px-6">
      <button
        onClick={toggleSidebar}
        aria-label="사이드바 토글"
        className="hidden rounded-md p-2 text-slate-500 hover:bg-slate-100 lg:block"
      >
        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M2 4.75A.75.75 0 012.75 4h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 4.75zm0 5A.75.75 0 012.75 9h14.5a.75.75 0 010 1.5H2.75A.75.75 0 012 9.75zm0 5a.75.75 0 01.75-.75h14.5a.75.75 0 010 1.5H2.75a.75.75 0 01-.75-.75z"
            clipRule="evenodd"
          />
        </svg>
      </button>

      <h1 className="flex-1 truncate text-base font-semibold text-slate-800">{title}</h1>

      {/* 데모용 역할 전환 토글 (원장/학생/학부모) */}
      <div
        className="flex items-center rounded-lg bg-slate-100 p-0.5"
        role="group"
        aria-label="역할 전환"
      >
        {APP_ROLES.map((r) => (
          <button
            key={r.value}
            onClick={() => setRole(r.value)}
            aria-pressed={role === r.value}
            className={`flex items-center gap-1 rounded-md px-2.5 py-1.5 text-xs font-medium transition-colors sm:px-3 ${
              role === r.value
                ? 'bg-white text-brand-700 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <span>{r.emoji}</span>
            <span className="hidden sm:inline">{r.label}</span>
          </button>
        ))}
      </div>

      <button className="rounded-md p-2 text-slate-400 hover:bg-slate-100" aria-label="펼치기">
        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
          <path
            fillRule="evenodd"
            d="M5.23 7.21a.75.75 0 011.06.02L10 11.17l3.71-3.94a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
            clipRule="evenodd"
          />
        </svg>
      </button>
    </header>
  )
}
