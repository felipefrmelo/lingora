import { createContext, useContext } from 'react'

export type AuthErrorCode = 'verification_required' | 'interaction_required' | 'access_denied' | 'unavailable'

export type AuthState = {
  configured: boolean
  isLoading: boolean
  isAuthenticated: boolean
  subject?: string
  name?: string
  email?: string
  error: AuthErrorCode | null
  login: (signup?: boolean) => Promise<void>
  logout: () => Promise<void>
  getAccessToken: (force?: boolean) => Promise<string>
}

export class SignInRequired extends Error {
  constructor() { super('Please sign in to continue.') }
}

export const AuthContext = createContext<AuthState | null>(null)

export function useAuth(): AuthState {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('AuthProvider is required')
  return auth
}

export function classifyAuthError(error: unknown): AuthErrorCode {
  if (error instanceof Error && error.message.includes('lingora_email_verification_required')) {
    return 'verification_required'
  }
  if (typeof error === 'object' && error !== null && 'error' in error) {
    if (['login_required', 'consent_required', 'interaction_required'].includes(String(error.error))) {
      return 'interaction_required'
    }
    if (error.error === 'access_denied') return 'access_denied'
  }
  return 'unavailable'
}
