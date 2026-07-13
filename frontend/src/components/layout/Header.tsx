import { useUiStore, APP_ROLES } from '../../store/uiStore'
import { useCourseOverview } from '../../api/hooks'
import { useAuthStore } from '../../store/authStore'

export default function Header() {
  const { toggleSidebar, role, setRole } = useUiStore()
  const { data } = useCourseOverview()
  const user = useAuthStore((s) => s.user)
  const logout = useAuthStore((s) => s.logout)

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

      {/* 로그인 사용자 + 로그아웃 */}
      <div className="flex items-center gap-2 pl-1">
        <span className="hidden max-w-[9rem] truncate text-sm font-medium text-slate-600 sm:inline">
          {user?.name || user?.email}
        </span>
        <button
          onClick={logout}
          className="rounded-md px-2.5 py-1.5 text-xs font-medium text-slate-500 ring-1 ring-line hover:bg-slate-100"
        >
          로그아웃
        </button>
      </div>
    </header>
  )
}
