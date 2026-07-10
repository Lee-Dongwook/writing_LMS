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

// ── 성적/평가 (국어 특화) ─────────────────────────────
export type GradeDomain = '독서' | '문학' | '화법과작문' | '언어와매체'
export type Competency = '사실적 이해' | '추론적 이해' | '비판적 이해' | '어휘·개념'

export interface DomainScore {
  domain: GradeDomain
  score: number // 획득 점수
  max: number // 만점
}

export interface CompetencyRate {
  competency: Competency
  correct: number
  total: number
}

export interface ExamResult {
  id: string
  date: string // YYYY-MM-DD
  title: string // 예: '6월 모의고사'
  type: '모의고사' | '정기평가'
  rawScore: number // 원점수 (0~100)
  standardScore: number // 표준점수
  percentile: number // 백분위 (0~100)
  grade: number // 등급 (1~9)
  classAvg: number // 반 평균 원점수
  domainScores: DomainScore[]
  competencyRates: CompetencyRate[]
}

export interface GradeReport {
  student: string
  className: string
  exams: ExamResult[] // 시간순(오래된→최신)
}

// ── 과제 / 오답노트 / 어휘 (국어 특화) ─────────────────
export type AssignmentStatus = '완료' | '미흡' | '미제출'
export type AssignmentCategory = '독서 분석' | '문학 감상' | '어휘 테스트' | '오답 정리'

export interface Assignment {
  id: string
  title: string
  category: AssignmentCategory
  dueDate: string // YYYY-MM-DD
  status: AssignmentStatus
  score: number | null // 이행도 점수 (0~100), 미제출은 null
  feedback: string
}

// 국어 갈래(장르) — 오답노트 유사 유형 묶음 기준
export type LiteraryGenre =
  | '현대시'
  | '고전시가'
  | '현대소설'
  | '고전소설'
  | '수필·극'
  | '독서(인문)'
  | '독서(과학)'
  | '독서(사회)'

export interface WrongItem {
  id: string
  date: string // YYYY-MM-DD
  source: string // 출처 예: '6월 모의평가 23번'
  genre: LiteraryGenre
  questionType: string // 유형 예: '세부 정보 추론'
  reason: string // 오답 원인
  mastered: boolean // 복습 완료 여부
}

export interface VocabTest {
  id: string
  week: string // '7월 1주차'
  date: string // YYYY-MM-DD
  score: number // 맞은 개수
  total: number
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
