import { create } from 'zustand'
import {
  fetchMe,
  loginRequest,
  registerRequest,
  type AuthUser,
} from '../api/auth'
import { setUnauthorizedHandler, tokenStore } from '../lib/apiClient'

// loading: 부팅 중(저장 토큰 검증) · authenticated: 로그인됨 · unauthenticated: 미로그인
type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

interface AuthState {
  status: AuthStatus
  user: AuthUser | null
  // 앱 시작 시 저장된 토큰으로 세션 복구
  bootstrap: () => Promise<void>
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string, name?: string) => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  status: 'loading',
  user: null,

  bootstrap: async () => {
    if (!tokenStore.get()) {
      set({ status: 'unauthenticated', user: null })
      return
    }
    try {
      const user = await fetchMe()
      set({ user, status: 'authenticated' })
    } catch {
      // 토큰 만료/무효 → 정리
      tokenStore.clear()
      set({ user: null, status: 'unauthenticated' })
    }
  },

  login: async (email, password) => {
    const { access_token } = await loginRequest(email, password)
    tokenStore.set(access_token)
    const user = await fetchMe()
    set({ user, status: 'authenticated' })
  },

  register: async (email, password, name) => {
    await registerRequest(email, password, name)
    // 가입 직후 자동 로그인
    const { access_token } = await loginRequest(email, password)
    tokenStore.set(access_token)
    const user = await fetchMe()
    set({ user, status: 'authenticated' })
  },

  logout: () => {
    tokenStore.clear()
    set({ user: null, status: 'unauthenticated' })
  },
}))

// 어떤 요청이든 401이면 전역 로그아웃 처리
setUnauthorizedHandler(() => {
  useAuthStore.setState({ user: null, status: 'unauthenticated' })
})
