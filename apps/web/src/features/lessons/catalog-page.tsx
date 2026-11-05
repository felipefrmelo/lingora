import { useMutation, useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from '@tanstack/react-router'
import { useRef, useState } from 'react'
import { useAuth } from '../../auth/context'
import { privateKey } from '../../auth/private-api'
import { Button } from '../../components/ui/button'
import { RequestFailure } from '../onboarding/shared'
import { useLessonApi, type Content, type Prepare } from './api'

export function SourceCredit({ source }: { source: Content }) {
  return <p className="mt-4 text-xs leading-relaxed text-muted-foreground"><a href={source.url} target="_blank" rel="noreferrer" className="underline">{source.source} · Original brief</a>{' · '}{new Date(source.published_at).toLocaleDateString()}<br />{source.attribution}{' '}<a className="underline" href={source.license_url} target="_blank" rel="noreferrer">{source.license_name}</a></p>
}

export function CatalogPage() {
  const auth = useAuth()
  const api = useLessonApi()
  const navigate = useNavigate()
  const [topic, setTopic] = useState('')
  const [offset, setOffset] = useState(0)
  const [historyOffset, setHistoryOffset] = useState(0)
  const [cefr, setCefr] = useState('')
  const key = useRef<{ payload: string; key: string } | null>(null)
  const catalog = useQuery({ queryKey: [...privateKey(auth.subject, 'catalog'), topic, offset], queryFn: ({ signal }) => api.catalog(topic || undefined, offset, signal), retry: false })
  const history = useQuery({ queryKey: [...privateKey(auth.subject, 'lessons'), historyOffset], queryFn: ({ signal }) => api.jobs(historyOffset, signal), retry: false, refetchInterval: query => query.state.data?.items.some(x => x.status === 'queued' || x.status === 'running') ? 4000 : false })
  const prepare = useMutation({ mutationFn: async (contentId: string) => {
    const body: Prepare = { content_id: contentId, cefr: cefr ? cefr as Prepare['cefr'] : null }
    const payload = JSON.stringify(body)
    if (key.current?.payload !== payload) key.current = { payload, key: crypto.randomUUID() }
    return api.prepare(body, key.current.key)
  }, onSuccess: async job => { key.current = null; await navigate({ to: '/app/learn/jobs/$jobId', params: { jobId: job.id } }) } })
  return <div className="space-y-10">
    <header><Link to="/app" className="text-sm underline">Your profile</Link><p className="mt-6 text-xs font-semibold uppercase tracking-widest text-primary">Read. Notice. Try.</p><h1 className="mt-3 font-display text-4xl sm:text-5xl">A little English, from your world.</h1><p className="mt-4 leading-relaxed text-muted-foreground">Choose an English news brief. We’ll turn it into a reading lesson with vocabulary and five exercises.</p></header>
    <section aria-labelledby="catalog-title" className="space-y-6">
      <h2 id="catalog-title" className="font-display text-3xl">Find your next lesson</h2>
      <div className="grid gap-4 sm:grid-cols-2"><label className="field-label">Topic<select className="field-input mt-2" value={topic} onChange={e => { setTopic(e.target.value); setOffset(0) }}><option value="">All topics</option><option value="space">Space</option><option value="environment">Environment</option></select></label><label className="field-label">Lesson level<select className="field-input mt-2" value={cefr} onChange={e => setCefr(e.target.value)}><option value="">Use my profile level (A2 if unknown)</option>{['A1', 'A2', 'B1', 'B2', 'C1', 'C2'].map(level => <option key={level}>{level}</option>)}</select></label></div>
      <p className="text-sm text-muted-foreground">Briefs are in their original English and have no assessed difficulty. Your chosen level applies to the generated lesson. External test scores do not set it.</p><p className="text-xs text-muted-foreground">Preparation sends the brief, your goals, interests and lesson level to OpenAI. Your name, email and test scores are excluded.</p>
      {catalog.isPending ? <p role="status">Finding news briefs…</p> : catalog.isError ? <RequestFailure error={catalog.error} retry={() => void catalog.refetch()} /> : <>
        {!catalog.data.generation_available && <p role="status" className="rounded-xl bg-muted p-4">Lesson preparation is temporarily unavailable. You can still explore the sources.</p>}
        {!catalog.data.items.length && <p>No briefs in this topic yet. Try another topic or check back after the next catalog update.</p>}
        {prepare.isError && <RequestFailure error={prepare.error} />}
        <div className="grid gap-5 sm:grid-cols-2">{catalog.data.items.map((content, index) => <article key={content.id} className="flex flex-col rounded-3xl border border-border bg-card p-6">
          <p className="text-xs font-semibold uppercase tracking-wider text-primary">{index === 0 && offset === 0 ? 'A place to start · ' : ''}{content.topics.join(' · ')}</p><h3 className="mt-3 font-display text-2xl">{content.title}</h3><p className="mt-3 text-sm leading-relaxed text-muted-foreground">{content.summary}</p><p className="mt-4 text-sm">{content.recommendation_reason}</p><SourceCredit source={content} /><Button disabled={prepare.isPending || !catalog.data.generation_available} className="mt-5 self-start" onClick={() => prepare.mutate(content.id)}>{prepare.isPending && prepare.variables === content.id ? 'Preparing…' : 'Make this my lesson'}</Button>
        </article>)}</div><div className="flex gap-3"><Button variant="outline" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 12))}>Previous briefs</Button><Button variant="outline" disabled={offset + 12 >= catalog.data.total} onClick={() => setOffset(offset + 12)}>More briefs</Button></div>
      </>}
    </section>
    <section aria-labelledby="history-title"><h2 id="history-title" className="font-display text-3xl">Your lessons</h2><p className="mt-3 text-sm text-muted-foreground">Preparation continues after you leave this page. Finished lessons and your saved answers stay here.</p>{history.isPending ? <p role="status" className="mt-4">Loading your lessons…</p> : history.isError ? <RequestFailure error={history.error} retry={() => void history.refetch()} /> : <><ul className="mt-5 space-y-3">{history.data.items.map(job => <li key={job.id} className="rounded-xl border border-border p-4"><Link to="/app/learn/jobs/$jobId" params={{ jobId: job.id }} className="underline">{job.cefr} lesson · {new Date(job.created_at).toLocaleString()}</Link><p className="mt-2 text-sm capitalize">{job.status === 'succeeded' ? 'Ready to study' : job.status === 'failed' ? 'Preparation could not finish' : job.status}</p></li>)}</ul>{!history.data.items.length && <p className="mt-4 text-muted-foreground">Your first lesson starts with a brief above.</p>}<div className="mt-4 flex gap-3"><Button variant="outline" disabled={!historyOffset} onClick={() => setHistoryOffset(Math.max(0, historyOffset - 12))}>Previous lessons</Button><Button variant="outline" disabled={historyOffset + 12 >= history.data.total} onClick={() => setHistoryOffset(historyOffset + 12)}>More lessons</Button></div></>}
    </section>
  </div>
}
