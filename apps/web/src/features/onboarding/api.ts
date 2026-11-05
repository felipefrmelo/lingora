import { createLingoraClient, type components } from '@lingora/api-client'
import { protectedRequest } from '../../auth/private-api'

export type Profile = components['schemas']['ProfileResponse']
export type ProfileWrite = components['schemas']['ProfileWrite']
export type Assessment = components['schemas']['AssessmentResponse']
export type AssessmentInput = components['schemas']['AssessmentFields']

export function createLearningApi(getToken: (force?: boolean) => Promise<string>, subject: string) {
  const client = createLingoraClient(import.meta.env.VITE_API_BASE_URL || window.location.origin)
  const request = protectedRequest(getToken, subject)
  return {
    profile: (parent?: AbortSignal) => request((headers, signal) => client.GET('/api/v1/me/profile', { headers, signal }), parent),
    saveProfile: (body: ProfileWrite) => request((headers, signal) => client.PUT('/api/v1/me/profile', { headers, signal, body })),
    assessments: (offset = 0, parent?: AbortSignal) => request((headers, signal) => client.GET('/api/v1/me/assessments', { headers, signal, params: { query: { limit: 20, offset } } }), parent),
    createAssessment: (body: AssessmentInput, key: string) => request((headers, signal) => client.POST('/api/v1/me/assessments', { headers, signal, body, params: { header: { 'Idempotency-Key': key } } })),
    updateAssessment: (id: string, body: components['schemas']['AssessmentWrite']) => request((headers, signal) => client.PUT('/api/v1/me/assessments/{assessment_id}', { headers, signal, body, params: { path: { assessment_id: id } } })),
    deleteAssessment: (id: string, version: number) => request((headers, signal) => client.DELETE('/api/v1/me/assessments/{assessment_id}', { headers, signal, params: { path: { assessment_id: id }, query: { expected_version: version } } })),
  }
}
