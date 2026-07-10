import { useAttendance } from '../api/hooks'
import type { AttendanceRecord, AttendanceStatus } from '../types'

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']

// 상태별 배지 색상 (Tailwind 클래스)
const STATUS_STYLE: Record<AttendanceStatus, string> = {
  출석: 'bg-emerald-50 text-emerald-600',
  지각: 'bg-amber-50 text-amber-600',
  결석: 'bg-rose-50 text-rose-600',
  조퇴: 'bg-sky-50 text-sky-600',
  공결: 'bg-violet-50 text-violet-600',
}

function StatusBadge({ status }: { status: AttendanceStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLE[status]}`}
    >
      {status}
    </span>
  )
}

function StatCard({
  label,
  value,
  unit,
  tone,
}: {
  label: string
  value: number | string
  unit: string
  tone: string
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="text-sm text-slate-400">{label}</div>
      <div className={`mt-2 flex items-baseline gap-1 ${tone}`}>
        <span className="text-2xl font-bold">{value}</span>
        <span className="text-sm font-medium text-slate-400">{unit}</span>
      </div>
    </div>
  )
}

function weekday(iso: string): string {
  const d = new Date(`${iso}T00:00:00`)
  return WEEKDAYS[d.getDay()]
}

function AttendanceRow({ record }: { record: AttendanceRecord }) {
  const wd = weekday(record.date)
  return (
    <tr className="border-b border-slate-100 last:border-0 hover:bg-slate-50/60">
      <td className="whitespace-nowrap px-4 py-3 text-sm text-slate-700">
        {record.date.slice(5).replace('-', '.')}
        <span
          className={`ml-1.5 text-xs ${
            wd === '일' ? 'text-rose-400' : wd === '토' ? 'text-sky-400' : 'text-slate-400'
          }`}
        >
          ({wd})
        </span>
      </td>
      <td className="px-4 py-3">
        <StatusBadge status={record.status} />
      </td>
      <td className="px-4 py-3 text-sm tabular-nums text-slate-600">
        {record.checkIn ?? '-'}
      </td>
      <td className="px-4 py-3 text-sm tabular-nums text-slate-600">
        {record.checkOut ?? '-'}
      </td>
      <td className="px-4 py-3 text-sm text-slate-500">{record.note || '-'}</td>
    </tr>
  )
}

export default function Attendance() {
  const { data, isLoading } = useAttendance()

  const [year, month] = (data?.month ?? '2026-07').split('-')

  return (
    <div className="mx-auto max-w-6xl space-y-5 p-4 sm:p-6">
      {/* 헤더 */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-800">출석 관리</h2>
        <span className="text-sm font-medium text-slate-500">
          {year}년 {Number(month)}월
        </span>
      </div>

      {/* 요약 카드 */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <StatCard
          label="출석률"
          value={data?.attendanceRate ?? 0}
          unit="%"
          tone="text-brand-600"
        />
        <StatCard
          label="출석"
          value={data?.presentDays ?? 0}
          unit={`/ ${data?.totalDays ?? 0}일`}
          tone="text-emerald-600"
        />
        <StatCard
          label="지각"
          value={data?.lateDays ?? 0}
          unit="회"
          tone="text-amber-600"
        />
        <StatCard
          label="결석"
          value={data?.absentDays ?? 0}
          unit="회"
          tone="text-rose-600"
        />
      </div>

      {/* 출석 기록 테이블 */}
      <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="flex items-center justify-between border-b border-slate-100 px-6 py-4">
          <h3 className="text-base font-bold text-slate-800">출석 기록</h3>
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-400">
            {(['출석', '지각', '결석', '조퇴', '공결'] as AttendanceStatus[]).map(
              (s) => (
                <span key={s} className="flex items-center gap-1">
                  <StatusBadge status={s} />
                </span>
              ),
            )}
          </div>
        </div>

        {isLoading ? (
          <div className="px-6 py-16 text-center text-sm text-slate-400">
            불러오는 중…
          </div>
        ) : !data || data.records.length === 0 ? (
          <div className="px-6 py-16 text-center text-sm text-slate-400">
            출석 기록이 없습니다.
          </div>
        ) : (
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-100 text-left text-xs font-medium text-slate-400">
                <th className="px-4 py-3 font-medium">날짜</th>
                <th className="px-4 py-3 font-medium">상태</th>
                <th className="px-4 py-3 font-medium">입실</th>
                <th className="px-4 py-3 font-medium">퇴실</th>
                <th className="px-4 py-3 font-medium">비고</th>
              </tr>
            </thead>
            <tbody>
              {data.records.map((r) => (
                <AttendanceRow key={r.id} record={r} />
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
