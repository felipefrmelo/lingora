import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, createRouter, RouterProvider } from '@tanstack/react-router'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import { AuthContext, type AuthState } from '../../auth/context'
import { routeTree } from '../../routes'

const api = vi.hoisted(() => ({ list: vi.fn(), get: vi.fn(), prepare: vi.fn(), abandon: vi.fn(), access: vi.fn(), setAccess: vi.fn() }))
vi.mock('./api', () => ({ useConversationApi: () => api }))
vi.mock('../account/api', async original => ({ ...await original<typeof import('../account/api')>(), createAccountApi: () => ({ bootstrap: async () => ({ id: 'one' }), current: async () => ({ id: 'one' }) }) }))
const auth: AuthState = { configured: true, isLoading: false, isAuthenticated: true, subject: 'one', error: null, login: vi.fn(), logout: vi.fn(), getAccessToken: vi.fn() }
const session = { id: 'session-one', lesson_id: 'lesson-one', status: 'READY', cefr: 'A2', correction_mode: 'balanced', save_examples: true, version: 1, created_at: '2026-11-05T00:00:00Z', completed_at: null, feedback: null }
function app(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  const router = createRouter({ routeTree, history: createMemoryHistory({ initialEntries: [path] }) })
  render(<QueryClientProvider client={client}><AuthContext.Provider value={auth}><RouterProvider router={router} /></AuthContext.Provider></QueryClientProvider>)
}
beforeEach(() => { vi.resetAllMocks(); api.get.mockResolvedValue(session); api.list.mockResolvedValue([session]); api.access.mockResolvedValue({ enabled: false }); api.setAccess.mockResolvedValue({ enabled: true }) })

it('shows recovery instructions and requires explicit MCP enablement', async () => {
  app('/app/sessions/session-one')
  expect(await screen.findByRole('heading', { name: 'Your A2 conversation' })).toBeVisible()
  expect(await screen.findByText('ChatGPT access: disabled')).toBeVisible()
  await userEvent.click(screen.getByRole('button', { name: 'Enable ChatGPT access' }))
  expect(api.setAccess).toHaveBeenCalledWith(true)
})

it('renders saved feedback and examples in readable form', async () => {
  api.get.mockResolvedValue({ ...session, status: 'COMPLETED', completed_at: '2026-11-05T00:00:00Z', feedback: { summary: 'You used clear sentences.', strengths: ['Clear answers'], priorities: ['Past tense'], observations: [{ skill: 'Grammar', feedback: 'Review past tense.', example: 'I go yesterday', correction: 'I went yesterday' }] } })
  app('/app/sessions/session-one')
  expect(await screen.findByText('You used clear sentences.')).toBeVisible()
  expect(screen.getByText('Example: I go yesterday')).toBeVisible()
  expect(screen.queryByRole('button', { name: 'Abandon session' })).not.toBeInTheDocument()
})
