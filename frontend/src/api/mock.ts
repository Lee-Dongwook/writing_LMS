import type {
  CalendarEvent,
  CourseOverview,
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
