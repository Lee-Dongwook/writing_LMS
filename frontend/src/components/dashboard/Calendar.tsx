import { useMemo, useState } from 'react'
import type { CalendarEvent } from '../../types'

const WEEKDAYS = ['일', '월', '화', '수', '목', '금', '토']
const TODAY = '2026-07-10' // 목업 기준일

const TONE: Record<CalendarEvent['tone'], string> = {
  green: 'bg-emerald-50 text-emerald-600',
  blue: 'bg-sky-50 text-sky-600',
  red: 'bg-rose-50 text-rose-600',
}

interface Props {
  events?: CalendarEvent[]
}

interface Cell {
  date: Date
  inMonth: boolean
  iso: string
}

function toIso(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export default function Calendar({ events = [] }: Props) {
  // 목업 기준월: 2026년 7월
  const [cursor, setCursor] = useState(new Date(2026, 6, 1))

  const cells = useMemo<Cell[]>(() => {
    const year = cursor.getFullYear()
    const month = cursor.getMonth()
    const first = new Date(year, month, 1)
    const start = new Date(first)
    start.setDate(first.getDate() - first.getDay())

    return Array.from({ length: 42 }, (_, i) => {
      const date = new Date(start)
      date.setDate(start.getDate() + i)
      return { date, inMonth: date.getMonth() === month, iso: toIso(date) }
    })
  }, [cursor])

  const eventMap = useMemo(() => {
    const map = new Map<string, CalendarEvent>()
    events.forEach((e) => map.set(e.date, e))
    return map
  }, [events])

  const shift = (delta: number) =>
    setCursor((c) => new Date(c.getFullYear(), c.getMonth() + delta, 1))

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-lg font-bold text-slate-800">
          {cursor.getFullYear()}년 {cursor.getMonth() + 1}월
        </h3>
        <div className="flex items-center gap-1.5">
          <button
            onClick={() => setCursor(new Date(2026, 6, 1))}
            className="rounded-md border border-slate-200 bg-brand-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-700"
          >
            오늘
          </button>
          <button
            onClick={() => shift(-1)}
            className="rounded-md border border-slate-200 p-1.5 text-slate-500 hover:bg-slate-50"
            aria-label="이전 달"
          >
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M12.79 5.23a.75.75 0 01-.02 1.06L8.832 10l3.938 3.71a.75.75 0 11-1.04 1.08l-4.5-4.25a.75.75 0 010-1.08l4.5-4.25a.75.75 0 011.06.02z"
                clipRule="evenodd"
              />
            </svg>
          </button>
          <button
            onClick={() => shift(1)}
            className="rounded-md border border-slate-200 p-1.5 text-slate-500 hover:bg-slate-50"
            aria-label="다음 달"
          >
            <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M7.21 14.77a.75.75 0 01.02-1.06L11.168 10 7.23 6.29a.75.75 0 111.04-1.08l4.5 4.25a.75.75 0 010 1.08l-4.5 4.25a.75.75 0 01-1.06-.02z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        </div>
      </div>

      <div className="grid grid-cols-7 border-b border-slate-200 pb-2 text-center text-xs font-medium">
        {WEEKDAYS.map((w, i) => (
          <div
            key={w}
            className={i === 0 ? 'text-rose-400' : i === 6 ? 'text-sky-400' : 'text-slate-400'}
          >
            {w}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-7">
        {cells.map((cell, i) => {
          const ev = eventMap.get(cell.iso)
          const isToday = cell.iso === TODAY
          const dow = i % 7
          return (
            <div
              key={cell.iso}
              className="min-h-[64px] border-b border-r border-slate-100 p-1.5 [&:nth-child(7n)]:border-r-0"
            >
              <span
                className={`inline-flex h-6 w-6 items-center justify-center rounded-full text-xs ${
                  isToday
                    ? 'bg-amber-100 font-semibold text-amber-700'
                    : !cell.inMonth
                      ? 'text-slate-300'
                      : dow === 0
                        ? 'text-rose-400'
                        : dow === 6
                          ? 'text-sky-400'
                          : 'text-slate-600'
                }`}
              >
                {cell.date.getDate()}
              </span>
              {ev && (
                <div className={`mt-1 truncate rounded px-1 py-0.5 text-[10px] ${TONE[ev.tone]}`}>
                  {ev.label}
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
