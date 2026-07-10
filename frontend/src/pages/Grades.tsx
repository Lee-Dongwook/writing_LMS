import { useState } from 'react'
import { useGradeReport } from '../api/hooks'
import { useUiStore } from '../store/uiStore'
import { Bar, Card, Eyebrow, PillButton, Stat } from '../components/ui'
import type { ExamResult } from '../types'

// 백분위 추이 — 선택 막대만 진홍, 나머지는 중립. 색은 위계에만.
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
    <Card>
      <h3 className="mb-6 text-lg font-bold text-ink">백분위 추이</h3>
      <div className="flex items-end gap-3 sm:gap-6">
        {exams.map((e) => {
          const active = e.id === selectedId
          return (
            <button
              key={e.id}
              onClick={() => onSelect(e.id)}
              className="flex flex-1 flex-col items-center gap-2.5"
            >
              <span
                className={`stat-num text-sm font-bold ${
                  active ? 'text-brand-600' : 'text-slate-400'
                }`}
              >
                {e.percentile}
              </span>
              <div className="flex h-44 w-full items-end">
                <div
                  className={`w-full rounded-t-md transition-colors ${
                    active ? 'bg-brand-600' : 'bg-brand-200 hover:bg-brand-300'
                  }`}
                  style={{ height: `${e.percentile}%` }}
                />
              </div>
              <span
                className={`text-center text-xs leading-tight ${
                  active ? 'font-semibold text-ink' : 'text-slate-400'
                }`}
              >
                {e.title}
              </span>
            </button>
          )
        })}
      </div>
    </Card>
  )
}

// 영역별 점수 — 중립(먹) 막대
function DomainBars({ exam }: { exam: ExamResult }) {
  const domains = exam.domainScores.filter((d) => d.max > 0)
  return (
    <Card>
      <h3 className="mb-1 text-lg font-bold text-ink">영역별 점수</h3>
      <p className="mb-6 text-sm text-slate-400">{exam.title}</p>
      <div className="space-y-5">
        {domains.map((d) => {
          const pct = Math.round((d.score / d.max) * 100)
          return (
            <div key={d.domain}>
              <div className="mb-2 flex items-baseline justify-between">
                <span className="text-sm font-semibold text-ink">{d.domain}</span>
                <span className="stat-num text-sm text-slate-500">
                  {d.score} / {d.max}
                  <span className="ml-2 text-slate-400">{pct}%</span>
                </span>
              </div>
              <Bar pct={pct} tone="mid" />
            </div>
          )
        })}
      </div>
    </Card>
  )
}

// 역량별 정답률 — 취약(70% 미만)만 진홍으로 강조
function CompetencyBars({ exam }: { exam: ExamResult }) {
  return (
    <Card>
      <h3 className="mb-6 text-lg font-bold text-ink">역량별 정답률</h3>
      <div className="space-y-5">
        {exam.competencyRates.map((c) => {
          const pct = Math.round((c.correct / c.total) * 100)
          const weak = pct < 70
          return (
            <div key={c.competency}>
              <div className="mb-2 flex items-baseline justify-between">
                <span className="flex items-center gap-2 text-sm font-semibold text-ink">
                  {c.competency}
                  {weak && (
                    <span className="text-xs font-bold text-brand-600">· 취약</span>
                  )}
                </span>
                <span className="stat-num text-sm text-slate-500">
                  {c.correct}/{c.total}
                  <span className="ml-2 text-slate-400">{pct}%</span>
                </span>
              </div>
              <Bar pct={pct} tone={weak ? 'strong' : 'soft'} />
            </div>
          )
        })}
      </div>
    </Card>
  )
}

export default function Grades() {
  const { data, isLoading } = useGradeReport()
  const role = useUiStore((s) => s.role)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  if (isLoading || !data) {
    return <div className="px-6 py-20 text-center text-sm text-slate-400">불러오는 중…</div>
  }

  const exams = data.exams
  const latest = exams[exams.length - 1]
  const selected = exams.find((e) => e.id === selectedId) ?? latest
  const prev = exams[exams.indexOf(selected) - 1]
  const diff = prev ? selected.rawScore - prev.rawScore : 0

  return (
    <div className="mx-auto max-w-5xl space-y-8 px-6 py-10 fade-up">
      {/* 헤더 */}
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <Eyebrow>성적 · 평가</Eyebrow>
          <h2 className="mt-2 text-[32px] font-extrabold leading-tight text-ink">
            성적 분석 리포트
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            {data.student} · {data.className}
          </p>
        </div>
        <PillButton>
          {role === 'director' ? '성적표 발송' : 'PDF 성적표 받기'}
        </PillButton>
      </header>

      {/* 요약 통계 (선택 시험 기준) */}
      <Card>
        <div className="mb-5 flex items-baseline justify-between">
          <span className="text-sm font-semibold text-ink">{selected.title}</span>
          <span className="text-xs text-slate-400">{selected.type}</span>
        </div>
        <div className="grid grid-cols-2 gap-x-6 gap-y-8 sm:grid-cols-4">
          <Stat
            label="원점수"
            value={selected.rawScore}
            unit="점"
            sub={prev ? `직전 대비 ${diff >= 0 ? '▲' : '▼'} ${Math.abs(diff)}점` : '첫 응시'}
          />
          <Stat
            label="백분위"
            value={selected.percentile}
            accent
            sub={`반 평균 ${selected.classAvg}점`}
          />
          <Stat
            label="등급"
            value={selected.grade}
            unit="등급"
            sub={`표준점수 ${selected.standardScore}`}
          />
          <Stat
            label="반 평균 대비"
            value={`+${selected.rawScore - selected.classAvg}`}
            unit="점"
            sub={`내 ${selected.rawScore} · 반 ${selected.classAvg}`}
          />
        </div>
      </Card>

      {/* 백분위 추이 */}
      <PercentileTrend exams={exams} selectedId={selected.id} onSelect={setSelectedId} />

      {/* 영역별 / 역량별 */}
      <div className="grid gap-6 lg:grid-cols-2">
        <DomainBars exam={selected} />
        <CompetencyBars exam={selected} />
      </div>

      {/* 응시 이력 */}
      <section>
        <h3 className="mb-4 text-lg font-bold text-ink">응시 이력</h3>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[560px] border-collapse">
            <thead>
              <tr className="text-left text-xs font-semibold uppercase tracking-wide text-slate-400">
                <th className="pb-3 pr-4 font-semibold">시험</th>
                <th className="pb-3 pr-4 font-semibold">구분</th>
                <th className="pb-3 pr-4 font-semibold">원점수</th>
                <th className="pb-3 pr-4 font-semibold">표준점수</th>
                <th className="pb-3 pr-4 font-semibold">백분위</th>
                <th className="pb-3 font-semibold">등급</th>
              </tr>
            </thead>
            <tbody>
              {[...exams].reverse().map((e) => {
                const on = e.id === selected.id
                return (
                  <tr
                    key={e.id}
                    onClick={() => setSelectedId(e.id)}
                    className="cursor-pointer border-t border-line text-sm"
                  >
                    <td className="py-3.5 pr-4">
                      <span
                        className={`font-semibold ${on ? 'text-brand-600' : 'text-ink'}`}
                      >
                        {on && <span className="mr-1.5">▸</span>}
                        {e.title}
                      </span>
                    </td>
                    <td className="py-3.5 pr-4 text-slate-500">{e.type}</td>
                    <td className="stat-num py-3.5 pr-4 text-ink">{e.rawScore}</td>
                    <td className="stat-num py-3.5 pr-4 text-slate-500">
                      {e.standardScore}
                    </td>
                    <td className="stat-num py-3.5 pr-4 text-slate-500">{e.percentile}</td>
                    <td className="stat-num py-3.5 font-bold text-ink">{e.grade}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
