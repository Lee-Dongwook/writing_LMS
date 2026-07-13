import Sidebar from './components/layout/Sidebar'
import Header from './components/layout/Header'
import Dashboard from './pages/Dashboard'
import Attendance from './pages/Attendance'
import Grades from './pages/Grades'
import Assignments from './pages/Assignments'
import Classes from './pages/Classes'
import Communication from './pages/Communication'
import OnlineUsersButton from './components/OnlineUsersButton'
import OnlineUsersModal from './components/OnlineUsersModal'
import Login from './pages/Login'
import { useUiStore } from './store/uiStore'
import { useAuthStore } from './store/authStore'
import { useEffect } from 'react'

export default function App() {
  const activeView = useUiStore((s) => s.activeView)
  const status = useAuthStore((s) => s.status)
  const bootstrap = useAuthStore((s) => s.bootstrap)

  // 앱 시작 시 저장된 토큰으로 세션 복구
  useEffect(() => {
    void bootstrap()
  }, [bootstrap])

  if (status === 'loading') {
    return (
      <div className="flex h-screen items-center justify-center bg-surface">
        <span className="text-sm text-slate-500">불러오는 중…</span>
      </div>
    )
  }

  if (status === 'unauthenticated') {
    return <Login />
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-y-auto thin-scroll">
          {activeView === 'attendance' ? (
            <Attendance />
          ) : activeView === 'grades' ? (
            <Grades />
          ) : activeView === 'assignments' ? (
            <Assignments />
          ) : activeView === 'classes' ? (
            <Classes />
          ) : activeView === 'communication' ? (
            <Communication />
          ) : (
            <Dashboard />
          )}
        </main>
      </div>

      <OnlineUsersButton />
      <OnlineUsersModal />
    </div>
  )
}
