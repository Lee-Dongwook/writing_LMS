import { useUiStore } from '../../store/uiStore'

const CLASSROOM_ITEMS = [
  '클래스룸',
  '사전학습/컨텐츠',
  '사전평가',
  '설문조사',
  '평가(과제) 제출 & 피드백',
  '스터디룸',
  '학습퀴즈',
]

const FOOTER_LINKS = ['서비스이용약관', '개인정보처리방침', '마케팅이용약관']

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      className={`h-4 w-4 shrink-0 text-slate-400 transition-transform ${open ? 'rotate-180' : ''}`}
      viewBox="0 0 20 20"
      fill="currentColor"
    >
      <path
        fillRule="evenodd"
        d="M5.23 7.21a.75.75 0 011.06.02L10 11.17l3.71-3.94a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
        clipRule="evenodd"
      />
    </svg>
  )
}

export default function Sidebar() {
  const { sidebarOpen, classroomExpanded, toggleClassroom } = useUiStore()

  return (
    <aside
      className={`${
        sidebarOpen ? 'w-64' : 'w-0'
      } hidden shrink-0 overflow-hidden border-r border-slate-200 bg-white transition-all duration-200 lg:flex lg:flex-col`}
    >
      {/* 프로필 */}
      <div className="flex items-center gap-3 px-5 py-5">
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-100 text-lg">
          🧑
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-1 text-sm font-semibold text-slate-800">
            이동욱
            <span className="text-slate-400">✎</span>
          </div>
          <div className="truncate text-xs text-slate-400">dlehddnr0713@gmail.com</div>
        </div>
      </div>

      {/* 네비게이션 */}
      <nav className="flex-1 overflow-y-auto px-3 pb-4 thin-scroll">
        <button
          onClick={toggleClassroom}
          className="flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm font-semibold text-brand-700"
        >
          <span className="flex items-center gap-2">
            <span className="text-base">🖥️</span>
            나의 강의실
          </span>
          <ChevronIcon open={classroomExpanded} />
        </button>

        {classroomExpanded && (
          <ul className="mb-2 space-y-0.5 pl-2">
            {CLASSROOM_ITEMS.map((item, i) => (
              <li key={item}>
                <a
                  href="#"
                  className={`block rounded-lg px-4 py-2 text-sm transition-colors ${
                    i === 0
                      ? 'bg-brand-50 font-medium text-brand-700'
                      : 'text-slate-500 hover:bg-slate-50'
                  }`}
                >
                  {item}
                </a>
              </li>
            ))}
          </ul>
        )}

        <button className="flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50">
          <span className="flex items-center gap-2">
            <span className="text-base">🎧</span>
            학습지원센터
          </span>
          <ChevronIcon open={false} />
        </button>
      </nav>

      {/* 푸터 */}
      <div className="border-t border-slate-100 px-5 py-4 text-[11px] text-slate-400">
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
          Copyright 2024-2026 FLOW-UP. all
          <br />
          rights reserved
        </p>
      </div>
    </aside>
  )
}
