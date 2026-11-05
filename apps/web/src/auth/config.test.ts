import { describe, expect, it } from 'vitest'
import { readAuthConfig } from './config'
import { classifyAuthError } from './context'

const environment = {
  VITE_AUTH0_DOMAIN: 'auth.example.test',
  VITE_AUTH0_CLIENT_ID: 'public-client',
  VITE_AUTH0_AUDIENCE: 'https://lingora.local/api',
  VITE_AUTH0_REDIRECT_URI: 'http://localhost:5173/auth/callback',
}

describe('Auth0 configuration', () => {
  it('requires complete public configuration and an exact same-origin callback', () => {
    expect(readAuthConfig(environment, 'http://localhost:5173')?.clientId).toBe('public-client')
    expect(readAuthConfig({}, 'http://localhost:5173')).toBeNull()
    expect(readAuthConfig({ ...environment, VITE_AUTH0_CLIENT_ID: '' }, 'http://localhost:5173')).toBeNull()
    expect(readAuthConfig({ ...environment, VITE_AUTH0_REDIRECT_URI: 'https://attacker.example/auth/callback' }, 'http://localhost:5173')).toBeNull()
    expect(readAuthConfig({ ...environment, VITE_AUTH0_REDIRECT_URI: 'http://localhost:5173/other' }, 'http://localhost:5173')).toBeNull()
  })

  it('classifies known failures without returning provider descriptions', () => {
    expect(classifyAuthError(new Error('lingora_email_verification_required'))).toBe('verification_required')
    expect(classifyAuthError({ error: 'login_required' })).toBe('interaction_required')
    expect(classifyAuthError({ error: 'consent_required' })).toBe('interaction_required')
    expect(classifyAuthError({ error: 'access_denied' })).toBe('access_denied')
    expect(classifyAuthError(new Error('private provider error'))).toBe('unavailable')
  })
})
