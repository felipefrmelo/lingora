import { useMutation, useQuery } from '@tanstack/react-query'
import { Link, Navigate, useNavigate } from '@tanstack/react-router'
import { useRef } from 'react'
import { useAuth } from '../../auth/context'
import { privateKey } from '../../auth/private-api'
import { Button } from '../../components/ui/button'
import { RequestFailure } from '../onboarding/shared'
import { useLessonApi } from './api'

export function JobPage({ jobId }: { jobId: string }) {
  const auth = useAuth()
  const api = useLessonApi()
  const navigate = useNavigate()
  const key = useRef(crypto.randomUUID())
  const job = useQuery({ queryKey: [...privateKey(auth.subject, 'lesson-job'), jobId], queryFn: ({ signal }) => api.job(jobId, signal), retry: false, refetchInterval: query => ['queued', 'running'].includes(query.state.data?.status || '') ? 2000 : false })
  const retry = useMutation({ mutationFn: () => api.prepare({ content_id: job.data!.content_id, cefr: job.data!.cefr }, key.current), onSuccess: async data => { key.current = crypto.randomUUID(); await navigate({ to: '/app/learn/jobs/$jobId', params: { jobId: data.id } }) } })
  if (job.isPending) return <p role="status">Finding your lesson…</p>
  if (job.isError) return <RequestFailure error={job.error} retry={() => void job.refetch()} />
  if (job.data.status === 'succeeded' && job.data.lesson_id) return <Navigate to="/app/lessons/$lessonId" params={{ lessonId: job.data.lesson_id }} replace />
  const failed = job.data.status === 'failed'
  return <section className="form-section"><Link to="/app/learn" className="text-sm underline">All lessons</Link><h1 className="mt-6 font-display text-4xl">{failed ? 'This lesson needs another try.' : 'Your lesson is taking shape.'}</h1><p className="mt-5" role="status">{failed ? 'We couldn’t prepare a validated lesson. No unfinished exercises have been published.' : job.data.status === 'queued' ? 'Queued for preparation. You can leave and return from your lesson list.' : 'Writing and checking your lesson. This may take a couple of minutes.'}</p><p className="mt-4 text-sm text-muted-foreground">{job.data.cefr} · {job.data.level_reason}</p>{failed && <Button disabled={retry.isPending} className="mt-6" onClick={() => retry.mutate()}>{retry.isPending ? 'Requesting…' : 'Try a new preparation'}</Button>}{retry.isError && <RequestFailure error={retry.error} />}<Button asChild variant="outline" className="mt-6"><Link to="/app/learn">Explore other briefs</Link></Button></section>
}
