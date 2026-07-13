// 백엔드 /auth 엔드포인트 계약.
// register: JSON, login: form-urlencoded(OAuth2), me: Bearer.
import { apiRequest } from '../lib/apiClient'

// 백엔드 UserRead 스키마와 1:1 대응
export interface AuthUser {
  uuid: string
  email: string
  name: string | null
  is_active: boolean
  is_admin: boolean
  role: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export const registerRequest = (
  email: string,
  password: string,
  name?: string,
): Promise<AuthUser> =>
  apiRequest<AuthUser>('/auth/register', {
    method: 'POST',
    auth: false,
    body: { email, password, name: name || null },
  })

// OAuth2PasswordRequestForm 규격: username 필드에 이메일을 담는다.
export const loginRequest = (
  email: string,
  password: string,
): Promise<TokenResponse> =>
  apiRequest<TokenResponse>('/auth/login', {
    method: 'POST',
    auth: false,
    form: { username: email, password },
  })

export const fetchMe = (): Promise<AuthUser> => apiRequest<AuthUser>('/auth/me')
