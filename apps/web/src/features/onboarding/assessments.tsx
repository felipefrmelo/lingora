import { zodResolver } from '@hookform/resolvers/zod'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useState } from 'react'
import { useFieldArray, useForm } from 'react-hook-form'
import { useAuth } from '../../auth/context'
import { PrivateApiError, privateKey } from '../../auth/private-api'
import { Button } from '../../components/ui/button'
import type { Assessment } from './api'
import { Field, RequestFailure } from './shared'
import { useLearningApi, useUnsavedChanges } from './hooks'
import { CEFR_LEVELS } from './options'
import { assessmentFormSchema, assessmentValues, assessmentPayload, type AssessmentFormValues } from './assessment-values'

function AssessmentForm({ record, close, refresh, onDirtyChange }: { record?: Assessment; close: () => void; refresh: () => Promise<unknown>; onDirtyChange?: (dirty: boolean) => void }) {
  const [key] = useState(() => crypto.randomUUID())
  const [error, setError] = useState<unknown>(null)
  const [saving, setSaving] = useState(false)
  const [version, setVersion] = useState(record?.version || 1)
  const api = useLearningApi()
  const form = useForm<AssessmentFormValues>({ resolver: zodResolver(assessmentFormSchema), defaultValues: assessmentValues(record) })
  const components = useFieldArray({ control: form.control, name: 'component_scores' })
  const allowNavigation = useUnsavedChanges(form.formState.isDirty)
  const errors = form.formState.errors
  useEffect(() => { onDirtyChange?.(form.formState.isDirty); return () => onDirtyChange?.(false) }, [form.formState.isDirty, onDirtyChange])
  const prefix = 'assessment-'

  const submit = form.handleSubmit(async values => {
    setError(null); setSaving(true)
    try {
      const data = assessmentPayload(values)
      if (record) await api.updateAssessment(record.id, { ...data, expected_version: version })
      else await api.createAssessment(data, key)
      form.reset(values); allowNavigation()
      await refresh(); close()
    } catch (cause) { setError(cause) } finally { setSaving(false) }
  })

  async function reload() {
    if (record && form.formState.isDirty && !window.confirm('Replace your unsaved input with the latest saved assessment?')) return
    setSaving(true)
    try {
      const first = await api.assessments()
      let found = first.items.find(item => item.id === record?.id)
      for (let offset = 20; record && !found && offset < first.total; offset += 20) {
        found = (await api.assessments(offset)).items.find(item => item.id === record.id)
      }
      if (record) {
        if (!found) throw new PrivateApiError(410)
        setVersion(found.version); form.reset(assessmentValues(found)); setError(null)
      }
      await refresh()
    } catch (cause) { setError(cause) } finally { setSaving(false) }
  }

  function cancel() { if (!form.formState.isDirty || window.confirm('Discard this unsaved assessment entry?')) close() }
  return <section className="form-section space-y-6" aria-labelledby="assessment-form-title">
    <h3 id="assessment-form-title" className="font-display text-2xl">{record ? 'Edit assessment' : 'Record a test result'}</h3>
    <p className="text-sm text-muted-foreground">Self-reported results only. Copy original scores and scale labels; adding a result won’t change your starting level.</p>
    {error != null && <><RequestFailure error={error} retry={() => void (error instanceof PrivateApiError && [409, 410].includes(error.status) ? reload() : submit())} />{!record && error instanceof PrivateApiError && error.status === 409 && <p className="text-sm">A previous save may already exist. Reload and review your records below before cancelling this form to start another entry.</p>}</>}
    <form onSubmit={e => void submit(e)} className="space-y-6" noValidate>
      <fieldset disabled={saving} className="space-y-6">
        <div className="grid gap-5 sm:grid-cols-2">
          <Field id={`${prefix}provider`} label="Test provider"><select id={`${prefix}provider`} className="field-input" {...form.register('provider')}><option value="other">Other</option><option value="englishscore">EnglishScore</option><option value="ef_set">EF SET</option></select></Field>
          <Field id={`${prefix}name`} label="Test name" error={errors.test_name?.message}><input id={`${prefix}name`} className="field-input" maxLength={120} {...form.register('test_name')} /></Field>
          <Field id={`${prefix}variant`} label="Test variant (optional)" error={errors.variant?.message}><input id={`${prefix}variant`} className="field-input" placeholder="For example, Core Skills or 4 skills" maxLength={120} {...form.register('variant')} /></Field>
          <Field id={`${prefix}date`} label="Assessment date" error={errors.taken_on?.message}><input id={`${prefix}date`} className="field-input" type="date" max={new Date().toISOString().slice(0, 10)} {...form.register('taken_on')} /></Field>
          <Field id={`${prefix}overall`} label="Original overall score (optional)" error={errors.overall_value?.message}><input id={`${prefix}overall`} className="field-input" maxLength={64} {...form.register('overall_value')} /></Field>
          <Field id={`${prefix}scale`} label="Overall scale (optional)" error={errors.overall_scale?.message}><input id={`${prefix}scale`} className="field-input" placeholder="For example, 0–100" maxLength={100} {...form.register('overall_scale')} /></Field>
          <Field id={`${prefix}cefr`} label="CEFR reported by this test (optional)"><select id={`${prefix}cefr`} className="field-input" {...form.register('reported_cefr')}><option value="unknown">Not reported</option>{CEFR_LEVELS.map(level => <option key={level}>{level}</option>)}</select></Field>
        </div>
        <fieldset className="space-y-4"><legend className="field-label">Original component scores (optional)</legend>
          {components.fields.map((item, index) => <div key={item.id} className="space-y-4 rounded-2xl border border-border p-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <Field id={`skill-${item.id}`} label={`Component ${index + 1}`} error={errors.component_scores?.[index]?.skill?.message}><input id={`skill-${item.id}`} className="field-input" placeholder="For example, Reading or Grammar" {...form.register(`component_scores.${index}.skill`)} /></Field>
              <Field id={`value-${item.id}`} label={`Component ${index + 1} score`} error={errors.component_scores?.[index]?.value?.message}><input id={`value-${item.id}`} className="field-input" {...form.register(`component_scores.${index}.value`)} /></Field>
              <Field id={`scale-${item.id}`} label={`Component ${index + 1} scale`} error={errors.component_scores?.[index]?.scale?.message}><input id={`scale-${item.id}`} className="field-input" {...form.register(`component_scores.${index}.scale`)} /></Field>
              <Field id={`cefr-${item.id}`} label={`Component ${index + 1} reported CEFR`}><select id={`cefr-${item.id}`} className="field-input" {...form.register(`component_scores.${index}.reported_cefr`)}><option value="unknown">Not reported</option>{CEFR_LEVELS.map(level => <option key={level}>{level}</option>)}</select></Field>
            </div><Button type="button" variant="outline" size="sm" onClick={() => components.remove(index)}>Remove component {index + 1}</Button>
          </div>)}
          {errors.component_scores?.root?.message && <p role="alert" className="field-error">{errors.component_scores.root.message}</p>}
          <Button type="button" variant="outline" size="sm" disabled={components.fields.length >= 20} onClick={() => components.append({ skill: '', value: '', scale: '', reported_cefr: 'unknown' })}>Add component score</Button>
        </fieldset>
      </fieldset>
      <div className="flex flex-wrap gap-3"><Button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save assessment'}</Button><Button type="button" variant="outline" disabled={saving} onClick={cancel}>Cancel assessment</Button></div>
    </form>
  </section>
}

export function AssessmentManager({ onDirtyChange }: { onDirtyChange?: (dirty: boolean) => void }) {
  const [offset, setOffset] = useState(0)
  const [editing, setEditing] = useState<Assessment | 'new' | null>(null)
  const [deleting, setDeleting] = useState(false)
  const [error, setError] = useState<unknown>(null)
  const auth = useAuth()
  const api = useLearningApi()
  const client = useQueryClient()
  const key = [...privateKey(auth.subject, 'assessments'), offset]
  const records = useQuery({ queryKey: key, queryFn: ({ signal }) => api.assessments(offset, signal), retry: false })
  async function refresh() { await client.invalidateQueries({ queryKey: privateKey(auth.subject, 'assessments') }) }
  async function remove(item: Assessment) {
    if (!window.confirm(`Delete your self-reported ${item.test_name} result?`)) return
    setDeleting(true); setError(null)
    try { await api.deleteAssessment(item.id, item.version); if ((records.data?.items.length || 0) === 1 && offset) setOffset(Math.max(0, offset - 20)); await refresh() } catch (cause) { setError(cause) } finally { setDeleting(false) }
  }
  return <section className="space-y-6" aria-labelledby="assessments-title">
    <div className="flex flex-wrap items-center justify-between gap-4"><div><p className="text-xs uppercase tracking-widest text-primary">Optional evidence</p><h2 id="assessments-title" className="mt-2 font-display text-3xl">Your test results</h2></div>{editing === null && <Button type="button" variant="outline" onClick={() => setEditing('new')}>Add assessment</Button>}</div>
    <p className="text-sm leading-relaxed text-muted-foreground">No test is required. If you’d like one, explore <a className="underline" href="https://www.britishcouncil.org/english/learn-online/englishscore" target="_blank" rel="noreferrer">EnglishScore</a> or <a className="underline" href="https://www.efset.org/" target="_blank" rel="noreferrer">EF SET</a>. Record which version you took and only the components it actually tested.</p>
    {editing !== null && <AssessmentForm key={editing === 'new' ? 'new' : editing.id} record={editing === 'new' ? undefined : editing} close={() => setEditing(null)} refresh={refresh} onDirtyChange={onDirtyChange} />}
    {error != null && <RequestFailure error={error} retry={() => { setError(null); void refresh() }} />}
    {records.isPending ? <p role="status">Loading your assessments…</p> : records.isError ? <RequestFailure error={records.error} retry={() => void records.refetch()} /> : <>
      {!records.data.items.length && <p className="rounded-2xl border border-dashed border-border p-6 text-muted-foreground">No assessment results recorded yet. You can start with your own level estimate.</p>}
      <ul className="space-y-4">{records.data.items.map(item => <li key={item.id} className="rounded-2xl border border-border bg-card p-6">
        <div className="flex flex-wrap justify-between gap-4"><div><h3 className="font-semibold">{item.test_name}{item.variant ? ` · ${item.variant}` : ''}</h3><p className="mt-1 text-sm text-muted-foreground">{item.taken_on} · Self-reported</p></div><div className="flex gap-2"><Button type="button" variant="outline" size="sm" disabled={editing !== null || deleting} onClick={() => setEditing(item)} aria-label={`Edit ${item.test_name}`}>Edit</Button><Button type="button" variant="outline" size="sm" disabled={editing !== null || deleting} onClick={() => void remove(item)} aria-label={`Delete ${item.test_name}`}>Delete</Button></div></div>
        {item.overall_score && <p className="mt-4 text-sm">Overall: {item.overall_score.value}{item.overall_score.scale ? ` (${item.overall_score.scale})` : ''}</p>}
        {item.reported_cefr && <p className="mt-2 text-sm">Test-reported CEFR: {item.reported_cefr}</p>}
        <ul className="mt-3 space-y-1 text-sm">{item.component_scores?.map(score => <li key={score.skill}>{score.skill}: {score.value}{score.scale ? ` (${score.scale})` : ''}{score.reported_cefr ? ` · ${score.reported_cefr}` : ''}</li>)}</ul>
      </li>)}</ul>
      {records.data.total > 20 && <nav aria-label="Assessment pages" className="flex items-center gap-4"><Button type="button" variant="outline" disabled={offset === 0} onClick={() => setOffset(Math.max(0, offset - 20))}>Previous</Button><span className="text-sm">{offset + 1}–{Math.min(offset + 20, records.data.total)} of {records.data.total}</span><Button type="button" variant="outline" disabled={offset + 20 >= records.data.total} onClick={() => setOffset(offset + 20)}>Next</Button></nav>}
    </>}
  </section>
}
