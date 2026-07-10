import type {
  AttendanceRecord,
  AttendanceStatus,
  AttendanceSummary,
  CalendarEvent,
  CourseOverview,
  ExamResult,
  GradeReport,
  Notice,
  OnlineUser,
  ScheduleItem,
} from '../types'

// 간단한 지연으로 실제 네트워크 요청을 흉내낸다 (Tanstack Query 로딩 UX 확인용)
const delay = <T>(data: T, ms = 400): Promise<T> =>
  new Promise((resolve) => setTimeout(() => resolve(data), ms))

export const fetchCourseOverview = (): Promise<CourseOverview> =>
  delay({
    title: '국풍2000 용죽국어관학원',
    round: '',
    trainingPeriod: '26.06.30 (화) ~ 26.09.07 (월)',
    examPeriod: '26.06.15 (월) ~ 26.06.15 (월)',
    totalHours: '60일 / 180시간',
    quote: '롤모델 삼는 사람은 레이저 같은 집중력을 가진 평범한 사람입니다.',
    quoteAuthor: '스티브 잡스',
    attendanceRate: 0,
    submitRate: 0,
    attendanceCount: '0/0',
    submitCount: '0/0',
  })

export const fetchNotices = (): Promise<Notice[]> =>
  delay([
    { id: 'n1', tag: '공지사항', title: '수업 일정', author: '임정민' },
    { id: 'n2', tag: '공지', title: '필요서류 요청받음', author: '임정민' },
    { id: 'n3', tag: '공지', title: '자습 운영 시간 안내', author: '임정민' },
    { id: 'n4', tag: '공지', title: '훈련생 필수 제출 서류', author: '임정민' },
  ])

export const fetchSchedule = (): Promise<ScheduleItem[]> =>
  delay([{ id: 's1', date: '2026-09-07', title: '종강' }])

export const fetchCalendarEvents = (): Promise<CalendarEvent[]> =>
  delay([
    { date: '2026-06-30', label: '개강', tone: 'green' },
    { date: '2026-09-07', label: '종강', tone: 'red' },
  ])

const ROLES: OnlineUser['role'][] = ['수강생', '강사', '매니저']
const NAMES = [
  '강연수', '김순동', '김영철', '김종대', '김지현', '박규섭2', '박세용', '박지원',
  '서민준', '오하늘', '이도윤', '이수민', '장현우', '정예린', '조민재', '최유나',
  '한지훈', '홍서연', '문가온', '배정후', '신아름', '윤도현',
]

// 출석 목업: 2026년 7월, 평일(월~금)만 수업일로 생성한다.
function buildAttendanceRecords(): AttendanceRecord[] {
  // 날짜별 상태 시나리오 (기준일 2026-07-10까지만 기록이 존재)
  const scenario: Record<number, { status: AttendanceStatus; note?: string }> = {
    1: { status: '출석' },
    2: { status: '출석' },
    3: { status: '지각', note: '지하철 지연' },
    6: { status: '출석' },
    7: { status: '결석', note: '병가 (진단서 제출)' },
    8: { status: '공결', note: '모의고사 응시' },
    9: { status: '출석' },
    10: { status: '조퇴', note: '병원 진료' },
  }

  const records: AttendanceRecord[] = []
  for (let day = 1; day <= 31; day++) {
    const date = new Date(2026, 6, day)
    const dow = date.getDay()
    if (dow === 0 || dow === 6) continue // 주말 제외
    const entry = scenario[day]
    if (!entry) continue // 기준일 이후는 기록 없음

    const iso = toIso(date)
    let checkIn: string | null = '09:00'
    let checkOut: string | null = '18:00'
    if (entry.status === '지각') checkIn = '09:24'
    if (entry.status === '조퇴') checkOut = '14:10'
    if (entry.status === '결석' || entry.status === '공결') {
      checkIn = null
      checkOut = null
    }

    records.push({
      id: `att-${iso}`,
      date: iso,
      status: entry.status,
      checkIn,
      checkOut,
      note: entry.note ?? '',
    })
  }
  return records
}

function toIso(d: Date): string {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export const fetchAttendance = (): Promise<AttendanceSummary> => {
  const records = buildAttendanceRecords()
  const presentDays = records.filter((r) => r.status === '출석').length
  const lateDays = records.filter((r) => r.status === '지각').length
  const absentDays = records.filter((r) => r.status === '결석').length
  // 출석률: 결석을 제외한 참여일 비율 (지각/조퇴/공결은 참여로 인정)
  const attended = records.filter((r) => r.status !== '결석').length
  const attendanceRate =
    records.length === 0 ? 0 : Math.round((attended / records.length) * 100)

  return delay({
    month: '2026-07',
    totalDays: records.length,
    presentDays,
    lateDays,
    absentDays,
    attendanceRate,
    records,
  })
}

// 성적/평가 목업: 3월→7월 모의고사 4회 + 정기평가 1회, 국어 영역/역량별 세부 점수
const EXAMS: ExamResult[] = [
  {
    id: 'e1',
    date: '2026-03-25',
    title: '3월 학력평가',
    type: '모의고사',
    rawScore: 78,
    standardScore: 118,
    percentile: 82,
    grade: 3,
    classAvg: 71,
    domainScores: [
      { domain: '독서', score: 28, max: 38 },
      { domain: '문학', score: 30, max: 38 },
      { domain: '언어와매체', score: 20, max: 24 },
      { domain: '화법과작문', score: 0, max: 0 },
    ],
    competencyRates: [
      { competency: '사실적 이해', correct: 12, total: 14 },
      { competency: '추론적 이해', correct: 8, total: 13 },
      { competency: '비판적 이해', correct: 5, total: 8 },
      { competency: '어휘·개념', correct: 6, total: 10 },
    ],
  },
  {
    id: 'e2',
    date: '2026-04-15',
    title: '4월 정기평가',
    type: '정기평가',
    rawScore: 82,
    standardScore: 122,
    percentile: 86,
    grade: 2,
    classAvg: 74,
    domainScores: [
      { domain: '독서', score: 31, max: 38 },
      { domain: '문학', score: 31, max: 38 },
      { domain: '언어와매체', score: 20, max: 24 },
      { domain: '화법과작문', score: 0, max: 0 },
    ],
    competencyRates: [
      { competency: '사실적 이해', correct: 13, total: 14 },
      { competency: '추론적 이해', correct: 9, total: 13 },
      { competency: '비판적 이해', correct: 6, total: 8 },
      { competency: '어휘·개념', correct: 7, total: 10 },
    ],
  },
  {
    id: 'e3',
    date: '2026-05-20',
    title: '5월 학력평가',
    type: '모의고사',
    rawScore: 80,
    standardScore: 120,
    percentile: 84,
    grade: 3,
    classAvg: 73,
    domainScores: [
      { domain: '독서', score: 29, max: 38 },
      { domain: '문학', score: 32, max: 38 },
      { domain: '언어와매체', score: 19, max: 24 },
      { domain: '화법과작문', score: 0, max: 0 },
    ],
    competencyRates: [
      { competency: '사실적 이해', correct: 12, total: 14 },
      { competency: '추론적 이해', correct: 8, total: 13 },
      { competency: '비판적 이해', correct: 6, total: 8 },
      { competency: '어휘·개념', correct: 8, total: 10 },
    ],
  },
  {
    id: 'e4',
    date: '2026-06-04',
    title: '6월 모의평가',
    type: '모의고사',
    rawScore: 88,
    standardScore: 128,
    percentile: 92,
    grade: 2,
    classAvg: 76,
    domainScores: [
      { domain: '독서', score: 34, max: 38 },
      { domain: '문학', score: 34, max: 38 },
      { domain: '언어와매체', score: 20, max: 24 },
      { domain: '화법과작문', score: 0, max: 0 },
    ],
    competencyRates: [
      { competency: '사실적 이해', correct: 14, total: 14 },
      { competency: '추론적 이해', correct: 11, total: 13 },
      { competency: '비판적 이해', correct: 7, total: 8 },
      { competency: '어휘·개념', correct: 8, total: 10 },
    ],
  },
  {
    id: 'e5',
    date: '2026-07-02',
    title: '7월 학력평가',
    type: '모의고사',
    rawScore: 91,
    standardScore: 131,
    percentile: 95,
    grade: 1,
    classAvg: 78,
    domainScores: [
      { domain: '독서', score: 36, max: 38 },
      { domain: '문학', score: 35, max: 38 },
      { domain: '언어와매체', score: 20, max: 24 },
      { domain: '화법과작문', score: 0, max: 0 },
    ],
    competencyRates: [
      { competency: '사실적 이해', correct: 14, total: 14 },
      { competency: '추론적 이해', correct: 12, total: 13 },
      { competency: '비판적 이해', correct: 7, total: 8 },
      { competency: '어휘·개념', correct: 9, total: 10 },
    ],
  },
]

export const fetchGradeReport = (): Promise<GradeReport> =>
  delay({
    student: '이동욱',
    className: '고3 독서·문학 심화반',
    exams: EXAMS,
  })

export const fetchOnlineUsers = (): Promise<OnlineUser[]> =>
  delay(
    NAMES.map((name, i) => ({
      id: `u${i}`,
      name,
      // 강사/매니저는 소수만, 나머지는 수강생
      role: i === 1 ? '강사' : i === 5 ? '매니저' : ROLES[0],
      emoji: i === 1 ? '👨‍🏫' : i === 5 ? '🧑‍💼' : '👨',
    })),
  )
