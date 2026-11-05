import { useMemo } from 'react'
import { createLingoraClient, type components } from '@lingora/api-client'
import { useAuth } from '../../auth/context'
import { protectedRequest } from '../../auth/private-api'

export type Lesson = components['schemas']['LessonView']
export type Attempt = components['schemas']['AttemptView']
export type Job = components['schemas']['JobView']
export type Content = components['schemas']['ContentView']
export type Prepare = components['schemas']['GenerateLesson']

export function createLessonApi(token: (force?: boolean) => Promise<string>, subject: string) {
  const client = createLingoraClient(import.meta.env.VITE_API_BASE_URL || window.location.origin)
  const request = protectedRequest(token, subject)
  return {
    catalog: (topic?: string, offset = 0, parent?: AbortSignal) => request((headers, signal) => client.GET('/api/v1/me/content', { headers, signal, params: { query: { topic, offset, limit: 12 } } }), parent),
    prepare: (body: Prepare, key: string) => request((headers, signal) => client.POST('/api/v1/me/lessons', { headers, signal, body, params: { header: { 'Idempotency-Key': key } } })),
    jobs: (offset = 0, parent?: AbortSignal) => request((headers, signal) => client.GET('/api/v1/me/lessons', { headers, signal, params: { query: { offset, limit: 12 } } }), parent),
    job: (id: string, parent?: AbortSignal) => request((headers, signal) => client.GET('/api/v1/me/lesson-jobs/{job_id}', { headers, signal, params: { path: { job_id: id } } }), parent),
    lesson: (id: string, parent?: AbortSignal) => request((headers, signal) => client.GET('/api/v1/me/lessons/{lesson_id}', { headers, signal, params: { path: { lesson_id: id } } }), parent),
    attempts: (id: string, offset = 0, parent?: AbortSignal) => request((headers, signal) => client.GET('/api/v1/me/lessons/{lesson_id}/attempts', { headers, signal, params: { path: { lesson_id: id }, query: { offset, limit: 12 } } }), parent),
    submit: (id: string, answers: string[][], key: string) => request((headers, signal) => client.POST('/api/v1/me/lessons/{lesson_id}/attempts', { headers, signal, body: { answers }, params: { path: { lesson_id: id }, header: { 'Idempotency-Key': key } } })),
  }
}

export function useLessonApi() {
  const auth = useAuth()
  return useMemo(() => createLessonApi(auth.getAccessToken, auth.subject || ''), [auth.getAccessToken, auth.subject])
}
