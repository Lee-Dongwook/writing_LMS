import { useState, type FormEvent, type ReactNode } from 'react'
import { Card, Eyebrow, PillButton } from '../components/ui'
import { useAuthStore } from '../store/authStore'
import { ApiError } from '../lib/apiClient'

type Mode = 'login' | 'register'

export default function Login() {
  const login = useAuthStore((s) => s.login)
  const register = useAuthStore((s) => s.register)

  const [mode, setMode] = useState<Mode>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  const isLogin = mode === 'login'

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (isLogin) {
        await login(email, password)
      } else {
        await register(email, password, name.trim() || undefined)
      }
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else if (err instanceof TypeError) {
        // fetch 자체 실패(네트워크/CORS) → 서버 미기동 가능성
        setError('서버에 연결할 수 없습니다. 백엔드(:8000)가 실행 중인지 확인해 주세요.')
      } else {
        setError('알 수 없는 오류가 발생했습니다.')
      }
    } finally {
      setSubmitting(false)
    }
  }

  function switchMode(next: Mode) {
    setMode(next)
    setError(null)
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="w-full max-w-md">
        <div className="mb-6 text-center">
          <Eyebrow>WRITING LMS</Eyebrow>
          <h1 className="mt-2 text-2xl font-extrabold text-ink">
            {isLogin ? '로그인' : '회원가입'}
          </h1>
          <p className="mt-1 text-sm text-slate-500">
            수능 국어 비문학 첨삭 · 자기주도학습
          </p>
        </div>

        <Card className="bg-white ring-1 ring-line">
          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <Field label="이름 (선택)">
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  autoComplete="name"
                  placeholder="홍길동"
                  className={inputCls}
                />
              </Field>
            )}

            <Field label="이메일">
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="email"
                placeholder="you@example.com"
                className={inputCls}
              />
            </Field>

            <Field label="비밀번호">
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={isLogin ? 'current-password' : 'new-password'}
                placeholder="••••••••"
                className={inputCls}
              />
            </Field>

            {error && (
              <p className="rounded-lg bg-brand-50 px-3 py-2 text-sm text-brand-700">
                {error}
              </p>
            )}

            <PillButton
              type="submit"
              disabled={submitting}
              className="w-full disabled:opacity-60"
            >
              {submitting ? '처리 중…' : isLogin ? '로그인' : '가입하고 시작하기'}
            </PillButton>
          </form>
        </Card>

        <p className="mt-4 text-center text-sm text-slate-500">
          {isLogin ? '계정이 없으신가요? ' : '이미 계정이 있으신가요? '}
          <button
            type="button"
            onClick={() => switchMode(isLogin ? 'register' : 'login')}
            className="font-semibold text-brand-600 hover:underline"
          >
            {isLogin ? '회원가입' : '로그인'}
          </button>
        </p>
      </div>
    </div>
  )
}

const inputCls =
  'w-full rounded-lg border border-line bg-white px-3.5 py-2.5 text-sm text-ink ' +
  'placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-100'

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-slate-600">{label}</span>
      {children}
    </label>
  )
}
