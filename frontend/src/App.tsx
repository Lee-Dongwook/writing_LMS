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
import { useUiStore } from './store/uiStore'

export default function App() {
  const activeView = useUiStore((s) => s.activeView)

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
