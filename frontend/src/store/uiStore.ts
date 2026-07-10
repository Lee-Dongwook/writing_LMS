import { create } from 'zustand'

export type ActiveView = 'dashboard' | 'attendance'

interface UiState {
  sidebarOpen: boolean
  classroomExpanded: boolean
  onlineModalOpen: boolean
  activeView: ActiveView
  toggleSidebar: () => void
  toggleClassroom: () => void
  openOnlineModal: () => void
  closeOnlineModal: () => void
  setActiveView: (view: ActiveView) => void
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  classroomExpanded: true,
  onlineModalOpen: false,
  activeView: 'dashboard',
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleClassroom: () => set((s) => ({ classroomExpanded: !s.classroomExpanded })),
  openOnlineModal: () => set({ onlineModalOpen: true }),
  closeOnlineModal: () => set({ onlineModalOpen: false }),
  setActiveView: (view) => set({ activeView: view }),
}))
