import { Link, Navigate } from '@tanstack/react-router'
import { useAuth } from '../../auth/context'
import { Button } from '../../components/ui/button'
import { AssessmentManager } from './assessments'
import { RequestFailure } from './shared'
import { useProfile } from './hooks'

export function ProfileOverview() {
  const profile = useProfile()
  const auth = useAuth()
  if (profile.isPending) return <p role="status">Loading your learning profile…</p>
  if (profile.isError) return <RequestFailure error={profile.error} retry={() => void profile.refetch()} />
  const data = profile.data
  if (data.onboarding_status === 'not_started' || data.onboarding_status === 'in_progress') return <Navigate to="/app/onboarding" replace />
  const name = data.preferred_name || auth.name
  return <div className="space-y-10">
    <header className="flex flex-wrap items-start justify-between gap-6">
      <div><p className="text-xs font-semibold uppercase tracking-widest text-primary">Your Lingora space</p><h1 className="mt-4 font-display text-4xl sm:text-5xl">Welcome{name ? `, ${name}` : ''}.</h1><p className="mt-4 text-muted-foreground">A learning profile shaped around your world.</p>{auth.email && <p className="mt-3 break-all text-sm text-muted-foreground">Signed in as {auth.email}</p>}</div>
      <Button asChild variant="outline"><Link to="/app/profile">Edit profile</Link></Button>
    </header>
    {data.onboarding_status === 'skipped' && <aside className="rounded-2xl border border-border bg-muted p-6"><h2 className="font-semibold">Settle in at your own pace.</h2><p className="mt-2 text-sm text-muted-foreground">Your saved choices are here. Finish setup whenever you’re ready.</p><Button asChild className="mt-4" size="sm"><Link to="/app/onboarding">Resume setup</Link></Button></aside>}
    <section className="form-section" aria-labelledby="profile-title">
      <div className="flex flex-wrap items-center justify-between gap-3"><h2 id="profile-title" className="font-display text-3xl">Your learning profile</h2><span className="rounded-full bg-muted px-3 py-1 text-xs">{data.onboarding_status === 'completed' ? 'Setup complete' : 'Setup saved for later'}</span></div>
      <dl className="mt-7 grid gap-6 sm:grid-cols-2">
        <div><dt className="field-label">Native language</dt><dd className="mt-2 text-muted-foreground">{data.native_language || 'Not set yet'}</dd></div>
        <div><dt className="field-label">Your selected level</dt><dd className="mt-2 text-muted-foreground">{data.selected_cefr || 'Not sure yet'}{data.selected_cefr && <span className="ml-2 text-xs">Self-selected</span>}</dd></div>
        <div><dt className="field-label">Learning goals</dt><dd className="mt-2 text-muted-foreground">{data.goals?.length ? data.goals.join(' · ') : 'Open to discovery'}</dd></div>
        <div><dt className="field-label">Interests</dt><dd className="mt-2 text-muted-foreground">{data.interests?.length ? data.interests.join(' · ') : 'Open to discovery'}</dd></div>
        <div><dt className="field-label">Study rhythm</dt><dd className="mt-2 text-muted-foreground">{data.sessions_per_week ? `${data.sessions_per_week} sessions per week` : 'Frequency not set'}{data.session_duration_minutes ? ` · ${data.session_duration_minutes} minutes each` : ''}</dd></div>
        <div><dt className="field-label">Conversation corrections</dt><dd className="mt-2 capitalize text-muted-foreground">{data.correction_mode || 'balanced'}</dd></div>
      </dl>
    </section>
    <aside className="rounded-3xl border border-border bg-muted p-7"><p className="text-xs font-semibold uppercase tracking-widest text-primary">Up next</p><h2 className="mt-3 font-display text-2xl">Your next discovery starts here.</h2><p className="mt-3 leading-relaxed text-muted-foreground">Explore news briefs, find a topic that interests you, and practise English at your selected level.</p><Button asChild className="mt-5"><Link to="/app/learn">Find my first lesson</Link></Button></aside>
    <AssessmentManager />
  </div>
}
