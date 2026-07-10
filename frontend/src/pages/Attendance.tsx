import { useState } from 'react'
import { useAttendance, useNotifLogs } from '../api/hooks'
import { useUiStore } from '../store/uiStore'
import type { AttendanceRecord, AttendanceStatus, NotifLog } from '../types'

// 체크인 스테이션 대상 학생(데모 로스터)과 학부모 연락처
const ROSTER: { name: string; to: string }[] = [
  { name: '이동욱', to: '아버지 010-****-1092' },
  { name: '김철수', to: '어머니 010-****-2841' },
  { name: '이영희', to: '어머니 010-****-7733' },
  { name: '박민수', to: '아버지 010-****-5510' },
]

function nowHHMM(): string {
  const d = new Date()
  return `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
}

// 등하원 체크인 스테이션 (QR / 태블릿) — 원장 화면
function CheckInStation({ onSend }: { onSend: (log: NotifLog) => void }) {
  const [flash, setFlash] = useState<string | null>(null)

  const check = (name: string, to: string, type: '등원' | '하원') => {
    const log: NotifLog = {
      id: `local-${name}-${type}-${nowHHMM()}`,
      time: nowHHMM(),
      student: name,
      type,
      channel: '알림톡',
      to,
    }
    onSend(log)
    setFlash(`${name} ${type} 처리 · ${to}에게 알림톡 발송됨`)
  }

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h3 className="mb-4 text-base font-bold text-slate-800">
        등하원 체크인 <span className="text-sm font-normal text-slate-400">(QR · 태블릿)</span>
      </h3>
      <div className="grid gap-5 sm:grid-cols-[180px_1fr]">
        {/* QR 스캔 영역 (플레이스홀더) */}
        <div className="flex flex-col items-center justify-center rounded-xl border-2 border-dashed border-slate-200 bg-slate-50 p-4 text-center">
          <div className="text-4xl">🔳</div>
          <div className="mt-2 text-xs text-slate-400">
            QR / 바코드 스캔 대기중
            <br />
            (RFID 태그 지원)
          </div>
        </div>

        {/* 태블릿 수동 체크인 */}
        <div>
          <div className="mb-2 text-xs text-slate-400">태블릿 수동 체크인</div>
          <ul className="space-y-2">
            {ROSTER.map((s) => (
              <li key={s.name} className="flex items-center justify-between gap-2">
                <span className="text-sm font-medium text-slate-700">{s.name}</span>
                <div className="flex gap-1.5">
                  <button
                    onClick={() => check(s.name, s.to, '등원')}
                    className="rounded-md bg-emerald-50 px-3 py-1.5 text-xs font-medium text-emerald-600 transition-colors hover:bg-emerald-100"
                  >
                    등원
                  </button>
                  <button
                    onClick={() => check(s.name, s.to, '하원')}
                    className="rounded-md bg-sky-50 px-3 py-1.5 text-xs font-medium text-sky-600 transition-colors hover:bg-sky-100"
                  >
                    하원
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {flash && (
        <div className="mt-4 rounded-lg bg-brand-50 px-4 py-2.5 text-sm text-brand-700">
          ✅ {flash}
        </div>
      )}
    </div>
  )
}

// 알림 발송 이력 (등하원 시 학부모 알림톡/SMS)
function NotifLogPanel({ logs }: { logs: NotifLog[] }) {
  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-6 py-4">
        <h3 className="text-base font-bold text-slate-800">알림 발송 이력</h3>
        <p className="mt-0.5 text-xs text-slate-400">등·하원 시 학부모에게 자동 발송</p>
      </div>
      {logs.length === 0 ? (
        <div className="px-6 py-10 text-center text-sm text-slate-400">발송 이력이 없습니다.</div>
      ) : (
        <ul className="divide-y divide-slate-100">
          {logs.map((l) => (
            <li key={l.id} className="flex items-center gap-3 px-6 py-3">
              <span className="tabular-nums text-xs text-slate-400">{l.time}</span>
              <span
                className={`rounded px-2 py-0.5 text-xs font-medium ${
                  l.type === '등원'
                    ? 'bg-emerald-50 text-emerald-600'
                    : 'bg-sky-50 text-sky-600'
                }`}
              >
                {l.type}
              </span>
              <span className="text-sm font-medium text-slate-700">{l.student}</span>
              <span className="text-xs text-slate-400">→ {l.to}</span>
              <span
                className={`ml-auto rounded px-2 py-0.5 text-[11px] font-medium ${
                  l.channel === '알림톡'
                    ? 'bg-yellow-50 text-yellow-600'
                    : 'bg-slate-100 text-slate-500'
                }`}
              >
                {l.channel}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

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
  const { data: fetchedLogs } = useNotifLogs()
  const role = useUiStore((s) => s.role)
  const [sentLogs, setSentLogs] = useState<NotifLog[]>([])

  const [year, month] = (data?.month ?? '2026-07').split('-')

  // 방금 발송한 알림(최신순) + 서버 이력 합침
  const allLogs = [...sentLogs, ...(fetchedLogs ?? [])]

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

      {/* 등하원 체크인 (원장 전용) */}
      {role === 'director' && (
        <CheckInStation onSend={(log) => setSentLogs((prev) => [log, ...prev])} />
      )}

      {/* 알림 발송 이력 */}
      <NotifLogPanel logs={allLogs} />

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
