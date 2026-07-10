import { create } from 'zustand'

interface UiState {
  sidebarOpen: boolean
  classroomExpanded: boolean
  onlineModalOpen: boolean
  toggleSidebar: () => void
  toggleClassroom: () => void
  openOnlineModal: () => void
  closeOnlineModal: () => void
}

export const useUiStore = create<UiState>((set) => ({
  sidebarOpen: true,
  classroomExpanded: true,
  onlineModalOpen: false,
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleClassroom: () => set((s) => ({ classroomExpanded: !s.classroomExpanded })),
  openOnlineModal: () => set({ onlineModalOpen: true }),
  closeOnlineModal: () => set({ onlineModalOpen: false }),
}))
