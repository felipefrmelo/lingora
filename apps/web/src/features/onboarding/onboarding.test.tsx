import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { createMemoryHistory, createRouter, RouterProvider } from '@tanstack/react-router'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthState } from '../../auth/context'
import { PrivateApiError } from '../../auth/private-api'
import { routeTree } from '../../routes'
import type { Assessment, AssessmentInput, Profile, ProfileWrite } from './api'

const api = vi.hoisted(() => ({ profile: vi.fn(), saveProfile: vi.fn(), assessments: vi.fn(), createAssessment: vi.fn(), updateAssessment: vi.fn(), deleteAssessment: vi.fn() }))
vi.mock('./api', () => ({ createLearningApi: () => api }))
vi.mock('../account/api', async original => ({ ...await original<typeof import('../account/api')>(), createAccountApi: () => ({ bootstrap: async () => ({ id: 'one' }), current: async () => ({ id: 'one' }) }) }))

let stored: Profile
let records: Assessment[]
const initialProfile = (): Profile => ({ version: 0, onboarding_status: 'not_started', correction_mode: 'balanced', goals: [], interests: [] })
const auth: AuthState = { configured: true, isLoading: false, isAuthenticated: true, subject: 'auth0|one', name: 'Student One', email: 'one@example.test', error: null, login: vi.fn(), logout: vi.fn(), getAccessToken: vi.fn() }

function app(path = '/app') {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  const router = createRouter({ routeTree, history: createMemoryHistory({ initialEntries: [path] }) })
  function tree(identity: AuthState) { return <QueryClientProvider client={client}><AuthContext.Provider value={identity}><RouterProvider router={router} /></AuthContext.Provider></QueryClientProvider> }
  const view = render(tree(auth))
  return { router, client, switchAccount: (identity: AuthState) => view.rerender(tree(identity)) }
}

beforeEach(() => {
  vi.resetAllMocks()
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  stored = initialProfile(); records = []
  api.profile.mockImplementation(async () => structuredClone(stored))
  api.saveProfile.mockImplementation(async ({ expected_version, intent, ...fields }: ProfileWrite) => {
    stored = { ...stored, ...fields, version: expected_version + 1, onboarding_status: stored.onboarding_status === 'completed' ? 'completed' : intent === 'finish' ? 'completed' : intent === 'skip' ? 'skipped' : 'in_progress' }
    return structuredClone(stored)
  })
  api.assessments.mockImplementation(async () => ({ items: structuredClone(records), total: records.length }))
  api.createAssessment.mockImplementation(async (body: AssessmentInput) => {
    const result: Assessment = { ...body, id: 'assessment-one', version: 1, created_at: '2026-01-01T12:00:00Z', updated_at: '2026-01-01T12:00:00Z', self_reported: true }
    records.push(result); return result
  })
  api.updateAssessment.mockImplementation(async (id: string, { expected_version, ...body }: AssessmentInput & { expected_version: number }) => {
    records = records.map(r => r.id === id ? { ...r, ...body, version: expected_version + 1 } : r)
    return records[0]
  })
  api.deleteAssessment.mockImplementation(async (id: string) => { records = records.filter(r => r.id !== id) })
})

describe('student onboarding', () => {
  it('routes first visits into setup and permits empty completion', async () => {
    app()
    expect(await screen.findByRole('heading', { name: 'About you' })).toBeVisible()
    await userEvent.click(screen.getByRole('button', { name: 'Save and continue' }))
    expect(await screen.findByRole('heading', { name: 'Your English' })).toBeVisible()
    expect(screen.getByLabelText('Your starting English level')).toHaveValue('unknown')
    await userEvent.click(screen.getByRole('button', { name: 'Save and continue' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Finish setup' }))
    expect(await screen.findByRole('heading', { name: 'Welcome, Student One.' })).toBeVisible()
    expect(stored.onboarding_status).toBe('completed')
    expect(stored.selected_cefr).toBeNull()
    expect(screen.getByText(/first lesson is still taking shape/)).toBeVisible()
  })

  it('saves suggested and pending custom entries, skips unsaved choices, and resumes saved progress', async () => {
    app()
    await userEvent.type(await screen.findByLabelText('What should we call you?'), 'Ana')
    await userEvent.type(screen.getByLabelText('Native language'), 'Portuguese')
    await userEvent.click(within(screen.getByRole('group', { name: 'What would you like English to help you do?' })).getByRole('button', { name: 'Travel' }))
    await userEvent.type(screen.getByLabelText('Add your own goal'), 'Interview practice')
    await userEvent.type(screen.getByLabelText('Add your own topic'), 'Gardening')
    await userEvent.click(screen.getByRole('button', { name: 'Save and continue' }))
    expect(await screen.findByRole('heading', { name: 'Your English' })).toBeVisible()
    expect(stored.goals).toContain('Interview practice')
    expect(stored.interests).toContain('Gardening')
    await userEvent.selectOptions(screen.getByLabelText('Your starting English level'), 'B1')
    await userEvent.click(screen.getByRole('button', { name: 'Skip for now' }))
    expect(await screen.findByRole('heading', { name: 'Welcome, Ana.' })).toBeVisible()
    expect(stored.selected_cefr).toBeNull()
    await userEvent.click(screen.getByRole('link', { name: 'Resume setup' }))
    expect(await screen.findByLabelText('What should we call you?')).toHaveValue('Ana')
    expect(screen.getByLabelText('Native language')).toHaveValue('Portuguese')
  })

  it('preserves conflicting input until the user explicitly reloads the saved record', async () => {
    stored = { ...initialProfile(), version: 1, onboarding_status: 'completed', preferred_name: 'Ana' }
    api.saveProfile.mockRejectedValueOnce(new PrivateApiError(409))
    app('/app/profile')
    const input = await screen.findByLabelText('What should we call you?')
    await userEvent.clear(input); await userEvent.type(input, 'My unsaved name')
    await userEvent.click(screen.getByRole('button', { name: 'Save profile' }))
    expect(await screen.findByRole('heading', { name: 'This record changed' })).toBeVisible()
    expect(input).toHaveValue('My unsaved name')
    stored = { ...stored, version: 2, preferred_name: 'Remote name' }
    await userEvent.click(screen.getByRole('button', { name: 'Reload saved record' }))
    await waitFor(() => expect(input).toHaveValue('Remote name'))
  })

  it('keeps the draft when a save fails and offers a working retry', async () => {
    api.saveProfile.mockRejectedValueOnce(new Error('network unavailable'))
    app('/app/onboarding')
    await userEvent.type(await screen.findByLabelText('What should we call you?'), 'Keep me')
    await userEvent.click(screen.getByRole('button', { name: 'Save and continue' }))
    await screen.findByRole('heading', { name: 'We couldn’t complete that request' })
    expect(screen.getByLabelText('What should we call you?')).toHaveValue('Keep me')
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(await screen.findByRole('heading', { name: 'Your English' })).toBeVisible()
  })

  it('warns before leaving a dirty profile and allows cancelling the navigation', async () => {
    stored = { ...initialProfile(), onboarding_status: 'completed' }
    app('/app/profile')
    await userEvent.type(await screen.findByLabelText('What should we call you?'), 'Unsaved')
    vi.mocked(window.confirm).mockReturnValue(false)
    await userEvent.click(screen.getByRole('link', { name: /^Cancel$/ }))
    await waitFor(() => expect(window.confirm).toHaveBeenCalled())
    expect(screen.getByLabelText('What should we call you?')).toHaveValue('Unsaved')
    vi.mocked(window.confirm).mockReturnValue(true)
    await userEvent.click(screen.getByRole('link', { name: /^Cancel$/ }))
    expect(await screen.findByRole('heading', { name: 'Welcome, Student One.' })).toBeVisible()
  })

  it('does not discard a dirty assessment when moving to another wizard step', async () => {
    app('/app/onboarding')
    await userEvent.click(await screen.findByRole('button', { name: 'Save and continue' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Add assessment' }))
    await userEvent.type(screen.getByLabelText('Test name'), 'Draft test')
    vi.mocked(window.confirm).mockReturnValue(false)
    await userEvent.click(screen.getByRole('button', { name: 'Save and continue' }))
    expect(screen.getByLabelText('Test name')).toHaveValue('Draft test')
    expect(screen.getByRole('heading', { name: 'Your English' })).toBeVisible()
    expect(api.createAssessment).not.toHaveBeenCalled()
  })

  it('clears unsaved form state when the authenticated identity changes', async () => {
    const view = app('/app/profile')
    await userEvent.type(await screen.findByLabelText('What should we call you?'), 'First account secret draft')
    stored = { ...initialProfile(), preferred_name: 'Second account' }
    view.switchAccount({ ...auth, subject: 'auth0|two', name: 'Second' })
    await waitFor(() => expect(screen.getByLabelText('What should we call you?')).toHaveValue('Second account'))
    expect(screen.queryByDisplayValue('First account secret draft')).not.toBeInTheDocument()
  })

  it('warns before discarding an invalid current step and permits returning to it', async () => {
    app('/app/onboarding')
    await userEvent.click(await screen.findByRole('button', { name: 'Save and continue' }))
    await userEvent.click(await screen.findByRole('button', { name: 'Save and continue' }))
    await userEvent.type(await screen.findByLabelText('Minutes per session'), '999')
    vi.mocked(window.confirm).mockReturnValue(false)
    await userEvent.click(screen.getByRole('button', { name: 'Back' }))
    expect(screen.getByLabelText('Minutes per session')).toHaveValue(999)
    vi.mocked(window.confirm).mockReturnValue(true)
    await userEvent.click(screen.getByRole('button', { name: 'Back' }))
    expect(await screen.findByRole('heading', { name: 'Your English' })).toBeVisible()
    await userEvent.click(screen.getByRole('button', { name: 'Save and continue' }))
    expect(await screen.findByLabelText('Minutes per session')).toHaveValue(null)
  })
})

describe('self-reported assessments', () => {
  async function open() {
    stored = { ...initialProfile(), onboarding_status: 'completed', selected_cefr: 'A2' }
    app()
    await userEvent.click(await screen.findByRole('button', { name: 'Add assessment' }))
  }
  async function fill() {
    await userEvent.selectOptions(screen.getByLabelText('Test provider'), 'ef_set')
    await userEvent.type(screen.getByLabelText('Test name'), 'EF SET')
    await userEvent.type(screen.getByLabelText('Test variant (optional)'), '2 skills')
    await userEvent.type(screen.getByLabelText('Assessment date'), '2026-01-01')
    await userEvent.type(screen.getByLabelText('Original overall score (optional)'), '050.0')
    await userEvent.type(screen.getByLabelText('Overall scale (optional)'), '0–100')
    await userEvent.selectOptions(screen.getByLabelText('CEFR reported by this test (optional)'), 'B1')
  }
  it('creates, edits and deletes original scores without changing selected CEFR', async () => {
    await open(); await fill()
    await userEvent.click(screen.getByRole('button', { name: 'Add component score' }))
    await userEvent.type(screen.getByLabelText('Component 1', { exact: true }), 'Reading')
    await userEvent.type(screen.getByLabelText('Component 1 score'), '0052')
    await userEvent.click(screen.getByRole('button', { name: 'Save assessment' }))
    expect(await screen.findByText('EF SET · 2 skills')).toBeVisible()
    expect(screen.getByText('Overall: 050.0 (0–100)')).toBeVisible()
    expect(screen.getByText('Reading: 0052')).toBeVisible()
    expect(stored.selected_cefr).toBe('A2')
    await userEvent.click(screen.getByRole('button', { name: 'Edit EF SET' }))
    const score = screen.getByLabelText('Original overall score (optional)')
    await userEvent.clear(score); await userEvent.type(score, '055.5')
    await userEvent.click(screen.getByRole('button', { name: 'Save assessment' }))
    expect(await screen.findByText('Overall: 055.5 (0–100)')).toBeVisible()
    await userEvent.click(screen.getByRole('button', { name: 'Delete EF SET' }))
    expect(await screen.findByText(/No assessment results recorded yet/)).toBeVisible()
    expect(stored.selected_cefr).toBe('A2')
    expect(api.saveProfile).not.toHaveBeenCalled()
  })

  it('validates missing results and retains an idempotency key on network retry', async () => {
    await open()
    await userEvent.click(screen.getByRole('button', { name: 'Save assessment' }))
    expect(await screen.findByText('Enter the test name.')).toBeVisible()
    expect(api.createAssessment).not.toHaveBeenCalled()
    await fill()
    api.createAssessment.mockRejectedValueOnce(new Error('lost response'))
    await userEvent.click(screen.getByRole('button', { name: 'Save assessment' }))
    const error = await screen.findByRole('heading', { name: 'We couldn’t complete that request' })
    await userEvent.click(within(error.closest('section')!).getByRole('button', { name: 'Try again' }))
    await screen.findByText('EF SET · 2 skills')
    expect(api.createAssessment.mock.calls[0]?.[1]).toBe(api.createAssessment.mock.calls[1]?.[1])
    expect(api.createAssessment.mock.calls[1]?.[0]?.overall_score?.value).toBe('050.0')
  })
})
