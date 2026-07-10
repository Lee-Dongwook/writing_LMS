import { useState } from 'react'
import { useAssignments, useVocabTests, useWrongItems } from '../api/hooks'
import type {
  Assignment,
  AssignmentStatus,
  LiteraryGenre,
  VocabTest,
  WrongItem,
} from '../types'

type Tab = 'assignments' | 'wrong' | 'vocab'

const TABS: { key: Tab; label: string; emoji: string }[] = [
  { key: 'assignments', label: '과제 이행도', emoji: '📝' },
  { key: 'wrong', label: '오답노트', emoji: '❌' },
  { key: 'vocab', label: '어휘 테스트', emoji: '📖' },
]

const STATUS_STYLE: Record<AssignmentStatus, string> = {
  완료: 'bg-emerald-50 text-emerald-600',
  미흡: 'bg-amber-50 text-amber-600',
  미제출: 'bg-rose-50 text-rose-600',
}

// ── 과제 이행도 탭 ──────────────────────────────────
function AssignmentsTab({ items }: { items: Assignment[] }) {
  const done = items.filter((a) => a.status === '완료').length
  const rate = items.length ? Math.round((done / items.length) * 100) : 0

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-3 gap-4">
        <StatCard label="완료율" value={`${rate}%`} tone="text-brand-600" />
        <StatCard
          label="완료"
          value={`${done} / ${items.length}`}
          tone="text-emerald-600"
        />
        <StatCard
          label="미제출"
          value={items.filter((a) => a.status === '미제출').length}
          tone="text-rose-600"
        />
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-6 py-4">
          <h3 className="text-base font-bold text-slate-800">과제 목록</h3>
        </div>
        <ul className="divide-y divide-slate-100">
          {items.map((a) => (
            <li key={a.id} className="px-6 py-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-500">
                      {a.category}
                    </span>
                    <span className="truncate font-medium text-slate-700">{a.title}</span>
                  </div>
                  <div className="mt-1 text-xs text-slate-400">
                    마감 {a.dueDate.slice(5).replace('-', '.')}
                    {a.feedback && ` · 💬 ${a.feedback}`}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {a.score !== null && (
                    <span className="tabular-nums text-sm font-semibold text-slate-600">
                      {a.score}점
                    </span>
                  )}
                  <span
                    className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLE[a.status]}`}
                  >
                    {a.status}
                  </span>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}

// ── 오답노트 탭 ────────────────────────────────────
function WrongTab({ items }: { items: WrongItem[] }) {
  const genres = Array.from(new Set(items.map((w) => w.genre)))
  const [genre, setGenre] = useState<LiteraryGenre | '전체'>('전체')

  const filtered = genre === '전체' ? items : items.filter((w) => w.genre === genre)
  const masteredCount = filtered.filter((w) => w.mastered).length

  return (
    <div className="space-y-5">
      {/* 갈래 필터 */}
      <div className="flex flex-wrap items-center gap-2">
        <FilterChip label="전체" active={genre === '전체'} onClick={() => setGenre('전체')} />
        {genres.map((g) => (
          <FilterChip
            key={g}
            label={g}
            active={genre === g}
            onClick={() => setGenre(g)}
          />
        ))}
        <button className="ml-auto rounded-lg bg-brand-600 px-3.5 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-brand-700">
          🖨️ {genre === '전체' ? '전체' : genre} 유사문제 모아 출력
        </button>
      </div>

      <div className="text-xs text-slate-400">
        {filtered.length}개 · 복습 완료 {masteredCount}개
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {filtered.map((w) => (
          <div
            key={w.id}
            className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
          >
            <div className="flex items-center justify-between">
              <span className="rounded bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
                {w.genre}
              </span>
              {w.mastered ? (
                <span className="text-xs font-medium text-emerald-600">✓ 복습완료</span>
              ) : (
                <span className="text-xs font-medium text-slate-400">복습 전</span>
              )}
            </div>
            <div className="mt-2 text-sm font-medium text-slate-700">{w.source}</div>
            <div className="mt-0.5 text-xs text-slate-500">유형: {w.questionType}</div>
            <div className="mt-2 rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
              🔍 {w.reason}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ── 어휘 테스트 탭 ─────────────────────────────────
function VocabTab({ items }: { items: VocabTest[] }) {
  const latest = items[items.length - 1]
  const avg =
    items.length === 0
      ? 0
      : Math.round(
          (items.reduce((s, v) => s + v.score / v.total, 0) / items.length) * 100,
        )

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-3 gap-4">
        <StatCard
          label="최근 점수"
          value={latest ? `${latest.score}/${latest.total}` : '-'}
          tone="text-brand-600"
        />
        <StatCard label="누적 평균" value={`${avg}%`} tone="text-emerald-600" />
        <StatCard label="응시 주차" value={`${items.length}주`} tone="text-slate-600" />
      </div>

      {/* 누적 추이 막대 */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-base font-bold text-slate-800">주차별 점수 추이</h3>
        <div className="flex items-end gap-4">
          {items.map((v) => {
            const pct = Math.round((v.score / v.total) * 100)
            return (
              <div key={v.id} className="flex flex-1 flex-col items-center gap-2">
                <span className="text-xs font-semibold text-brand-600">{v.score}</span>
                <div className="flex h-32 w-full items-end">
                  <div
                    className="w-full rounded-t-md bg-brand-400"
                    style={{ height: `${pct}%` }}
                  />
                </div>
                <span className="text-center text-[11px] leading-tight text-slate-400">
                  {v.week}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <table className="w-full">
          <thead>
            <tr className="border-b border-slate-100 text-left text-xs font-medium text-slate-400">
              <th className="px-4 py-3 font-medium">주차</th>
              <th className="px-4 py-3 font-medium">응시일</th>
              <th className="px-4 py-3 font-medium">점수</th>
              <th className="px-4 py-3 font-medium">정답률</th>
            </tr>
          </thead>
          <tbody>
            {[...items].reverse().map((v) => (
              <tr
                key={v.id}
                className="border-b border-slate-100 text-sm last:border-0 hover:bg-slate-50/60"
              >
                <td className="px-4 py-3 font-medium text-slate-700">{v.week}</td>
                <td className="px-4 py-3 text-slate-500">
                  {v.date.slice(5).replace('-', '.')}
                </td>
                <td className="px-4 py-3 tabular-nums text-slate-600">
                  {v.score} / {v.total}
                </td>
                <td className="px-4 py-3 tabular-nums text-slate-600">
                  {Math.round((v.score / v.total) * 100)}%
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

// ── 공용 소품 ──────────────────────────────────────
function StatCard({
  label,
  value,
  tone,
}: {
  label: string
  value: string | number
  tone: string
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-sm text-slate-400">{label}</div>
      <div className={`mt-2 text-2xl font-bold ${tone}`}>{value}</div>
    </div>
  )
}

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      onClick={onClick}
      className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
        active
          ? 'bg-brand-600 text-white'
          : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
      }`}
    >
      {label}
    </button>
  )
}

export default function Assignments() {
  const [tab, setTab] = useState<Tab>('assignments')
  const assignments = useAssignments()
  const wrong = useWrongItems()
  const vocab = useVocabTests()

  const loading =
    (tab === 'assignments' && assignments.isLoading) ||
    (tab === 'wrong' && wrong.isLoading) ||
    (tab === 'vocab' && vocab.isLoading)

  return (
    <div className="mx-auto max-w-6xl space-y-5 p-4 sm:p-6">
      <h2 className="text-lg font-bold text-slate-800">과제 · 오답노트</h2>

      {/* 탭 */}
      <div className="flex gap-1 rounded-xl bg-slate-100 p-1">
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              tab === t.key
                ? 'bg-white text-brand-700 shadow-sm'
                : 'text-slate-500 hover:text-slate-700'
            }`}
          >
            <span className="mr-1">{t.emoji}</span>
            {t.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="px-6 py-16 text-center text-sm text-slate-400">불러오는 중…</div>
      ) : tab === 'assignments' ? (
        <AssignmentsTab items={assignments.data ?? []} />
      ) : tab === 'wrong' ? (
        <WrongTab items={wrong.data ?? []} />
      ) : (
        <VocabTab items={vocab.data ?? []} />
      )}
    </div>
  )
}
