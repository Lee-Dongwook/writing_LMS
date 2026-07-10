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
