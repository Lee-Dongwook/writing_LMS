import { useUiStore } from '../../store/uiStore'
import type { ActiveView } from '../../store/uiStore'

const NAV: { view: ActiveView; icon: string; label: string }[] = [
  { view: 'dashboard', icon: '🖥️', label: '나의 강의실' },
  { view: 'attendance', icon: '📋', label: '출석 관리' },
  { view: 'grades', icon: '📊', label: '성적 · 평가' },
  { view: 'assignments', icon: '📝', label: '과제 · 오답노트' },
]

const FOOTER_LINKS = ['서비스이용약관', '개인정보처리방침', '마케팅이용약관']

export default function Sidebar() {
  const { sidebarOpen, activeView, setActiveView } = useUiStore()

  return (
    <aside
      className={`${
        sidebarOpen ? 'w-64' : 'w-0'
      } hidden shrink-0 overflow-hidden border-r border-line bg-white transition-all duration-200 lg:flex lg:flex-col`}
    >
      {/* 프로필 */}
      <div className="flex items-center gap-3 px-5 py-5">
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-50 text-lg">
          🧑
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-1 text-sm font-semibold text-ink">
            이동욱
            <span className="text-slate-400">✎</span>
          </div>
          <div className="truncate text-xs text-slate-400">dlehddnr0713@gmail.com</div>
        </div>
      </div>

      {/* 네비게이션 */}
      <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 pb-4 thin-scroll">
        {NAV.map((item) => {
          const active = activeView === item.view
          return (
            <button
              key={item.view}
              onClick={() => setActiveView(item.view)}
              className={`flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-sm font-semibold transition-colors ${
                active ? 'bg-brand-50 text-brand-700' : 'text-slate-600 hover:bg-surface'
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </button>
          )
        })}
      </nav>

      {/* 푸터 */}
      <div className="px-5 py-4 text-[11px] text-slate-400">
        <ul className="mb-3 space-y-1">
          {FOOTER_LINKS.map((link) => (
            <li key={link}>
              <a href="#" className="hover:text-slate-600">
                {link}
              </a>
            </li>
          ))}
        </ul>
        <p className="leading-relaxed">
          Copyright 2024-2026 국풍2000 용죽 국어관.
          <br />
          all rights reserved
        </p>
      </div>
    </aside>
  )
}
