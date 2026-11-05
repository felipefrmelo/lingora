import type { ReactNode } from 'react'
import { SignInRequired } from '../../auth/context'
import { AuthMessage } from '../../auth/auth-status'
import { PrivateApiError } from '../../auth/private-api'
import { Button } from '../../components/ui/button'

export function Field({ id, label, error, children }: { id: string; label: string; error?: string; children: ReactNode }) {
  return <div className="space-y-2"><label className="field-label" htmlFor={id}>{label}</label>{children}{error && <p id={`${id}-error`} role="alert" className="field-error">{error}</p>}</div>
}

export function RequestFailure({ error, retry }: { error: unknown; retry?: () => void }) {
  if (error instanceof SignInRequired || (error instanceof PrivateApiError && error.status === 401)) return <AuthMessage code="interaction_required" />
  const conflict = error instanceof PrivateApiError && error.status === 409
  return <section role="alert" className="rounded-2xl border border-border bg-card p-6">
    <h2 className="font-display text-2xl">{conflict ? 'This record changed' : error instanceof PrivateApiError && error.status === 404 ? 'This record is no longer available' : 'We couldn’t complete that request'}</h2>
    <p className="mt-3 text-muted-foreground">{conflict ? 'Your unsaved input is still here. Reload the saved record before trying again.' : error instanceof PrivateApiError && error.status === 403 ? 'Your account does not have the required permission.' : error instanceof PrivateApiError && error.status === 410 ? 'This assessment was deleted. Review your records before starting a new entry.' : error instanceof PrivateApiError && error.status === 422 ? 'Check your entries and try again.' : error instanceof PrivateApiError && error.status === 404 ? 'This record could not be found in your account.' : 'Your changes have not been confirmed. Your input is still here; please try again.'}</p>
    {retry && <Button type="button" variant="outline" className="mt-5" onClick={retry}>{conflict ? 'Reload saved record' : 'Try again'}</Button>}
  </section>
}

