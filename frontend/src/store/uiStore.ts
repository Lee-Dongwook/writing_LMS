import { create } from 'zustand'

export type ActiveView =
  | 'dashboard'
  | 'attendance'
  | 'grades'
  | 'assignments'
  | 'classes'
  | 'communication'

// 데모용 앱 권한(역할). 온라인 유저의 role(수강생/강사/매니저)과는 별개다.
export type AppRole = 'director' | 'student' | 'parent'

export const APP_ROLES: { value: AppRole; label: string; emoji: string }[] = [
  { value: 'director', label: '원장', emoji: '🧑‍💼' },
  { value: 'student', label: '학생', emoji: '🧑‍🎓' },
  { value: 'parent', label: '학부모', emoji: '👪' },
]

interface UiState {
  sidebarOpen: boolean
  classroomExpanded: boolean
  onlineModalOpen: boolean
  activeView: ActiveView
  role: AppRole
  toggleSidebar: () => void
  toggleClassroom: () => void
  openOnlineModal: () => void
  closeOnlineModal: () => void
  setActiveView: (view: ActiveView) => void
  setRole: (role: AppRole) => void
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  classroomExpanded: true,
  onlineModalOpen: false,
  activeView: 'dashboard',
  role: 'student',
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleClassroom: () => set((s) => ({ classroomExpanded: !s.classroomExpanded })),
  openOnlineModal: () => set({ onlineModalOpen: true }),
  closeOnlineModal: () => set({ onlineModalOpen: false }),
  setActiveView: (view) => set({ activeView: view }),
  setRole: (role) => set({ role }),
}))
