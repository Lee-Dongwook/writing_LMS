export type UserRole = '수강생' | '강사' | '매니저'

export interface OnlineUser {
  id: string
  name: string
  role: UserRole
  emoji: string
}

export interface Notice {
  id: string
  tag: string
  title: string
  author: string
}

export interface ScheduleItem {
  id: string
  date: string // YYYY-MM-DD
  title: string
}

export interface CalendarEvent {
  date: string // YYYY-MM-DD
  label: string
  tone: 'green' | 'blue' | 'red'
}

export type AttendanceStatus = '출석' | '지각' | '결석' | '조퇴' | '공결'

export interface AttendanceRecord {
  id: string
  date: string // YYYY-MM-DD
  status: AttendanceStatus
  checkIn: string | null // HH:MM
  checkOut: string | null // HH:MM
  note: string
}

export interface AttendanceSummary {
  month: string // YYYY-MM
  totalDays: number
  presentDays: number
  lateDays: number
  absentDays: number
  attendanceRate: number // 0~100
  records: AttendanceRecord[]
}

export interface CourseOverview {
  title: string
  round: string
  trainingPeriod: string
  examPeriod: string
  totalHours: string
  quote: string
  quoteAuthor: string
  attendanceRate: number
  submitRate: number
  attendanceCount: string
  submitCount: string
}
