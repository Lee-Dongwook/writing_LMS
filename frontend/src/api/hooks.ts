import { useQuery } from '@tanstack/react-query'
import {
  fetchAssignments,
  fetchAttendance,
  fetchCalendarEvents,
  fetchCourseOverview,
  fetchGradeReport,
  fetchNotices,
  fetchOnlineUsers,
  fetchSchedule,
  fetchVocabTests,
  fetchWrongItems,
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

export const useGradeReport = () =>
  useQuery({ queryKey: ['grade-report'], queryFn: fetchGradeReport })

export const useAssignments = () =>
  useQuery({ queryKey: ['assignments'], queryFn: fetchAssignments })

export const useWrongItems = () =>
  useQuery({ queryKey: ['wrong-items'], queryFn: fetchWrongItems })

export const useVocabTests = () =>
  useQuery({ queryKey: ['vocab-tests'], queryFn: fetchVocabTests })

export const useOnlineUsers = (enabled: boolean) =>
  useQuery({ queryKey: ['online-users'], queryFn: fetchOnlineUsers, enabled })
