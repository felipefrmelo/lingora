import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, createRouter, RouterProvider } from '@tanstack/react-router'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, it, vi } from 'vitest'
import { AuthContext, type AuthState } from '../../auth/context'
import { PrivateApiError } from '../../auth/private-api'
import { routeTree } from '../../routes'
import fixture from './lesson.fixture.json'
import type { Attempt, Lesson } from './api'

const api = vi.hoisted(() => ({ catalog: vi.fn(), prepare: vi.fn(), jobs: vi.fn(), job: vi.fn(), lesson: vi.fn(), attempts: vi.fn(), submit: vi.fn() }))
vi.mock('./api', () => ({ useLessonApi: () => api }))
vi.mock('../account/api', async original => ({ ...await original<typeof import('../account/api')>(), createAccountApi: () => ({ bootstrap: async () => ({ id: 'one' }), current: async () => ({ id: 'one' }) }) }))
const auth: AuthState = { configured: true, isLoading: false, isAuthenticated: true, subject: 'one', error: null, login: vi.fn(), logout: vi.fn(), getAccessToken: vi.fn() }
const lesson = fixture as Lesson
const job = { id: 'job-one', status: 'queued', content_id: 'content-one', cefr: 'B1', level_reason: 'Your selected level', lesson_id: null, error_code: null, created_at: '2026-11-05T00:00:00Z' }
let saved: Attempt[]
function app(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  const router = createRouter({ routeTree, history: createMemoryHistory({ initialEntries: [path] }) })
  const tree = (identity: AuthState) => <QueryClientProvider client={client}><AuthContext.Provider value={identity}><RouterProvider router={router} /></AuthContext.Provider></QueryClientProvider>
  const view = render(tree(auth))
  return { router, switchAccount: (identity: AuthState) => view.rerender(tree(identity)) }
}
beforeEach(() => {
  vi.resetAllMocks()
  vi.spyOn(window, 'confirm').mockReturnValue(false)
  saved = []
  api.catalog.mockResolvedValue({ items: [fixture.source], total: 1, generation_available: true })
  api.jobs.mockResolvedValue({ items: [], total: 0 })
  api.job.mockResolvedValue(job)
  api.prepare.mockResolvedValue(job)
  api.lesson.mockResolvedValue(lesson)
  api.attempts.mockImplementation(async () => structuredClone(saved))
  api.submit.mockImplementation(async (_id: string, answers: string[][]) => {
    const result: Attempt = { id: 'attempt-one', lesson_id: lesson.id, created_at: '2026-11-05T00:00:00Z', answers, correct: 1, total: 5, results: lesson.exercises.map((exercise, index) => ({ correct: index === 0, expected: ['Accepted answer'], explanation: 'A clear explanation of this answer.', skill: exercise.skill })) }
    saved.push(result); return result
  })
})

it('offers attributed content and keeps a creation key across an uncertain retry', async () => {
  api.prepare.mockRejectedValueOnce(new Error('lost response'))
  app('/app/learn')
  await screen.findByRole('heading', { name: 'A garden' })
  expect(screen.getByRole('link', { name: 'GOV.UK · Original brief' })).toHaveAttribute('href', fixture.source.url)
  await userEvent.selectOptions(screen.getByLabelText('Lesson level'), 'B2')
  await userEvent.click(screen.getByRole('button', { name: 'Make this my lesson' }))
  await screen.findByRole('heading', { name: 'We couldn’t complete that request' })
  await userEvent.click(screen.getByRole('button', { name: 'Make this my lesson' }))
  expect(await screen.findByRole('heading', { name: 'Your lesson is taking shape.' })).toBeVisible()
  expect(api.prepare.mock.calls[0]?.[1]).toBe(api.prepare.mock.calls[1]?.[1])
  expect(api.prepare.mock.calls[1]?.[0]).toEqual({ content_id: 'content-one', cefr: 'B2' })
})

it('fails closed for unavailable generation and shows an empty catalog honestly', async () => {
  api.catalog.mockResolvedValue({ items: [], total: 0, generation_available: false })
  app('/app/learn')
  expect(await screen.findByText(/No briefs in this topic yet/)).toBeVisible()
  expect(screen.getByText(/Lesson preparation is temporarily unavailable/)).toBeVisible()
  expect(api.prepare).not.toHaveBeenCalled()
})

it('opens a finished job and saves deterministic feedback only after confirmation', async () => {
  api.job.mockResolvedValue({ ...job, status: 'succeeded', lesson_id: lesson.id })
  app('/app/learn/jobs/job-one')
  await screen.findByRole('heading', { name: lesson.title })
  expect(screen.queryByText('Accepted answer')).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('radio', { name: 'A garden' }))
  await userEvent.click(screen.getByRole('button', { name: 'Save answers and check' }))
  const feedback = await screen.findByRole('status', { name: 'Latest feedback' })
  expect(within(feedback).getByText('1 of 5 exercises correct')).toBeVisible()
  expect(within(feedback).getAllByText('Accepted: Accepted answer')).toHaveLength(5)
  expect(api.submit.mock.calls[0]?.[1]?.[0]).toEqual(['A garden'])
  expect(saved).toHaveLength(1)
})

it('retains unsaved answers and idempotency key after a failed submission', async () => {
  api.submit.mockRejectedValueOnce(new Error('network unavailable'))
  app('/app/lessons/lesson-one')
  await screen.findByRole('heading', { name: lesson.title })
  const answer = screen.getAllByLabelText('Your answer')[0]!
  await userEvent.type(answer, 'plant')
  await userEvent.click(screen.getByRole('button', { name: 'Save answers and check' }))
  await screen.findByRole('heading', { name: 'We couldn’t complete that request' })
  expect(answer).toHaveValue('plant')
  expect(screen.queryByRole('status', { name: 'Latest feedback' })).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Save answers and check' }))
  await screen.findByRole('status', { name: 'Latest feedback' })
  expect(api.submit.mock.calls[0]?.[2]).toBe(api.submit.mock.calls[1]?.[2])
})

it('warns before discarding answers and clears forms on account switching', async () => {
  const view = app('/app/lessons/lesson-one')
  await screen.findByRole('heading', { name: lesson.title })
  await userEvent.type(screen.getAllByLabelText('Your answer')[0]!, 'Private draft')
  await userEvent.click(screen.getByRole('link', { name: 'All lessons' }))
  expect(window.confirm).toHaveBeenCalled()
  expect(screen.getByDisplayValue('Private draft')).toBeVisible()
  api.lesson.mockRejectedValue(new PrivateApiError(404))
  view.switchAccount({ ...auth, subject: 'two' })
  await waitFor(() => expect(screen.queryByDisplayValue('Private draft')).not.toBeInTheDocument())
  expect(await screen.findByRole('heading', { name: 'This record is no longer available' })).toBeVisible()
})

it('requires sign-in after expired credentials without a redirect loop', async () => {
  api.lesson.mockRejectedValue(new PrivateApiError(401))
  app('/app/lessons/lesson-one')
  expect(await screen.findByRole('heading', { name: /Sign in again/ })).toBeVisible()
  expect(auth.login).not.toHaveBeenCalled()
  expect(api.submit).not.toHaveBeenCalled()
})

it('shows failed preparation without presenting an unfinished lesson', async () => {
  api.job.mockResolvedValue({ ...job, status: 'failed', error_code: 'validation_failed' })
  app('/app/learn/jobs/job-one')
  expect(await screen.findByRole('heading', { name: 'This lesson needs another try.' })).toBeVisible()
  expect(screen.getByRole('button', { name: 'Try a new preparation' })).toBeEnabled()
  expect(screen.queryByText('Put it into practice')).not.toBeInTheDocument()
})
