import { useUiStore } from '../store/uiStore'
import { useOnlineUsers } from '../api/hooks'
import type { UserRole } from '../types'

const ROLE_COLOR: Record<UserRole, string> = {
  수강생: 'text-slate-400',
  강사: 'text-brand-600',
  매니저: 'text-emerald-600',
}

export default function OnlineUsersModal() {
  const { onlineModalOpen, closeOnlineModal } = useUiStore()
  const { data, isLoading } = useOnlineUsers(onlineModalOpen)

  if (!onlineModalOpen) return null

  const count = data?.length ?? 0

  return (
    <div
      className="fixed inset-0 z-40 flex items-start justify-center bg-slate-900/30 p-4 pt-24 sm:justify-end sm:pr-8"
      onClick={closeOnlineModal}
    >
      <div
        className="flex max-h-[70vh] w-full max-w-sm flex-col overflow-hidden rounded-2xl bg-white shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between bg-brand-500 px-5 py-4 text-white">
          <h3 className="text-base font-semibold">현재 접속자 리스트 ({count})</h3>
          <button
            onClick={closeOnlineModal}
            aria-label="닫기"
            className="rounded-md p-1 hover:bg-white/20"
          >
            <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto thin-scroll">
          {isLoading ? (
            <div className="space-y-3 p-5">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-8 animate-pulse rounded bg-slate-100" />
              ))}
            </div>
          ) : (
            <ul className="divide-y divide-slate-100">
              {data?.map((u) => (
                <li key={u.id} className="flex items-center gap-3 px-5 py-3.5">
                  <span className="text-xl">{u.emoji}</span>
                  <span className="font-medium text-slate-700">{u.name}</span>
                  <span className={`text-sm ${ROLE_COLOR[u.role]}`}>[{u.role}]</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  )
}
