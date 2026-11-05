import { afterEach, describe, expect, it, vi } from 'vitest'
import { cancelPrivateRequests, protectedRequest } from './private-api'

afterEach(() => cancelPrivateRequests())

describe('private request lifecycle', () => {
  it('aborts pending token acquisition before a signed-out request can be sent', async () => {
    let resolve!: (token: string) => void
    const token = new Promise<string>(done => { resolve = done })
    const execute = vi.fn()
    const pending = protectedRequest(() => token, 'one')(execute)
    cancelPrivateRequests()
    resolve('expired-session-token')
    await expect(pending).rejects.toMatchObject({ name: 'AbortError' })
    expect(execute).not.toHaveBeenCalled()
  })

  it('cancels only the previous account’s requests when identities switch', async () => {
    const signals: AbortSignal[] = []
    const execute = async (_headers: Record<string, string>, signal: AbortSignal) => {
      signals.push(signal)
      await new Promise<void>((_resolve, reject) => signal.addEventListener('abort', () => reject(signal.reason)))
      return { response: new Response(), data: 'value' }
    }
    const first = protectedRequest(async () => 'token', 'one')(execute)
    const second = protectedRequest(async () => 'token', 'two')(execute)
    await vi.waitFor(() => expect(signals).toHaveLength(2))
    cancelPrivateRequests('one')
    await expect(first).rejects.toMatchObject({ name: 'AbortError' })
    expect(signals[1]?.aborted).toBe(false)
    cancelPrivateRequests('two')
    await expect(second).rejects.toMatchObject({ name: 'AbortError' })
  })
})
