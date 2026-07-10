import { useUiStore } from '../store/uiStore'

export default function OnlineUsersButton() {
  const openOnlineModal = useUiStore((s) => s.openOnlineModal)

  return (
    <button
      onClick={openOnlineModal}
      aria-label="현재 접속자 보기"
      className="fixed bottom-6 right-6 z-30 flex h-12 w-12 items-center justify-center rounded-full bg-brand-500 text-white shadow-lg shadow-brand-500/30 transition hover:bg-brand-600 active:scale-95"
    >
      <span className="text-xl">🧑‍🤝‍🧑</span>
    </button>
  )
}
