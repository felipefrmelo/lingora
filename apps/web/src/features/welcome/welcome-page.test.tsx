import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'
import { getHealth } from '../../lib/api'
import { WelcomePage } from './welcome-page'

vi.mock('../../lib/api', () => ({ getHealth: vi.fn() }))
const mockedHealth = vi.mocked(getHealth)

function renderWelcome() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false, gcTime: 0 } } })
  return render(<QueryClientProvider client={client}><WelcomePage /></QueryClientProvider>)
}

describe('WelcomePage', () => {
  it('shows loading while checking the service', () => {
    mockedHealth.mockReturnValue(new Promise(() => {}))
    renderWelcome()
    expect(screen.getByRole('status')).toHaveTextContent('Checking connection')
    expect(screen.getByRole('button', { name: 'Check connection' })).toBeDisabled()
  })

  it('shows a successful connection without invented student progress', async () => {
    mockedHealth.mockResolvedValue({ status: 'ok' })
    renderWelcome()
    expect(await screen.findByText('Connection ready')).toBeVisible()
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('Your world.In English.')
  })

  it('recovers after a failed request when the student retries', async () => {
    mockedHealth.mockRejectedValueOnce(new Error('Network unavailable')).mockResolvedValue({ status: 'ok' })
    renderWelcome()
    const retry = await screen.findByRole('button', { name: 'Try again' })
    await userEvent.click(retry)
    await waitFor(() => expect(screen.getByRole('status')).toHaveTextContent('Connection ready'))
    expect(mockedHealth).toHaveBeenCalledTimes(2)
  })
})
