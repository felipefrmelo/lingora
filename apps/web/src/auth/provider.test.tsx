import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import type { ReactNode } from 'react'
import { AuthProvider } from './provider'
import { useAuth } from './context'

const sdk = vi.hoisted(() => ({
  isLoading: false,
  isAuthenticated: true,
  user: { sub: 'auth0|one', name: 'One', email: 'one@example.test' } as { sub: string; name: string; email: string } | undefined,
  error: undefined as Error | undefined,
  loginWithRedirect: vi.fn(),
  logout: vi.fn(),
  getAccessTokenSilently: vi.fn(),
}))

vi.mock('@auth0/auth0-react', () => ({
  Auth0Provider: ({ children }: { children: ReactNode }) => <>{children}</>,
  useAuth0: () => sdk,
}))

const config = { domain: 'auth.example.test', clientId: 'public-client', audience: 'https://lingora.local/api', redirectUri: 'http://localhost:5173/auth/callback' }

function Probe() {
  const auth = useAuth()
  return <>
    <span>{auth.email || 'anonymous'}</span>
    <button onClick={() => void auth.login(true)}>Register</button>
    <button onClick={() => void auth.logout()}>Logout</button>
  </>
}

function app(client: QueryClient) {
  return <QueryClientProvider client={client}><AuthProvider config={config} onRedirect={() => {}}><Probe /></AuthProvider></QueryClientProvider>
}

beforeEach(() => {
  vi.resetAllMocks()
  sdk.user = { sub: 'auth0|one', name: 'One', email: 'one@example.test' }
  sdk.error = undefined
  sdk.isAuthenticated = true
  sdk.loginWithRedirect.mockResolvedValue(undefined)
  sdk.logout.mockResolvedValue(undefined)
})

describe('Auth0 SDK bridge', () => {
  it('uses the SDK registration flow', async () => {
    const client = new QueryClient()
    render(app(client))
    await userEvent.click(screen.getByRole('button', { name: 'Register' }))
    expect(sdk.loginWithRedirect).toHaveBeenCalledWith({ authorizationParams: { screen_hint: 'signup' } })
  })

  it('clears account data before calling Auth0 logout', async () => {
    const client = new QueryClient()
    client.setQueryData(['account', 'auth0|one'], { id: 'one' })
    sdk.logout.mockImplementation(async () => {
      expect(client.getQueryData(['account', 'auth0|one'])).toBeUndefined()
    })
    render(app(client))
    await userEvent.click(screen.getByRole('button', { name: 'Logout' }))
    expect(sdk.logout).toHaveBeenCalledWith({ logoutParams: { returnTo: window.location.origin } })
  })

  it('removes the previous identity cache when accounts change', async () => {
    const client = new QueryClient()
    client.setQueryData(['account', 'auth0|one'], { id: 'one' })
    const view = render(app(client))
    sdk.user = { sub: 'google-oauth2|two', name: 'Two', email: 'two@example.test' }
    client.setQueryData(['account', 'google-oauth2|two'], { id: 'two' })
    view.rerender(app(client))
    await waitFor(() => expect(client.getQueryData(['account', 'auth0|one'])).toBeUndefined())
    expect(client.getQueryData(['account', 'google-oauth2|two'])).toEqual({ id: 'two' })
    expect(screen.queryByText('one@example.test')).not.toBeInTheDocument()
    expect(screen.getByText('two@example.test')).toBeVisible()
  })
})
