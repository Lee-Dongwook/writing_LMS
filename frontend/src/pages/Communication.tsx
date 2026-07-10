import { useState } from 'react'
import { useAnnouncements, useCounselLogs } from '../api/hooks'
import { useUiStore } from '../store/uiStore'
import type { Announcement, CounselLog } from '../types'

type Tab = 'notices' | 'counsel'

// ── 공지 · 알림장 ──────────────────────────────────
function AnnouncementItem({ a }: { a: Announcement }) {
  return (
    <li className="px-6 py-4">
      <div className="flex flex-wrap items-center gap-2">
        {a.pinned && <span className="text-brand-600">📌</span>}
        <span
          className={`rounded px-2 py-0.5 text-xs font-medium ${
            a.category === '공지'
              ? 'bg-brand-50 text-brand-700'
              : 'bg-amber-50 text-amber-600'
          }`}
        >
          {a.category}
        </span>
        <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
          {a.scope}
        </span>
        <span className="font-medium text-slate-800">{a.title}</span>
        <span className="ml-auto text-xs text-slate-400">
          {a.author} · {a.date.slice(5).replace('-', '.')}
        </span>
      </div>
      <p className="mt-1.5 text-sm text-slate-500">{a.body}</p>
    </li>
  )
}

function NoticesTab({ items }: { items: Announcement[] }) {
  const scopes = ['전체', ...Array.from(new Set(items.map((a) => a.scope))).filter((s) => s !== '전체')]
  const [scope, setScope] = useState('전체')

  // '전체' 필터는 모든 항목, 특정 반 선택 시 그 반 + 전체 공지 노출
  const filtered =
    scope === '전체' ? items : items.filter((a) => a.scope === scope || a.scope === '전체')
  const sorted = [...filtered].sort((a, b) => Number(b.pinned) - Number(a.pinned))

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {scopes.map((s) => (
          <button
            key={s}
            onClick={() => setScope(s)}
            className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
              scope === s
                ? 'bg-brand-600 text-white'
                : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <ul className="divide-y divide-slate-100">
          {sorted.map((a) => (
            <AnnouncementItem key={a.id} a={a} />
          ))}
        </ul>
      </div>
    </div>
  )
}

// ── 상담일지 (원장 전용) ────────────────────────────
function CounselTab({ items }: { items: CounselLog[] }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <ul className="divide-y divide-slate-100">
        {items.map((c) => (
          <li key={c.id} className="px-6 py-4">
            <div className="flex flex-wrap items-center gap-2">
              <span
                className={`rounded px-2 py-0.5 text-xs font-medium ${
                  c.type === '학부모'
                    ? 'bg-sky-50 text-sky-600'
                    : 'bg-violet-50 text-violet-600'
                }`}
              >
                {c.type} 상담
              </span>
              <span className="font-medium text-slate-800">{c.student}</span>
              <span className="text-xs text-slate-400">· {c.counselor}</span>
              <span className="ml-auto flex items-center gap-2 text-xs text-slate-400">
                {c.shared ? (
                  <span className="rounded bg-emerald-50 px-1.5 py-0.5 font-medium text-emerald-600">
                    공유됨
                  </span>
                ) : (
                  <span className="rounded bg-slate-100 px-1.5 py-0.5 text-slate-400">
                    비공개
                  </span>
                )}
                {c.date.slice(5).replace('-', '.')}
              </span>
            </div>
            <p className="mt-1.5 text-sm text-slate-500">{c.summary}</p>
          </li>
        ))}
      </ul>
    </div>
  )
}

export default function Communication() {
  const role = useUiStore((s) => s.role)
  const announcements = useAnnouncements()
  const counsel = useCounselLogs()
  const [tab, setTab] = useState<Tab>('notices')

  // 상담일지는 스태프(원장) 전용
  const canSeeCounsel = role === 'director'
  const activeTab = !canSeeCounsel ? 'notices' : tab

  return (
    <div className="mx-auto max-w-4xl space-y-5 p-4 sm:p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-bold text-slate-800">알림 · 소통</h2>
        {role === 'director' && (
          <button className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-brand-700">
            {activeTab === 'counsel' ? '+ 상담 기록' : '+ 공지 작성'}
          </button>
        )}
      </div>

      {/* 탭 (상담일지는 원장만) */}
      {canSeeCounsel && (
        <div className="flex gap-1 rounded-xl bg-slate-100 p-1">
          <button
            onClick={() => setTab('notices')}
            className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              activeTab === 'notices'
                ? 'bg-white text-brand-700 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            📢 공지 · 알림장
          </button>
          <button
            onClick={() => setTab('counsel')}
            className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              activeTab === 'counsel'
                ? 'bg-white text-brand-700 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            💬 상담일지
          </button>
        </div>
      )}

      {activeTab === 'counsel' ? (
        counsel.isLoading ? (
          <div className="px-6 py-16 text-center text-sm text-slate-400">불러오는 중…</div>
        ) : (
          <CounselTab items={counsel.data ?? []} />
        )
      ) : announcements.isLoading ? (
        <div className="px-6 py-16 text-center text-sm text-slate-400">불러오는 중…</div>
      ) : (
        <NoticesTab items={announcements.data ?? []} />
      )}
    </div>
  )
}
