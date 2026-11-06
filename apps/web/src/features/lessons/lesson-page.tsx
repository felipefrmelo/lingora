import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from '@tanstack/react-router'
import { useRef, useState } from 'react'
import { useAuth } from '../../auth/context'
import { privateKey } from '../../auth/private-api'
import { Button } from '../../components/ui/button'
import { useUnsavedChanges } from '../onboarding/hooks'
import { RequestFailure } from '../onboarding/shared'
import { SourceCredit } from './catalog-page'
import { PrepareConversation } from '../conversation/pages'
import { useLessonApi, type Attempt, type Lesson } from './api'

function Feedback({ attempt }: { attempt: Attempt }) {
  return <article className="rounded-2xl border border-border bg-muted p-6"><h3 className="font-display text-2xl">{attempt.correct} of {attempt.total} exercises correct</h3><p className="mt-2 text-xs text-muted-foreground">Saved {new Date(attempt.created_at).toLocaleString()} · A record of this practice, not a proficiency score.</p><ol className="mt-5 space-y-5">{attempt.results.map((result, index) => <li key={index}><p className="font-semibold">{index + 1}. {result.correct ? 'Correct' : 'Keep practising'} · {result.skill}</p><p className="mt-1 text-sm">Your answer: {attempt.answers[index]?.filter(Boolean).join(' · ') || 'Skipped'}</p><p className="mt-1 text-sm">Accepted: {result.expected.join(' · ')}</p><p className="mt-2 text-sm leading-relaxed text-muted-foreground">{result.explanation}</p></li>)}</ol></article>
}

function StudyLesson({ lesson }: { lesson: Lesson }) {
  const auth = useAuth()
  const api = useLessonApi()
  const cache = useQueryClient()
  const [answers, setAnswers] = useState<string[][]>(() => lesson.exercises.map(exercise => exercise.kind === 'matching' ? exercise.parts.map(() => '') : ['']))
  const [saved, setSaved] = useState(() => JSON.stringify(answers))
  const [latest, setLatest] = useState<Attempt | null>(null)
  const [offset, setOffset] = useState(0)
  const key = useRef<{ payload: string; key: string } | null>(null)
  useUnsavedChanges(JSON.stringify(answers) !== saved)
  const historyKey = [...privateKey(auth.subject, 'attempts'), lesson.id, offset]
  const history = useQuery({ queryKey: historyKey, queryFn: ({ signal }) => api.attempts(lesson.id, offset, signal), retry: false })
  const submit = useMutation({ mutationFn: async () => {
    const payload = JSON.stringify(answers)
    if (key.current?.payload !== payload) key.current = { payload, key: crypto.randomUUID() }
    return api.submit(lesson.id, answers, key.current.key)
  }, onSuccess: async attempt => {
    setSaved(JSON.stringify(attempt.answers)); setLatest(attempt); key.current = null
    await cache.invalidateQueries({ queryKey: privateKey(auth.subject, 'attempts') })
  } })
  function change(index: number, part: number, value: string) {
    setAnswers(previous => previous.map((row, i) => i === index ? row.map((answer, j) => j === part ? value : answer) : row))
  }
  return <div className="space-y-9">
    <header><Link to="/app/learn" className="text-sm underline">All lessons</Link><p className="mt-6 text-xs font-semibold uppercase tracking-widest text-primary">Your {lesson.cefr} reading practice</p><h1 className="mt-3 font-display text-4xl sm:text-5xl">{lesson.title}</h1><p className="mt-4 text-sm text-muted-foreground">{lesson.level_reason} AI-generated teaching material, adapted from a news brief; details may be imperfect.</p><SourceCredit source={lesson.source} /><p className="mt-2 text-xs text-muted-foreground">Adapted and expanded for English practice. Hypothetical examples are not news reporting.</p></header>
    <section className="form-section"><h2 className="font-display text-2xl">What you’ll practise</h2><ul className="mt-4 list-disc space-y-2 pl-5">{lesson.objectives.map(objective => <li key={objective}>{objective}</li>)}</ul></section>
    <section className="form-section"><h2 className="font-display text-3xl">Read in context</h2><p className="mt-5 whitespace-pre-line text-lg leading-loose">{lesson.reading}</p></section>
    <section className="form-section"><h2 className="font-display text-3xl">Words to take with you</h2><dl className="mt-5 grid gap-5 sm:grid-cols-2">{lesson.vocabulary.map(word => <div key={word.term}><dt className="font-semibold">{word.term}</dt><dd className="mt-1 text-muted-foreground">{word.meaning}</dd></div>)}</dl></section>
    <form className="space-y-6" onSubmit={event => { event.preventDefault(); submit.mutate() }}><header><h2 className="font-display text-3xl">Put it into practice</h2><p className="mt-3 text-sm text-muted-foreground">Short answers use exact accepted phrases, ignoring case and extra spaces. Spelling and punctuation count. Leave an answer blank to skip it. Matching answers follow the word order shown.</p></header>
      {lesson.exercises.map((exercise, index) => <fieldset key={index} disabled={submit.isPending} className="form-section"><legend className="px-2 text-xs font-semibold uppercase tracking-wider">Exercise {index + 1} · {exercise.kind.replace('_', ' ')}</legend><p id={`prompt-${index}`} className="font-semibold">{exercise.prompt}</p><p className="mt-2 text-xs text-muted-foreground">{exercise.skill}</p><div className="mt-4 space-y-3">{exercise.kind === 'choice' ? exercise.options.map(option => <label key={option} className="flex items-start gap-3 rounded-xl border border-border p-3"><input type="radio" name={`exercise-${index}`} value={option} checked={answers[index]?.[0] === option} onChange={() => change(index, 0, option)} className="mt-1" />{option}</label>) : exercise.kind === 'matching' ? exercise.parts.map((part, partIndex) => <label key={partIndex} className="field-label">{part}<select className="field-input mt-2" value={answers[index]?.[partIndex] || ''} onChange={event => change(index, partIndex, event.target.value)}><option value="">Choose a meaning</option>{exercise.options.map(option => <option key={option}>{option}</option>)}</select></label>) : <label className="field-label">Your answer<input className="field-input mt-2" aria-describedby={`prompt-${index}`} maxLength={300} value={answers[index]?.[0] || ''} onChange={event => change(index, 0, event.target.value)} /></label>}</div></fieldset>)}
      {submit.isError && <RequestFailure error={submit.error} />}
      <Button disabled={submit.isPending} type="submit">{submit.isPending ? 'Saving your answers…' : 'Save answers and check'}</Button><p className="text-sm text-muted-foreground">Answers are saved only after confirmation. Your selected CEFR stays unchanged.</p>
    </form>
    {latest && <section aria-label="Latest feedback" role="status"><Feedback attempt={latest} /></section>}
    <section className="form-section"><h2 className="font-display text-3xl">Conversation starters</h2><ul className="mt-5 list-disc space-y-3 pl-5">{lesson.discussion.map(question => <li key={question}>{question}</li>)}</ul><p className="mt-5 text-sm text-muted-foreground">Try these aloud or prepare a conversation below.</p></section>
    <PrepareConversation lessonId={lesson.id} />
    <section aria-labelledby="attempts-title"><h2 id="attempts-title" className="font-display text-3xl">Saved practice</h2>{history.isPending ? <p role="status" className="mt-4">Loading saved attempts…</p> : history.isError ? <RequestFailure error={history.error} retry={() => void history.refetch()} /> : <><div className="mt-5 space-y-5">{history.data.map(attempt => <Feedback key={attempt.id} attempt={attempt} />)}{!history.data.length && <p>Your first saved attempt will appear here.</p>}</div><div className="mt-4 flex gap-3"><Button variant="outline" disabled={!offset} onClick={() => setOffset(Math.max(0, offset - 12))}>Newer attempts</Button><Button variant="outline" disabled={history.data.length < 12} onClick={() => setOffset(offset + 12)}>Older attempts</Button></div></>}
    </section>
  </div>
}

export function LessonPage({ lessonId }: { lessonId: string }) {
  const auth = useAuth()
  const api = useLessonApi()
  const lesson = useQuery({ queryKey: [...privateKey(auth.subject, 'lesson'), lessonId], queryFn: ({ signal }) => api.lesson(lessonId, signal), retry: false })
  if (lesson.isPending) return <p role="status">Opening your lesson…</p>
  if (lesson.isError) return <RequestFailure error={lesson.error} retry={() => void lesson.refetch()} />
  return <StudyLesson key={`${auth.subject}-${lessonId}`} lesson={lesson.data} />
}
