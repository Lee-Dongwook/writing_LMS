import type {
  Assignment,
  AttendanceRecord,
  AttendanceStatus,
  AttendanceSummary,
  CalendarEvent,
  CourseOverview,
  CurriculumWeek,
  ExamResult,
  GradeReport,
  Klass,
  Notice,
  NotifLog,
  OnlineUser,
  ScheduleItem,
  SessionChange,
  VocabTest,
  WrongItem,
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
    { id: 'n1', tag: '공지사항', title: '수업 일정', author: '김강사' },
    { id: 'n2', tag: '공지', title: '필요서류 요청받음', author: '김강사' },
    { id: 'n3', tag: '공지', title: '자습 운영 시간 안내', author: '김강사' },
    { id: 'n4', tag: '공지', title: '훈련생 필수 제출 서류', author: '김강사' },
  ])

export const fetchSchedule = (): Promise<ScheduleItem[]> =>
  delay([{ id: 's1', date: '2026-09-07', title: '종강' }])

export const fetchCalendarEvents = (): Promise<CalendarEvent[]> =>
  delay([
    { date: '2026-06-30', label: '개강', tone: 'green' },
    { date: '2026-09-07', label: '종강', tone: 'red' },
  ])

const ROLES: OnlineUser['role'][] = ['수강생', '강사', '매니저']
// 데모용 가명 (실명 아님)
const NAMES = [
  '홍길동', '김철수', '이영희', '박민수', '최지우', '정하늘', '강바다', '윤소라',
  '임가온', '오태양', '한별이', '서은결', '조아름', '신도담', '문누리', '배슬기',
  '남기찬', '유보라', '전초롱', '고나무', '허수아', '노을찬',
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

// 과제 이행도 목업
export const fetchAssignments = (): Promise<Assignment[]> =>
  delay([
    {
      id: 'a1',
      title: '독서 지문 분석 - 「양자역학과 관측」',
      category: '독서 분석',
      dueDate: '2026-07-04',
      status: '완료',
      score: 95,
      feedback: '문단별 중심문장 추출이 정확합니다.',
    },
    {
      id: 'a2',
      title: '주간 어휘 테스트 (7월 1주차)',
      category: '어휘 테스트',
      dueDate: '2026-07-05',
      status: '완료',
      score: 88,
      feedback: '한자어 의미 구분 보완 필요.',
    },
    {
      id: 'a3',
      title: '문학 감상문 - 김소월 「진달래꽃」',
      category: '문학 감상',
      dueDate: '2026-07-07',
      status: '미흡',
      score: 62,
      feedback: '화자의 정서 근거를 지문에서 찾아 서술하세요.',
    },
    {
      id: 'a4',
      title: '오답 정리 - 6월 모의평가 독서',
      category: '오답 정리',
      dueDate: '2026-07-08',
      status: '미제출',
      score: null,
      feedback: '',
    },
    {
      id: 'a5',
      title: '독서 지문 분석 - 「소유권과 점유」',
      category: '독서 분석',
      dueDate: '2026-07-10',
      status: '완료',
      score: 90,
      feedback: '논리 구조 요약이 명료합니다.',
    },
  ])

// 오답노트 목업 — 갈래별로 다양하게
export const fetchWrongItems = (): Promise<WrongItem[]> =>
  delay([
    {
      id: 'w1',
      date: '2026-06-04',
      source: '6월 모의평가 23번',
      genre: '독서(과학)',
      questionType: '세부 정보 추론',
      reason: '지문의 조건절을 놓쳐 반대로 해석',
      mastered: false,
    },
    {
      id: 'w2',
      date: '2026-06-04',
      source: '6월 모의평가 31번',
      genre: '독서(인문)',
      questionType: '관점 비교',
      reason: '두 학자의 견해 차이 혼동',
      mastered: true,
    },
    {
      id: 'w3',
      date: '2026-05-20',
      source: '5월 학력평가 27번',
      genre: '고전소설',
      questionType: '인물 심리 파악',
      reason: '고어 어휘 미숙지',
      mastered: false,
    },
    {
      id: 'w4',
      date: '2026-05-20',
      source: '5월 학력평가 34번',
      genre: '현대시',
      questionType: '표현상 특징',
      reason: '반어·역설 구분 실수',
      mastered: false,
    },
    {
      id: 'w5',
      date: '2026-07-02',
      source: '7월 학력평가 18번',
      genre: '독서(사회)',
      questionType: '구체적 사례 적용',
      reason: '보기 사례를 지문 원리에 대응 실패',
      mastered: false,
    },
    {
      id: 'w6',
      date: '2026-07-02',
      source: '7월 학력평가 40번',
      genre: '고전시가',
      questionType: '화자의 정서',
      reason: '시적 화자와 대상 혼동',
      mastered: true,
    },
  ])

// 주간 어휘 테스트 누적 목업
export const fetchVocabTests = (): Promise<VocabTest[]> =>
  delay([
    { id: 'v1', week: '6월 2주차', date: '2026-06-14', score: 32, total: 40 },
    { id: 'v2', week: '6월 3주차', date: '2026-06-21', score: 35, total: 40 },
    { id: 'v3', week: '6월 4주차', date: '2026-06-28', score: 34, total: 40 },
    { id: 'v4', week: '7월 1주차', date: '2026-07-05', score: 38, total: 40 },
  ])

// 오늘 등하원 알림 발송 이력 목업
export const fetchNotifLogs = (): Promise<NotifLog[]> =>
  delay([
    { id: 'nl1', time: '18:02', student: '김철수', type: '하원', channel: '알림톡', to: '어머니 010-****-2841' },
    { id: 'nl2', time: '18:00', student: '이동욱', type: '하원', channel: '알림톡', to: '아버지 010-****-1092' },
    { id: 'nl3', time: '09:04', student: '김철수', type: '등원', channel: '알림톡', to: '어머니 010-****-2841' },
    { id: 'nl4', time: '09:02', student: '이동욱', type: '등원', channel: '알림톡', to: '아버지 010-****-1092' },
    { id: 'nl5', time: '09:24', student: '이영희', type: '등원', channel: 'SMS', to: '어머니 010-****-7733' },
  ])

// 수강/강의 관리 목업 ──────────────────────────────
export const fetchClasses = (): Promise<Klass[]> =>
  delay([
    {
      id: 'c1',
      name: '고3 독서·문학 심화반',
      grade: '고3',
      level: '심화',
      school: '공통',
      studentCount: 14,
      capacity: 16,
      schedule: '월·수·금 19:00',
      teacher: '김강사',
      progress: 68,
    },
    {
      id: 'c2',
      name: '고2 국어 내신대비반 (용죽고)',
      grade: '고2',
      level: '내신대비',
      school: '용죽고',
      studentCount: 12,
      capacity: 15,
      schedule: '화·목 18:00',
      teacher: '박강사',
      progress: 42,
    },
    {
      id: 'c3',
      name: '고1 기초 다지기반',
      grade: '고1',
      level: '기초',
      school: '공통',
      studentCount: 9,
      capacity: 15,
      schedule: '토 10:00',
      teacher: '이강사',
      progress: 25,
    },
  ])

export const fetchCurriculum = (): Promise<CurriculumWeek[]> =>
  delay([
    { week: 1, topic: '독서 - 인문', detail: '논지 전개와 관점 비교', status: '완료' },
    { week: 2, topic: '독서 - 사회', detail: '경제/법 지문 정보 처리', status: '완료' },
    { week: 3, topic: '독서 - 과학/기술', detail: '원리·과정 도식화', status: '완료' },
    { week: 4, topic: '문학 - 현대시', detail: '화자·정서·표현', status: '진행중' },
    { week: 5, topic: '문학 - 고전시가', detail: '갈래별 관습과 어휘', status: '예정' },
    { week: 6, topic: '문학 - 현대소설', detail: '서술상 특징과 시점', status: '예정' },
    { week: 7, topic: '선택 - 언어와 매체', detail: '음운·문법 요소', status: '예정' },
    { week: 8, topic: '실전 모의고사', detail: '시간 운용 전략', status: '예정' },
  ])

export const fetchSessionChanges = (): Promise<SessionChange[]> =>
  delay([
    {
      id: 'sc1',
      date: '2026-07-15',
      type: '휴강',
      target: '고3 독서·문학 심화반',
      reason: '강사 학회 참석',
      makeupDate: '2026-07-19',
    },
    {
      id: 'sc2',
      date: '2026-07-11',
      type: '보강',
      target: '김철수 (고3 심화반)',
      reason: '7/7 결석 보충',
      makeupDate: null,
    },
    {
      id: 'sc3',
      date: '2026-07-22',
      type: '휴강',
      target: '전체',
      reason: '학원 정기 점검',
      makeupDate: '2026-07-24',
    },
  ])

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
