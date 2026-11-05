import createClient from 'openapi-fetch'
import type { paths } from './schema'

export type { paths, components, operations } from './schema'

export function createLingoraClient(baseUrl: string) {
  return createClient<paths>({ baseUrl })
}
