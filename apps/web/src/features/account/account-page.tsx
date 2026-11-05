import { useQuery } from '@tanstack/react-query'
import { Fragment, lazy, Suspense, type ReactNode } from 'react'
import { useAuth, SignInRequired } from '../../auth/context'
import { AuthMessage } from '../../auth/auth-status'
import { Button } from '../../components/ui/button'
import { AccountApiError, createAccountApi } from './api'
import { privateKey } from '../../auth/private-api'
const ProfileOverview = lazy(() => import('../onboarding/overview').then(module => ({ default: module.ProfileOverview })))
const ProfilePage = lazy(() => import('../onboarding/profile-page').then(module => ({ default: module.ProfilePage })))

export function AccountPage() {
  return <AccountBoundary><ProfileOverview /></AccountBoundary>
}

export function LearningProfilePage({ wizard = false }: { wizard?: boolean }) {
  return <AccountBoundary><ProfilePage wizard={wizard} /></AccountBoundary>
}

export function AccountBoundary({ children }: { children: ReactNode }) {
  const auth = useAuth()
  const account = useQuery({
    queryKey: privateKey(auth.subject, 'account'),
    enabled: auth.isAuthenticated && Boolean(auth.subject) && !auth.error,
    queryFn: async ({ signal }) => {
      const api = createAccountApi(auth.getAccessToken, auth.subject)
      await api.bootstrap(signal)
      return api.current(signal)
    },
    retry: false,
    staleTime: 60_000,
  })

  if (auth.isLoading) return <main id="main" className="px-6 py-16"><p role="status" className="text-center">Checking sign-in…</p></main>
  if (!auth.isAuthenticated || auth.error || !auth.subject) {
    return <main id="main" className="px-6 py-16"><AuthMessage code={auth.error} /></main>
  }
  if (account.error instanceof SignInRequired || (account.error instanceof AccountApiError && account.error.status === 401)) {
    return <main id="main" className="px-6 py-16"><AuthMessage code="interaction_required" /></main>
  }

  return (
    <main id="main" className="mx-auto max-w-4xl px-6 py-12 sm:px-10 sm:py-16">
      {account.isPending ? <p role="status">Preparing your account…</p> : account.isError ? (
        <section role="alert" className="rounded-3xl border border-border bg-card p-8">
          <h1 className="font-display text-3xl">We couldn’t open your account</h1>
          <p className="mt-4 text-muted-foreground">{account.error instanceof AccountApiError && account.error.status === 403
            ? 'Your account does not have the required permission. Please contact the administrator.'
            : 'Your sign-in is still active. Please try again shortly.'}</p>
          <Button className="mt-6" variant="outline" onClick={() => void account.refetch()}>Try again</Button>
        </section>
      ) : (
        <Fragment key={auth.subject}><Suspense fallback={<p role="status">Loading your learning space…</p>}>{children}</Suspense></Fragment>
      )}
    </main>
  )
}
