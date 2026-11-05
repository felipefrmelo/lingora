import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from '@tanstack/react-router'
import { useRef, useState } from 'react'
import { useAuth } from '../../auth/context'
import { privateKey } from '../../auth/private-api'
import { Button } from '../../components/ui/button'
import { AccountBoundary } from '../account/account-page'
import { RequestFailure } from '../onboarding/shared'
import { useConversationApi } from './api'

export function PrepareConversation({ lessonId }: { lessonId: string }) {
  const api = useConversationApi()
  const navigate = useNavigate()
  const [examples, setExamples] = useState(true)
  const key = useRef<{ examples: boolean; id: string } | null>(null)
  const prepare = useMutation({ mutationFn: () => {
    if (!key.current || key.current.examples !== examples) key.current = { examples, id: crypto.randomUUID() }
    return api.prepare(lessonId, examples, key.current.id)
  }, onSuccess: async session => { await navigate({ to: '/app/sessions/$sessionId', params: { sessionId: session.id } }) } })
  return <section className="form-section"><h2 className="font-display text-3xl">Practise with ChatGPT</h2><p className="mt-3 text-sm text-muted-foreground">Prepare this lesson for a conversation. ChatGPT can save feedback at the end.</p><label className="mt-4 flex gap-3"><input type="checkbox" checked={examples} onChange={event => setExamples(event.target.checked)} /> Save short examples in final feedback</label><p className="mt-2 text-xs text-muted-foreground">Lingora does not save full transcripts or recordings.</p><Button className="mt-4" disabled={prepare.isPending} onClick={() => prepare.mutate()}>{prepare.isPending ? 'Preparing…' : 'Practice with ChatGPT'}</Button>{prepare.isError && <RequestFailure error={prepare.error} />}<p className="mt-4 text-sm"><Link to="/app/sessions" className="underline">View conversation sessions</Link></p></section>
}

function AccessControl() {
  const auth = useAuth(); const api = useConversationApi(); const cache = useQueryClient()
  const access = useQuery({ queryKey: privateKey(auth.subject, 'mcp-access'), queryFn: ({ signal }) => api.access(signal), retry: false })
  const toggle = useMutation({ mutationFn: (enabled: boolean) => api.setAccess(enabled), onSuccess: async () => { await cache.invalidateQueries({ queryKey: privateKey(auth.subject, 'mcp-access') }) } })
  return <div className="space-y-3"><h2 className="font-display text-2xl">ChatGPT access</h2>{access.isPending ? <p>Checking access…</p> : access.isError ? <RequestFailure error={access.error} retry={() => void access.refetch()} /> : <><p>ChatGPT access: {access.data.enabled ? 'enabled' : 'disabled'}</p><Button variant="outline" disabled={toggle.isPending} onClick={() => toggle.mutate(!access.data.enabled)}>{access.data.enabled ? 'Disable ChatGPT access' : 'Enable ChatGPT access'}</Button>{toggle.isError && <RequestFailure error={toggle.error} />}</>}<p className="text-sm text-muted-foreground">Disabling access blocks Lingora requests. Disconnect the plugin in ChatGPT separately to revoke its connection.</p></div>
}

function SessionList() {
  const auth = useAuth(); const api = useConversationApi()
  const sessions = useQuery({ queryKey: privateKey(auth.subject, 'conversation-sessions'), queryFn: ({ signal }) => api.list(signal), retry: false })
  return <section className="form-section"><Link to="/app" className="underline">Your profile</Link><h1 className="mt-5 font-display text-4xl">Conversation sessions</h1>{sessions.isPending ? <p role="status">Loading…</p> : sessions.isError ? <RequestFailure error={sessions.error} retry={() => void sessions.refetch()} /> : <ul className="mt-5 space-y-3">{sessions.data.map(session => <li key={session.id}><Link className="underline" to="/app/sessions/$sessionId" params={{ sessionId: session.id }}>{session.cefr} conversation · {new Date(session.created_at).toLocaleString()}</Link> — {session.status.toLowerCase().replace('_', ' ')}</li>)}{!sessions.data.length && <li>No conversations yet. Prepare one from a saved lesson.</li>}</ul>}<div className="mt-8"><AccessControl /></div></section>
}

function SessionDetail({ id }: { id: string }) {
  const auth = useAuth(); const api = useConversationApi(); const cache = useQueryClient(); const key = useRef(crypto.randomUUID())
  const [copyState, setCopyState] = useState('')
  const queryKey = [...privateKey(auth.subject, 'conversation-session'), id]
  const session = useQuery({ queryKey, queryFn: ({ signal }) => api.get(id, signal), retry: false })
  const abandon = useMutation({ mutationFn: () => api.abandon(id, session.data!.version, key.current), onSuccess: async () => { await cache.invalidateQueries({ queryKey }); await cache.invalidateQueries({ queryKey: privateKey(auth.subject, 'conversation-sessions') }) } })
  if (session.isPending) return <p role="status">Loading session…</p>
  if (session.isError) return <RequestFailure error={session.error} retry={() => void session.refetch()} />
  const unfinished = session.data.status === 'READY' || session.data.status === 'IN_PROGRESS'
  return <section className="form-section space-y-5"><Link className="underline" to="/app/sessions">All conversations</Link><h1 className="font-display text-4xl">Your {session.data.cefr} conversation</h1><p>Status: {session.data.status.toLowerCase().replace('_', ' ')} · Correction: {session.data.correction_mode}</p><p>Short examples: {session.data.save_examples ? 'allowed' : 'disabled'}. Lingora does not retain the conversation transcript.</p>{unfinished && <><h2 className="font-display text-2xl">Continue in ChatGPT</h2><p>Connect the Lingora MCP plugin in ChatGPT, sign in with this same Lingora account, and say: “Use Lingora to find my pending session and start my lesson.”</p><Button variant="outline" onClick={() => { void navigator.clipboard.writeText('Use Lingora to find my pending session and start my lesson.').then(() => setCopyState('Starter prompt copied.'), () => setCopyState('Select and copy the prompt above.')) }}>Copy starter prompt</Button>{copyState && <p role="status">{copyState}</p>}<AccessControl /><Button variant="outline" disabled={abandon.isPending} onClick={() => { if (window.confirm('Abandon this unfinished conversation?')) abandon.mutate() }}>Abandon session</Button>{abandon.isError && <RequestFailure error={abandon.error} />}</>}{session.data.feedback && <div><h2 className="font-display text-2xl">Saved feedback</h2><p className="mt-3 whitespace-pre-wrap">{session.data.feedback.summary}</p><h3 className="mt-4 font-semibold">Strengths</h3><ul className="list-disc pl-5">{session.data.feedback.strengths.map((item, i) => <li key={i}>{item}</li>)}</ul><h3 className="mt-4 font-semibold">Priorities</h3><ul className="list-disc pl-5">{session.data.feedback.priorities.map((item, i) => <li key={i}>{item}</li>)}</ul><ul className="mt-4 space-y-3">{session.data.feedback.observations.map((observation, i) => <li key={i}><p className="font-semibold">{observation.skill}</p><p>{observation.feedback}</p>{observation.example && <p>Example: {observation.example}</p>}{observation.correction && <p>Suggestion: {observation.correction}</p>}</li>)}</ul></div>}</section>
}
export function ConversationsPage() { return <AccountBoundary><SessionList /></AccountBoundary> }
export function ConversationPage({ id }: { id: string }) { return <AccountBoundary><SessionDetail key={id} id={id} /></AccountBoundary> }
