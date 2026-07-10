import {
  useCalendarEvents,
  useCourseOverview,
  useNotices,
  useSchedule,
} from '../api/hooks'
import WelcomeCard from '../components/dashboard/WelcomeCard'
import ProgressCard from '../components/dashboard/ProgressCard'
import NoticeCard from '../components/dashboard/NoticeCard'
import Calendar from '../components/dashboard/Calendar'
import ScheduleList from '../components/dashboard/ScheduleList'

export default function Dashboard() {
  const overview = useCourseOverview()
  const notices = useNotices()
  const schedule = useSchedule()
  const events = useCalendarEvents()

  return (
    <div className="mx-auto max-w-6xl space-y-5 p-4 sm:p-6">
      {/* 상단 4분할 */}
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-4">
        <div className="lg:col-span-2">
          <WelcomeCard data={overview.data} loading={overview.isLoading} />
        </div>
        <ProgressCard
          title="권장 진도율"
          percent={overview.data?.attendanceRate ?? 0}
          count={overview.data?.attendanceCount ?? '0/0'}
          loading={overview.isLoading}
        />
        <ProgressCard
          title="과제 제출"
          percent={overview.data?.submitRate ?? 0}
          count={overview.data?.submitCount ?? '0/0'}
          loading={overview.isLoading}
        />
      </div>

      {/* 공지사항 */}
      <NoticeCard notices={notices.data} loading={notices.isLoading} />

      {/* 학습 캘린더 + 주요 학습일정 */}
      <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h3 className="mb-5 text-base font-bold text-slate-800">학습 캘린더</h3>
        <div className="flex flex-col gap-6 lg:flex-row">
          <div className="flex-1">
            <Calendar events={events.data} />
          </div>
          <ScheduleList items={schedule.data} loading={schedule.isLoading} />
        </div>
      </div>
    </div>
  )
}
