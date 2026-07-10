import Sidebar from './components/layout/Sidebar'
import Header from './components/layout/Header'
import Dashboard from './pages/Dashboard'
import OnlineUsersButton from './components/OnlineUsersButton'
import OnlineUsersModal from './components/OnlineUsersModal'

export default function App() {
  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header />
        <main className="flex-1 overflow-y-auto thin-scroll">
          <Dashboard />
        </main>
      </div>

      <OnlineUsersButton />
      <OnlineUsersModal />
    </div>
  )
}
