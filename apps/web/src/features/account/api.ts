import { createLingoraClient } from '@lingora/api-client'
import { protectedRequest } from '../../auth/private-api'

export { PrivateApiError as AccountApiError } from '../../auth/private-api'

export function createAccountApi(getToken: (force?: boolean) => Promise<string>, subject = '') {
  const client = createLingoraClient(import.meta.env.VITE_API_BASE_URL || window.location.origin)
  const request = protectedRequest(getToken, subject)
  return {
    bootstrap: (parent?: AbortSignal) => request((headers, signal) => client.POST('/api/v1/me/bootstrap', { body: {}, headers, signal }), parent),
    current: (parent?: AbortSignal) => request((headers, signal) => client.GET('/api/v1/me', { headers, signal }), parent),
  }
}
