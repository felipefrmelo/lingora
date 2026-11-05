import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AccountApiError, createAccountApi } from './api'

const fetchMock = vi.fn<typeof fetch>()
const account = { id: '88b70da0-400a-4d49-b4fe-ddf33b9b9845', created_at: '2026-11-04T12:00:00Z' }
const jsonResponse = (status: number) => new Response(JSON.stringify(account), { status, headers: { 'Content-Type': 'application/json' } })

beforeEach(() => { vi.resetAllMocks(); vi.stubGlobal('fetch', fetchMock) })
afterEach(() => { vi.unstubAllGlobals() })

describe('authenticated account API', () => {
  it('renews once on 401 and sends only access tokens in authorization headers', async () => {
    fetchMock.mockResolvedValueOnce(jsonResponse(401)).mockResolvedValueOnce(jsonResponse(200))
    const getToken = vi.fn().mockResolvedValueOnce('old-access-token').mockResolvedValueOnce('new-access-token')
    expect(await createAccountApi(getToken).current()).toEqual(account)
    expect(getToken.mock.calls).toEqual([[false], [true]])
    const first = fetchMock.mock.calls[0]?.[0] as Request
    const second = fetchMock.mock.calls[1]?.[0] as Request
    expect(first.headers.get('Authorization')).toBe('Bearer old-access-token')
    expect(second.headers.get('Authorization')).toBe('Bearer new-access-token')
    expect(first.url).not.toContain('token')
  })

  it.each([403, 503])('does not retry or renew tokens on %s', async (status) => {
    fetchMock.mockResolvedValue(jsonResponse(status))
    const getToken = vi.fn().mockResolvedValue('access-token')
    await expect(createAccountApi(getToken).current()).rejects.toEqual(new AccountApiError(status))
    expect(fetchMock).toHaveBeenCalledTimes(1)
    expect(getToken).toHaveBeenCalledExactlyOnceWith(false)
  })

  it('stops after one unsuccessful renewal', async () => {
    fetchMock.mockImplementation(async () => jsonResponse(401))
    const getToken = vi.fn().mockResolvedValue('expired-access-token')
    await expect(createAccountApi(getToken).bootstrap()).rejects.toEqual(new AccountApiError(401))
    expect(fetchMock).toHaveBeenCalledTimes(2)
  })
})
