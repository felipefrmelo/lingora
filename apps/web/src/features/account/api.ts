import { createLingoraClient } from '@lingora/api-client'

export class AccountApiError extends Error {
  constructor(readonly status: number) { super('The account request could not be completed.') }
}

export function createAccountApi(getToken: (force?: boolean) => Promise<string>) {
  const client = createLingoraClient(import.meta.env.VITE_API_BASE_URL || window.location.origin)

  async function request(bootstrap: boolean, signal?: AbortSignal) {
    const execute = async (force = false) => {
      const headers = { Authorization: `Bearer ${await getToken(force)}` }
      return bootstrap
        ? client.POST('/api/v1/me/bootstrap', { body: {}, headers, signal })
        : client.GET('/api/v1/me', { headers, signal })
    }
    let result = await execute()
    if (result.response.status === 401) result = await execute(true)
    if (!result.response.ok || !result.data) throw new AccountApiError(result.response.status)
    return result.data
  }

  return {
    bootstrap: (signal?: AbortSignal) => request(true, signal),
    current: (signal?: AbortSignal) => request(false, signal),
  }
}
