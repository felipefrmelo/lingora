import { Link, Navigate } from '@tanstack/react-router'
import { Button } from '../components/ui/button'
import { useAuth, type AuthErrorCode } from './context'

export function AuthMessage({ code }: { code?: AuthErrorCode | null }) {
  const auth = useAuth()
  const verification = code === 'verification_required'
  return (
    <section className="mx-auto max-w-lg rounded-3xl border border-border bg-card p-8" aria-labelledby="auth-title">
      <h1 id="auth-title" className="font-display text-3xl">{
        verification ? 'Check your email' : code === 'interaction_required' ? 'Sign in again to continue' : !auth.configured ? 'Sign-in is temporarily unavailable' : code ? 'We couldn’t complete sign-in' : 'Your learning space is private'
      }</h1>
      <p className="mt-4 leading-relaxed text-muted-foreground">{
        verification
          ? 'Open the verification link sent to your email, then sign in again. If the link has expired, contact the administrator for a new verification email.'
          : code === 'access_denied'
            ? 'Access was not granted. You can try signing in again or return home.'
            : code
              ? 'Please try again. Your private account information has not been displayed.'
              : 'Sign in to access your personal Lingora account.'
      }</p>
      <div className="mt-6 flex items-center gap-4">
        {auth.configured && <Button onClick={() => void auth.login()}>{verification ? 'I verified my email — sign in' : 'Sign in'}</Button>}
        <Link to="/" className="text-sm underline">Return home</Link>
      </div>
    </section>
  )
}

export function CallbackPage() {
  const auth = useAuth()
  if (!auth.isLoading && !auth.error && auth.isAuthenticated) return <Navigate to="/app" replace />
  return (
    <main id="main" className="px-6 py-16">
      {auth.isLoading ? <p role="status" className="text-center">Completing sign-in…</p> : <AuthMessage code={auth.error || 'unavailable'} />}
    </main>
  )
}
