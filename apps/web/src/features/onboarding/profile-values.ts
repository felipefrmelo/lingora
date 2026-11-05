import { z } from 'zod'
import type { Profile, ProfileWrite } from './api'
import { CEFR_LEVELS } from './options'

const tag = z.string().trim().min(1, 'Enter a short label.').max(100, 'Use at most 100 characters.')
const tags = z.array(tag).max(10, 'Choose at most 10 entries.').refine(v => new Set(v.map(x => x.toLowerCase())).size === v.length, 'Remove duplicate entries.')
export const profileFormSchema = z.object({
  preferred_name: z.string().max(80, 'Use at most 80 characters.'),
  native_language: z.string().max(80, 'Use at most 80 characters.'),
  goals: tags, interests: tags,
  custom_goal: z.string().max(100, 'Use at most 100 characters.'),
  custom_interest: z.string().max(100, 'Use at most 100 characters.'),
  selected_cefr: z.enum(['unknown', ...CEFR_LEVELS]),
  sessions_per_week: z.string().refine(v => v === '' || /^[1-7]$/.test(v), 'Choose 1 to 7 sessions per week.'),
  session_duration_minutes: z.string().refine(v => v === '' || (/^\d+$/.test(v) && Number(v) >= 5 && Number(v) <= 120), 'Choose 5 to 120 minutes.'),
  correction_mode: z.enum(['free', 'balanced', 'intensive']),
}).superRefine((v, ctx) => {
  for (const [field, extra] of [['goals', 'custom_goal'], ['interests', 'custom_interest']] as const) {
    const values = [...v[field], ...(v[extra].trim() ? [v[extra].trim()] : [])]
    if (values.length > 10 || new Set(values.map(x => x.toLowerCase())).size !== values.length) {
      ctx.addIssue({ code: 'custom', path: [extra], message: 'Use at most 10 different entries.' })
    }
  }
})
export type ProfileFormValues = z.infer<typeof profileFormSchema>

export function toProfileForm(profile: Profile): ProfileFormValues {
  return {
    preferred_name: profile.preferred_name || '', native_language: profile.native_language || '',
    goals: profile.goals || [], interests: profile.interests || [], custom_goal: '', custom_interest: '',
    selected_cefr: profile.selected_cefr || 'unknown', sessions_per_week: profile.sessions_per_week?.toString() || '',
    session_duration_minutes: profile.session_duration_minutes?.toString() || '', correction_mode: profile.correction_mode || 'balanced',
  }
}

export function profilePayload(values: ProfileFormValues, version: number, intent: ProfileWrite['intent']): ProfileWrite {
  return {
    preferred_name: values.preferred_name.trim() || null, native_language: values.native_language.trim() || null,
    goals: [...values.goals, ...(values.custom_goal.trim() ? [values.custom_goal.trim()] : [])],
    interests: [...values.interests, ...(values.custom_interest.trim() ? [values.custom_interest.trim()] : [])],
    selected_cefr: values.selected_cefr === 'unknown' ? null : values.selected_cefr,
    sessions_per_week: values.sessions_per_week ? Number(values.sessions_per_week) : null,
    session_duration_minutes: values.session_duration_minutes ? Number(values.session_duration_minutes) : null,
    correction_mode: values.correction_mode, expected_version: version, intent,
  }
}

