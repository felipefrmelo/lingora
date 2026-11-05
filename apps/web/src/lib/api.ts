import { createLingoraClient } from '@lingora/api-client'

const client = createLingoraClient(import.meta.env.VITE_API_BASE_URL || window.location.origin)

export async function getHealth() {
  const { data, error, response } = await client.GET('/api/v1/health')
  if (error || !response.ok || !data) {
    throw new Error('Lingora is temporarily unavailable.')
  }
  return data
}
