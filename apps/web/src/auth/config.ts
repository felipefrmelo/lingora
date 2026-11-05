import { z } from 'zod'

const authConfig = z.object({
  domain: z.string().regex(/^[a-z0-9.-]+$/i),
  clientId: z.string().min(1),
  audience: z.url().startsWith('https://'),
  redirectUri: z.url(),
})

export type AuthConfig = z.infer<typeof authConfig>

export function readAuthConfig(env: Record<string, unknown>, origin: string): AuthConfig | null {
  const parsed = authConfig.safeParse({
    domain: env.VITE_AUTH0_DOMAIN,
    clientId: env.VITE_AUTH0_CLIENT_ID,
    audience: env.VITE_AUTH0_AUDIENCE,
    redirectUri: env.VITE_AUTH0_REDIRECT_URI || `${origin}/auth/callback`,
  })
  if (!parsed.success || new URL(parsed.data.redirectUri).origin !== origin) return null
  if (new URL(parsed.data.redirectUri).pathname !== '/auth/callback') return null
  return parsed.data
}
