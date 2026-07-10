import { useQuery } from '@tanstack/react-query'
import {
  fetchAttendance,
  fetchCalendarEvents,
  fetchCourseOverview,
  fetchNotices,
  fetchOnlineUsers,
  fetchSchedule,
} from './mock'

export const useCourseOverview = () =>
  useQuery({ queryKey: ['course-overview'], queryFn: fetchCourseOverview })

export const useNotices = () =>
  useQuery({ queryKey: ['notices'], queryFn: fetchNotices })

export const useSchedule = () =>
  useQuery({ queryKey: ['schedule'], queryFn: fetchSchedule })

export const useCalendarEvents = () =>
  useQuery({ queryKey: ['calendar-events'], queryFn: fetchCalendarEvents })

export const useAttendance = () =>
  useQuery({ queryKey: ['attendance'], queryFn: fetchAttendance })

export const useOnlineUsers = (enabled: boolean) =>
  useQuery({ queryKey: ['online-users'], queryFn: fetchOnlineUsers, enabled })
