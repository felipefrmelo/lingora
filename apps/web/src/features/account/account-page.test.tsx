import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, createRootRoute, createRouter, RouterProvider } from '@tanstack/react-router'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext, SignInRequired, type AuthState } from '../../auth/context'
import { AccountBoundary } from './account-page'
import { AccountApiError } from './api'

const api = vi.hoisted(() => ({ bootstrap: vi.fn(), current: vi.fn() }))
vi.mock('./api', async (original) => ({ ...await original<typeof import('./api')>(), createAccountApi: () => api }))

const account = { id: 'one', created_at: '2026-11-04T12:00:00Z' }
const login = vi.fn()
const logout = vi.fn()

function renderAccount(overrides: Partial<AuthState> = {}) {
  const auth: AuthState = {
    configured: true, isLoading: false, isAuthenticated: true, subject: 'auth0|one',
    name: 'Student One', email: 'one@example.test', error: null,
    login, logout, getAccessToken: vi.fn().mockResolvedValue('access-token'), ...overrides,
  }
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  const route = createRootRoute({ component: () => <AccountBoundary><h1>Account ready</h1></AccountBoundary> })
  const router = createRouter({ routeTree: route, history: createMemoryHistory({ initialEntries: ['/'] }) })
  render(<QueryClientProvider client={client}><AuthContext.Provider value={auth}><RouterProvider router={router} /></AuthContext.Provider></QueryClientProvider>)
}

beforeEach(() => {
  vi.resetAllMocks()
  api.bootstrap.mockResolvedValue(account)
  api.current.mockResolvedValue(account)
})

describe('private account page', () => {
  it('does not fetch or display private data before authentication', async () => {
    renderAccount({ isAuthenticated: false, subject: undefined })
    expect(await screen.findByText('Your learning space is private')).toBeVisible()
    expect(api.bootstrap).not.toHaveBeenCalled()
    expect(screen.queryByText('one@example.test')).not.toBeInTheDocument()
  })

  it('loads the current student only after successful provisioning', async () => {
    api.current.mockImplementation(async () => {
      expect(api.bootstrap).toHaveBeenCalledTimes(1)
      return account
    })
    renderAccount()
    expect(await screen.findByRole('heading', { name: 'Account ready' })).toBeVisible()
    expect(api.current).toHaveBeenCalledTimes(1)
  })

  it('offers explicit sign-in when silent renewal requires interaction', async () => {
    api.bootstrap.mockRejectedValue(new SignInRequired())
    renderAccount()
    await userEvent.click(await screen.findByRole('button', { name: 'Sign in' }))
    expect(login).toHaveBeenCalledTimes(1)
    expect(api.current).not.toHaveBeenCalled()
  })

  it('retains the session and retries after an unavailable API', async () => {
    api.bootstrap.mockRejectedValueOnce(new AccountApiError(503)).mockResolvedValue(account)
    renderAccount()
    const retry = await screen.findByRole('button', { name: 'Try again' })
    expect(screen.getByText('Your sign-in is still active. Please try again shortly.')).toBeVisible()
    await userEvent.click(retry)
    expect(await screen.findByRole('heading', { name: 'Account ready' })).toBeVisible()
    expect(logout).not.toHaveBeenCalled()
  })

  it('shows verification feedback and grants no private access', async () => {
    renderAccount({ error: 'verification_required', isAuthenticated: false })
    expect(await screen.findByRole('heading', { name: 'Check your email' })).toBeVisible()
    await waitFor(() => expect(api.bootstrap).not.toHaveBeenCalled())
  })
})
