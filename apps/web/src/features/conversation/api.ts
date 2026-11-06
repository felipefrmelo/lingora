import { useMemo } from 'react'
import { createLingoraClient } from '@lingora/api-client'
import { useAuth } from '../../auth/context'
import { protectedRequest } from '../../auth/private-api'

export function useConversationApi() {
  const auth = useAuth()
  return useMemo(() => {
    const client = createLingoraClient(import.meta.env.VITE_API_BASE_URL || window.location.origin)
    const request = protectedRequest(auth.getAccessToken, auth.subject || '')
    return {
      list: (parent?: AbortSignal) => request((headers, signal) => client.GET('/api/v1/me/conversation-sessions', { headers, signal }), parent),
      get: (id: string, parent?: AbortSignal) => request((headers, signal) => client.GET('/api/v1/me/conversation-sessions/{identifier}', { headers, signal, params: { path: { identifier: id } } }), parent),
      prepare: (id: string, saveExamples: boolean, key: string) => request((headers, signal) => client.POST('/api/v1/me/conversation-sessions', { headers, signal, body: { lesson_id: id, save_examples: saveExamples }, params: { header: { 'Idempotency-Key': key } } })),
      abandon: (id: string, version: number, key: string) => request((headers, signal) => client.POST('/api/v1/me/conversation-sessions/{identifier}/abandon', { headers, signal, body: { expected_version: version }, params: { path: { identifier: id }, header: { 'Idempotency-Key': key } } })),
      access: (parent?: AbortSignal) => request((headers, signal) => client.GET('/api/v1/me/mcp-access', { headers, signal }), parent),
      setAccess: (enabled: boolean) => request((headers, signal) => client.PUT('/api/v1/me/mcp-access', { headers, signal, body: { enabled } })),
    }
  }, [auth.getAccessToken, auth.subject])
}
