import type { components } from '@lingora/api-client'

type Problem = components['schemas']['ProblemDetails']
const requests = new Map<AbortController, string>()

export const privateKey = (subject: string | undefined, resource: string) => ['private', subject, resource] as const

export function cancelPrivateRequests(subject?: string) {
  for (const [controller, owner] of requests) {
    if (subject === undefined || owner === subject) controller.abort()
  }
}

export class PrivateApiError extends Error {
  constructor(readonly status: number, readonly problem?: Problem) {
    super(problem?.detail || 'The request could not be completed.')
  }
}

type Result<T> = { data?: T; error?: unknown; response: Response }

export function protectedRequest(getToken: (force?: boolean) => Promise<string>, subject: string) {
  return async function request<T>(execute: (headers: Record<string, string>, signal: AbortSignal) => Promise<Result<T>>, parentSignal?: AbortSignal): Promise<T> {
    const controller = new AbortController()
    const signal = parentSignal ? AbortSignal.any([controller.signal, parentSignal]) : controller.signal
    requests.set(controller, subject)
    try {
      const run = async (force = false) => {
        signal.throwIfAborted()
        const token = await getToken(force)
        signal.throwIfAborted()
        return execute({ Authorization: `Bearer ${token}` }, signal)
      }
      let result = await run()
      if (result.response.status === 401) result = await run(true)
      signal.throwIfAborted()
      if (!result.response.ok) {
        const body = result.error
        const problem = typeof body === 'object' && body !== null && 'detail' in body && typeof body.detail === 'string' ? body as Problem : undefined
        throw new PrivateApiError(result.response.status, problem)
      }
      return result.data as T
    } finally {
      requests.delete(controller)
    }
  }
}
