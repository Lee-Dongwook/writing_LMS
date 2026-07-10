import { useState } from 'react'
import { useClasses, useCurriculum, useSessionChanges } from '../api/hooks'
import { useUiStore } from '../store/uiStore'
import type { Klass, SessionChange, WeekStatus } from '../types'

const WEEK_STYLE: Record<WeekStatus, string> = {
  완료: 'bg-emerald-50 text-emerald-600',
  진행중: 'bg-brand-50 text-brand-700',
  예정: 'bg-slate-100 text-slate-500',
}

// 반 카드
function ClassCard({
  klass,
  active,
  onClick,
}: {
  klass: Klass
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-2xl border bg-white p-5 text-left shadow-sm transition-colors ${
        active ? 'border-brand-400 ring-1 ring-brand-200' : 'border-slate-200 hover:border-slate-300'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="font-semibold text-slate-800">{klass.name}</span>
      </div>
      <div className="mt-2 flex flex-wrap gap-1.5">
        {[klass.grade, klass.level, klass.school].map((t) => (
          <span
            key={t}
            className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500"
          >
            {t}
          </span>
        ))}
      </div>

      <div className="mt-4 space-y-1 text-xs text-slate-500">
        <div>👩‍🏫 {klass.teacher} · {klass.schedule}</div>
        <div>
          👥 정원 {klass.studentCount}/{klass.capacity}명
        </div>
      </div>

      {/* 진도율 */}
      <div className="mt-3">
        <div className="mb-1 flex items-center justify-between text-xs">
          <span className="text-slate-400">진도율</span>
          <span className="font-semibold text-brand-600">{klass.progress}%</span>
        </div>
        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
          <div
            className="h-full rounded-full bg-brand-500"
            style={{ width: `${klass.progress}%` }}
          />
        </div>
      </div>
    </button>
  )
}

function SessionRow({ s }: { s: SessionChange }) {
  return (
    <li className="flex flex-wrap items-center gap-x-3 gap-y-1 px-6 py-3.5">
      <span className="tabular-nums text-sm text-slate-500">
        {s.date.slice(5).replace('-', '.')}
      </span>
      <span
        className={`rounded px-2 py-0.5 text-xs font-medium ${
          s.type === '보강' ? 'bg-sky-50 text-sky-600' : 'bg-rose-50 text-rose-600'
        }`}
      >
        {s.type}
      </span>
      <span className="text-sm font-medium text-slate-700">{s.target}</span>
      <span className="text-xs text-slate-400">· {s.reason}</span>
      {s.makeupDate && (
        <span className="ml-auto text-xs text-slate-500">
          보강일 {s.makeupDate.slice(5).replace('-', '.')}
        </span>
      )}
    </li>
  )
}

export default function Classes() {
  const role = useUiStore((s) => s.role)
  const { data: classes, isLoading } = useClasses()
  const { data: curriculum } = useCurriculum()
  const { data: sessions } = useSessionChanges()
  const [selectedId, setSelectedId] = useState<string | null>(null)

  const selected = classes?.find((c) => c.id === selectedId) ?? classes?.[0]

  return (
    <div className="mx-auto max-w-6xl space-y-5 p-4 sm:p-6">
      {/* 헤더 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-lg font-bold text-slate-800">수강 · 강의 관리</h2>
        {role === 'director' && (
          <button className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-brand-700">
            + 반 개설
          </button>
        )}
      </div>

      {/* 반 목록 */}
      {isLoading ? (
        <div className="px-6 py-16 text-center text-sm text-slate-400">불러오는 중…</div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {classes?.map((c) => (
            <ClassCard
              key={c.id}
              klass={c}
              active={c.id === selected?.id}
              onClick={() => setSelectedId(c.id)}
            />
          ))}
        </div>
      )}

      {/* 선택 반 진도(주차별 커리큘럼) */}
      {selected && (
        <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
            <div>
              <h3 className="text-base font-bold text-slate-800">주차별 진도</h3>
              <p className="mt-0.5 text-xs text-slate-400">{selected.name}</p>
            </div>
            <span className="text-sm font-semibold text-brand-600">
              진도율 {selected.progress}%
            </span>
          </div>
          <ul className="divide-y divide-slate-100">
            {curriculum?.map((w) => (
              <li key={w.week} className="flex items-center gap-4 px-6 py-3.5">
                <span className="w-10 shrink-0 text-sm font-semibold text-slate-400">
                  {w.week}주차
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-slate-700">{w.topic}</div>
                  <div className="text-xs text-slate-400">{w.detail}</div>
                </div>
                <span
                  className={`shrink-0 rounded-full px-2.5 py-0.5 text-xs font-medium ${WEEK_STYLE[w.status]}`}
                >
                  {w.status}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 보강 · 휴강 일정 */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <h3 className="text-base font-bold text-slate-800">보강 · 휴강 일정</h3>
          {role === 'director' && (
            <button className="rounded-lg border border-slate-200 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50">
              + 일정 등록
            </button>
          )}
        </div>
        {sessions && sessions.length > 0 ? (
          <ul className="divide-y divide-slate-100">
            {sessions.map((s) => (
              <SessionRow key={s.id} s={s} />
            ))}
          </ul>
        ) : (
          <div className="px-6 py-10 text-center text-sm text-slate-400">
            예정된 보강/휴강이 없습니다.
          </div>
        )}
      </div>
    </div>
  )
}
