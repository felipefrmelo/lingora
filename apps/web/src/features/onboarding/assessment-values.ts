import { z } from 'zod'
import type { Assessment, AssessmentInput } from './api'
import { CEFR_LEVELS } from './options'

const component = z.object({ skill: z.string().trim().min(1, 'Name the tested component.').max(100), value: z.string().min(1, 'Enter the original score.').max(64).refine(v => !!v.trim(), 'Enter the original score.'), scale: z.string().max(100), reported_cefr: z.enum(['unknown', ...CEFR_LEVELS]) })
export const assessmentFormSchema = z.object({
  provider: z.enum(['englishscore', 'ef_set', 'other']),
  test_name: z.string().trim().min(1, 'Enter the test name.').max(120), variant: z.string().max(120),
  taken_on: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Choose the assessment date.').refine(v => v <= new Date().toISOString().slice(0, 10), 'The date cannot be in the future.'),
  overall_value: z.string().max(64), overall_scale: z.string().max(100),
  component_scores: z.array(component).max(20), reported_cefr: z.enum(['unknown', ...CEFR_LEVELS]),
}).superRefine((v, ctx) => {
  if (!v.overall_value.trim() && !v.component_scores.length && v.reported_cefr === 'unknown') ctx.addIssue({ code: 'custom', path: ['overall_value'], message: 'Enter a score, a tested component, or the test’s reported CEFR.' })
  const labels = v.component_scores.map(c => c.skill.toLowerCase())
  if (new Set(labels).size !== labels.length) ctx.addIssue({ code: 'custom', path: ['component_scores'], message: 'Use different component names.' })
})
export type AssessmentFormValues = z.infer<typeof assessmentFormSchema>

export function assessmentValues(record?: Assessment): AssessmentFormValues {
  return { provider: record?.provider || 'other', test_name: record?.test_name || '', variant: record?.variant || '', taken_on: record?.taken_on || '', overall_value: record?.overall_score?.value || '', overall_scale: record?.overall_score?.scale || '', reported_cefr: record?.reported_cefr || 'unknown', component_scores: (record?.component_scores || []).map(c => ({ ...c, scale: c.scale || '', reported_cefr: c.reported_cefr || 'unknown' })) }
}

export function assessmentPayload(values: AssessmentFormValues): AssessmentInput {
  return { provider: values.provider, test_name: values.test_name, variant: values.variant || null, taken_on: values.taken_on,
    overall_score: values.overall_value.trim() ? { value: values.overall_value, scale: values.overall_scale || null } : null,
    component_scores: values.component_scores.map(c => ({ ...c, scale: c.scale || null, reported_cefr: c.reported_cefr === 'unknown' ? null : c.reported_cefr })),
    reported_cefr: values.reported_cefr === 'unknown' ? null : values.reported_cefr,
  }
}

