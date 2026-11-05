import { zodResolver } from '@hookform/resolvers/zod'
import { useQueryClient } from '@tanstack/react-query'
import { Link, useNavigate } from '@tanstack/react-router'
import { useState } from 'react'
import { useForm, type UseFormReturn } from 'react-hook-form'
import { useAuth } from '../../auth/context'
import { PrivateApiError, privateKey } from '../../auth/private-api'
import { Button } from '../../components/ui/button'
import type { Profile, ProfileWrite } from './api'
import { AssessmentManager } from './assessments'
import { Field, RequestFailure } from './shared'
import { useLearningApi, useUnsavedChanges } from './hooks'
import { CEFR_LEVELS } from './options'
import { profileFormSchema, toProfileForm, profilePayload, type ProfileFormValues } from './profile-values'

const suggestions = {
  goals: ['Everyday conversation', 'Travel', 'Work', 'Reading', 'Confidence'],
  interests: ['Technology', 'Culture', 'Science', 'Sports', 'Travel', 'Business'],
}

function TagChoices({ name, label, form }: { name: 'goals' | 'interests'; label: string; form: UseFormReturn<ProfileFormValues> }) {
  const values = form.watch(name)
  const custom = name === 'goals' ? 'custom_goal' : 'custom_interest'
  const choices = [...new Set([...suggestions[name], ...values])]
  function add() {
    const value = form.getValues(custom).trim()
    if (!value) return
    if (values.length >= 10 || values.some(x => x.toLowerCase() === value.toLowerCase())) {
      form.setError(custom, { message: 'Use at most 10 different entries.' }); return
    }
    form.setValue(name, [...values, value], { shouldDirty: true, shouldValidate: true })
    form.setValue(custom, '', { shouldDirty: true, shouldValidate: true })
  }
  return <fieldset className="space-y-3">
    <legend className="field-label">{label}</legend>
    <div className="flex flex-wrap gap-2">{choices.map(value => <button key={value} type="button" aria-pressed={values.includes(value)} className={`rounded-full border px-4 py-2 text-sm ${values.includes(value) ? 'border-primary bg-primary text-primary-foreground' : 'border-border bg-background'}`} onClick={() => form.setValue(name, values.includes(value) ? values.filter(x => x !== value) : [...values, value], { shouldDirty: true, shouldValidate: true })}>{value}</button>)}</div>
    <Field id={custom} label={`Add your own ${name === 'goals' ? 'goal' : 'topic'}`} error={form.formState.errors[custom]?.message || form.formState.errors[name]?.message}>
      <div className="flex gap-2"><input id={custom} className="field-input min-w-0" maxLength={100} {...form.register(custom)} onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); add() } }} /><Button type="button" variant="outline" onClick={add}>Add</Button></div>
    </Field>
  </fieldset>
}

export function ProfileForm({ profile, wizard = false }: { profile: Profile; wizard?: boolean }) {
  const [saved, setSaved] = useState(profile)
  const [step, setStep] = useState(0)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const [notice, setNotice] = useState('')
  const [assessmentDirty, setAssessmentDirty] = useState(false)
  const [assessmentReset, setAssessmentReset] = useState(0)
  const api = useLearningApi()
  const auth = useAuth()
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const form = useForm<ProfileFormValues>({ resolver: zodResolver(profileFormSchema), defaultValues: toProfileForm(profile) })
  const allowNavigation = useUnsavedChanges(form.formState.isDirty)
  const errors = form.formState.errors
  const titles = ['About you', 'Your English', 'Your routine']

  async function persist(values: ProfileFormValues, intent: ProfileWrite['intent'], checkAssessment = true) {
    if (checkAssessment && !discardAssessment()) return
    setSaving(true); setError(null); setNotice('')
    try {
      const response = await api.saveProfile(profilePayload(values, saved.version || 0, intent))
      setSaved(response); form.reset(toProfileForm(response))
      queryClient.setQueryData(privateKey(auth.subject, 'profile'), response)
      if (intent === 'skip' || intent === 'finish' || !wizard) {
        allowNavigation()
        await navigate({ to: '/app' })
      } else { setStep(s => s + 1); setNotice('Your progress is saved.') }
    } catch (cause) { setError(cause) } finally { setSaving(false) }
  }

  async function reload() {
    if (form.formState.isDirty && !window.confirm('Replace your unsaved input with the latest saved profile?')) return
    setSaving(true)
    try {
      const response = await api.profile()
      setSaved(response); form.reset(toProfileForm(response)); setError(null)
      queryClient.setQueryData(privateKey(auth.subject, 'profile'), response)
      setNotice('The latest saved profile is loaded.')
    } catch (cause) { setError(cause) } finally { setSaving(false) }
  }

  const submit = form.handleSubmit(values => persist(values, wizard ? (step === 2 ? 'finish' : 'resume') : 'save'), () => setNotice('Please check your entries.'))
  function discardAssessment() {
    if (!assessmentDirty) return true
    if (!window.confirm('Discard your unsaved assessment entry before leaving this step?')) return false
    setAssessmentReset(n => n + 1); setAssessmentDirty(false)
    return true
  }
  const show = (index: number) => !wizard || step === index
  return <div className="space-y-8">
    <header>
      <p className="text-xs font-semibold uppercase tracking-widest text-primary">{wizard ? 'Make yourself at home' : 'Your learning profile'}</p>
      <h1 className="mt-3 font-display text-4xl">{wizard ? titles[step] : 'A little more you.'}</h1>
      <p className="mt-4 text-muted-foreground">Every field is optional. You can change these choices whenever you like.</p>
      {wizard && <ol aria-label="Setup progress" className="mt-6 flex flex-wrap gap-5 text-sm">{titles.map((title, index) => <li key={title} aria-current={index === step ? 'step' : undefined} className={index === step ? 'font-semibold text-primary' : 'text-muted-foreground'}>{index + 1}. {title}</li>)}</ol>}
    </header>
    {error != null && <RequestFailure error={error} retry={() => void (error instanceof PrivateApiError && error.status === 409 ? reload() : submit())} />}
    <p role="status" className="text-sm text-primary">{notice}</p>
    <form onSubmit={e => void submit(e)} className="space-y-8" noValidate>
      <fieldset disabled={saving} className="space-y-8">
        {show(0) && <section className="form-section space-y-7" aria-label="About you">
          <div className="grid gap-6 sm:grid-cols-2">
            <Field id="preferred_name" label="What should we call you?" error={errors.preferred_name?.message}><input id="preferred_name" className="field-input" maxLength={80} autoComplete="nickname" {...form.register('preferred_name')} /></Field>
            <Field id="native_language" label="Native language" error={errors.native_language?.message}><input id="native_language" className="field-input" placeholder="For example, Portuguese" maxLength={80} {...form.register('native_language')} /></Field>
          </div>
          <TagChoices name="goals" label="What would you like English to help you do?" form={form} />
          <TagChoices name="interests" label="What catches your curiosity?" form={form} />
        </section>}
        {show(1) && <section className="form-section space-y-6" aria-label="Your English">
          <Field id="selected_cefr" label="Your starting English level" error={errors.selected_cefr?.message}><select id="selected_cefr" className="field-input" {...form.register('selected_cefr')}><option value="unknown">I don’t know yet</option>{CEFR_LEVELS.map((level, i) => <option key={level} value={level}>{level} — {['Beginner', 'Elementary', 'Intermediate', 'Upper intermediate', 'Advanced', 'Proficient'][i]}</option>)}</select></Field>
          <p className="text-sm text-muted-foreground">This is your choice, not a verified assessment. Test results stay separate and never change it automatically.</p>
          {wizard && <p className="text-sm">Have a test result? You can add it below. You can also start without a test.</p>}
        </section>}
        {show(2) && <section className="form-section space-y-7" aria-label="Your routine">
          <div className="grid gap-6 sm:grid-cols-2">
            <Field id="sessions_per_week" label="Sessions per week" error={errors.sessions_per_week?.message}><select id="sessions_per_week" className="field-input" {...form.register('sessions_per_week')}><option value="">Decide later</option>{[1, 2, 3, 4, 5, 6, 7].map(n => <option key={n} value={n}>{n}</option>)}</select></Field>
            <Field id="session_duration_minutes" label="Minutes per session" error={errors.session_duration_minutes?.message}><input id="session_duration_minutes" className="field-input" type="number" min={5} max={120} placeholder="Decide later" {...form.register('session_duration_minutes')} /></Field>
          </div>
          <fieldset className="space-y-3"><legend className="field-label">How would you like conversation corrections?</legend>{([['free', 'Free', 'Feedback mainly at the end.'], ['balanced', 'Balanced', 'Occasional corrections along the way.'], ['intensive', 'Intensive', 'Frequent corrections and sentence reformulations.']] as const).map(([value, label, description]) => <label key={value} className="flex cursor-pointer gap-3 rounded-2xl border border-border p-4"><input type="radio" value={value} {...form.register('correction_mode')} /><span><span className="block font-semibold">{label}</span><span className="text-sm text-muted-foreground">{description}</span></span></label>)}</fieldset>
        </section>}
      </fieldset>
      <div className="flex flex-wrap items-center gap-3">
        {wizard && step > 0 && <Button type="button" variant="outline" disabled={saving} onClick={() => { if ((form.formState.isDirty || assessmentDirty) && !window.confirm('Go back and discard unsaved changes on this step? Your saved progress will be kept.')) return; form.reset(toProfileForm(saved)); setAssessmentDirty(false); setStep(s => s - 1); setNotice('') }}>Back</Button>}
        <Button type="submit" disabled={saving}>{saving ? 'Saving…' : !wizard ? 'Save profile' : step === 2 ? 'Finish setup' : 'Save and continue'}</Button>
        {wizard ? <Button type="button" variant="outline" disabled={saving} onClick={() => { if ((form.formState.isDirty || assessmentDirty) && !window.confirm('Skip setup and discard unsaved changes? Your saved progress will be kept.')) return; setAssessmentReset(n => n + 1); setAssessmentDirty(false); void persist(toProfileForm(saved), 'skip', false) }}>Skip for now</Button> : <Link to="/app" className="text-sm underline">Cancel</Link>}
      </div>
    </form>
    {wizard && step === 1 && <AssessmentManager key={assessmentReset} onDirtyChange={setAssessmentDirty} />}
  </div>
}
