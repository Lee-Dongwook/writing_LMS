import { useState } from 'react'
import { useGradeReport } from '../api/hooks'
import { useUiStore } from '../store/uiStore'
import type { ExamResult } from '../types'

// 등급 배지 색상 (1~2 우수 / 3~4 보통 / 5+ 주의)
function gradeTone(grade: number): string {
  if (grade <= 2) return 'bg-emerald-50 text-emerald-600'
  if (grade <= 4) return 'bg-sky-50 text-sky-600'
  return 'bg-amber-50 text-amber-600'
}

function SummaryCard({
  label,
  value,
  unit,
  sub,
  tone,
}: {
  label: string
  value: string | number
  unit?: string
  sub?: string
  tone: string
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-sm text-slate-400">{label}</div>
      <div className={`mt-2 flex items-baseline gap-1 ${tone}`}>
        <span className="text-2xl font-bold">{value}</span>
        {unit && <span className="text-sm font-medium text-slate-400">{unit}</span>}
      </div>
      {sub && <div className="mt-1 text-xs text-slate-400">{sub}</div>}
    </div>
  )
}

// 백분위 추이 막대 차트 (순수 CSS)
function PercentileTrend({
  exams,
  selectedId,
  onSelect,
}: {
  exams: ExamResult[]
  selectedId: string
  onSelect: (id: string) => void
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-base font-bold text-slate-800">백분위 추이</h3>
      <div className="flex items-end gap-3 sm:gap-5">
        {exams.map((e) => {
          const active = e.id === selectedId
          return (
            <button
              key={e.id}
              onClick={() => onSelect(e.id)}
              className="flex flex-1 flex-col items-center gap-2"
            >
              <span
                className={`text-xs font-semibold ${
                  active ? 'text-brand-600' : 'text-slate-400'
                }`}
              >
                {e.percentile}
              </span>
              <div className="flex h-40 w-full items-end">
                <div
                  className={`w-full rounded-t-md transition-colors ${
                    active ? 'bg-brand-500' : 'bg-brand-100 hover:bg-brand-200'
                  }`}
                  style={{ height: `${e.percentile}%` }}
                />
              </div>
              <span
                className={`text-center text-[11px] leading-tight ${
                  active ? 'font-medium text-slate-700' : 'text-slate-400'
                }`}
              >
                {e.title.replace(' ', '\n')}
              </span>
            </button>
          )
        })}
      </div>
    </div>
  )
}

// 영역별 점수 (독서/문학/선택)
function DomainBars({ exam }: { exam: ExamResult }) {
  const domains = exam.domainScores.filter((d) => d.max > 0)
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-base font-bold text-slate-800">
        영역별 점수 <span className="text-sm font-normal text-slate-400">({exam.title})</span>
      </h3>
      <div className="space-y-4">
        {domains.map((d) => {
          const pct = Math.round((d.score / d.max) * 100)
          return (
            <div key={d.domain}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="font-medium text-slate-600">{d.domain}</span>
                <span className="tabular-nums text-slate-500">
                  {d.score} / {d.max}
                  <span className="ml-1.5 text-xs text-slate-400">{pct}%</span>
                </span>
              </div>
              <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className="h-full rounded-full bg-brand-500"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// 역량별 정답률 (사실적/추론적/비판적 이해, 어휘·개념)
function CompetencyBars({ exam }: { exam: ExamResult }) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-base font-bold text-slate-800">역량별 정답률</h3>
      <div className="space-y-4">
        {exam.competencyRates.map((c) => {
          const pct = Math.round((c.correct / c.total) * 100)
          // 정답률 70% 미만은 취약 영역으로 강조
          const weak = pct < 70
          return (
            <div key={c.competency}>
              <div className="mb-1 flex items-center justify-between text-sm">
                <span className="font-medium text-slate-600">
                  {c.competency}
                  {weak && (
                    <span className="ml-1.5 rounded bg-rose-50 px-1.5 py-0.5 text-[11px] font-medium text-rose-500">
                      취약
                    </span>
                  )}
                </span>
                <span className="tabular-nums text-slate-500">
                  {c.correct}/{c.total}
                  <span className="ml-1.5 text-xs text-slate-400">{pct}%</span>
                </span>
              </div>
              <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-full rounded-full ${weak ? 'bg-rose-400' : 'bg-emerald-500'}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

export default function Grades() {
  const { data, isLoading } = useGradeReport()
  const role = useUiStore((s) => s.role)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  if (isLoading || !data) {
    return (
      <div className="px-6 py-16 text-center text-sm text-slate-400">불러오는 중…</div>
    )
  }

  const exams = data.exams
  const latest = exams[exams.length - 1]
  const selected = exams.find((e) => e.id === selectedId) ?? latest
  const prev = exams[exams.indexOf(selected) - 1]
  const diff = prev ? selected.rawScore - prev.rawScore : 0

  const actionLabel = role === 'director' ? '성적표 발송' : 'PDF 성적표 받기'

  return (
    <div className="mx-auto max-w-6xl space-y-5 p-4 sm:p-6">
      {/* 헤더 */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-bold text-slate-800">성적 · 평가 분석</h2>
          <p className="mt-0.5 text-sm text-slate-400">
            {data.student} · {data.className}
          </p>
        </div>
        <button className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-brand-700">
          {role === 'director' ? '📤 ' : '📄 '}
          {actionLabel}
        </button>
      </div>

      {/* 최신 성적 요약 */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <SummaryCard
          label={`원점수 (${selected.title})`}
          value={selected.rawScore}
          unit="점"
          sub={
            prev
              ? `직전 대비 ${diff >= 0 ? '▲' : '▼'} ${Math.abs(diff)}점`
              : '첫 응시'
          }
          tone={diff >= 0 ? 'text-brand-600' : 'text-rose-600'}
        />
        <SummaryCard
          label="백분위"
          value={selected.percentile}
          unit="%"
          sub={`반 평균 원점수 ${selected.classAvg}점`}
          tone="text-emerald-600"
        />
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="text-sm text-slate-400">등급</div>
          <div className="mt-2 flex items-baseline gap-2">
            <span
              className={`inline-flex h-9 w-9 items-center justify-center rounded-lg text-lg font-bold ${gradeTone(
                selected.grade,
              )}`}
            >
              {selected.grade}
            </span>
            <span className="text-sm text-slate-400">등급</span>
          </div>
          <div className="mt-1 text-xs text-slate-400">표준점수 {selected.standardScore}</div>
        </div>
        <SummaryCard
          label="반 평균 대비"
          value={`+${selected.rawScore - selected.classAvg}`}
          unit="점"
          sub={`내 ${selected.rawScore} · 반 ${selected.classAvg}`}
          tone="text-brand-600"
        />
      </div>

      {/* 백분위 추이 (시험 선택) */}
      <PercentileTrend
        exams={exams}
        selectedId={selected.id}
        onSelect={setSelectedId}
      />

      {/* 영역별 / 역량별 */}
      <div className="grid gap-5 lg:grid-cols-2">
        <DomainBars exam={selected} />
        <CompetencyBars exam={selected} />
      </div>

      {/* 시험 목록 */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-100 px-6 py-4">
          <h3 className="text-base font-bold text-slate-800">응시 이력</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px]">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs font-medium text-slate-400">
                <th className="px-4 py-3 font-medium">시험</th>
                <th className="px-4 py-3 font-medium">구분</th>
                <th className="px-4 py-3 font-medium">원점수</th>
                <th className="px-4 py-3 font-medium">표준점수</th>
                <th className="px-4 py-3 font-medium">백분위</th>
                <th className="px-4 py-3 font-medium">등급</th>
              </tr>
            </thead>
            <tbody>
              {[...exams].reverse().map((e) => (
                <tr
                  key={e.id}
                  onClick={() => setSelectedId(e.id)}
                  className={`cursor-pointer border-b border-slate-100 text-sm last:border-0 hover:bg-slate-50/60 ${
                    e.id === selected.id ? 'bg-brand-50/50' : ''
                  }`}
                >
                  <td className="whitespace-nowrap px-4 py-3 font-medium text-slate-700">
                    {e.title}
                  </td>
                  <td className="px-4 py-3 text-slate-500">{e.type}</td>
                  <td className="px-4 py-3 tabular-nums text-slate-600">{e.rawScore}</td>
                  <td className="px-4 py-3 tabular-nums text-slate-600">
                    {e.standardScore}
                  </td>
                  <td className="px-4 py-3 tabular-nums text-slate-600">{e.percentile}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex h-6 w-6 items-center justify-center rounded text-xs font-bold ${gradeTone(
                        e.grade,
                      )}`}
                    >
                      {e.grade}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
