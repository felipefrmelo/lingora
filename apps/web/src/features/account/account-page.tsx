import { useQuery } from '@tanstack/react-query'
import { useAuth, SignInRequired } from '../../auth/context'
import { AuthMessage } from '../../auth/auth-status'
import { Button } from '../../components/ui/button'
import { AccountApiError, createAccountApi } from './api'

export function AccountPage() {
  const auth = useAuth()
  const account = useQuery({
    queryKey: ['account', auth.subject],
    enabled: auth.isAuthenticated && Boolean(auth.subject) && !auth.error,
    queryFn: async ({ signal }) => {
      const api = createAccountApi(auth.getAccessToken)
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
    <main id="main" className="mx-auto max-w-3xl px-6 py-16 sm:px-10">
      {account.isPending ? <p role="status">Preparing your account…</p> : account.isError ? (
        <section role="alert" className="rounded-3xl border border-border bg-card p-8">
          <h1 className="font-display text-3xl">We couldn’t open your account</h1>
          <p className="mt-4 text-muted-foreground">{account.error instanceof AccountApiError && account.error.status === 403
            ? 'Your account does not have the required permission. Please contact the administrator.'
            : 'Your sign-in is still active. Please try again shortly.'}</p>
          <Button className="mt-6" variant="outline" onClick={() => void account.refetch()}>Try again</Button>
        </section>
      ) : (
        <section className="rounded-3xl border border-border bg-card p-8 sm:p-12" aria-labelledby="account-title">
          <p className="text-xs font-semibold uppercase tracking-widest text-primary">Your Lingora account</p>
          <h1 id="account-title" className="mt-5 font-display text-4xl">Welcome{auth.name ? `, ${auth.name}` : ''}.</h1>
          <p className="mt-5 text-muted-foreground">Your personal learning space starts here.</p>
          {auth.email && <p className="mt-7 break-all text-sm">Signed in as {auth.email}</p>}
          <p className="mt-3 text-sm text-muted-foreground">Account created {new Intl.DateTimeFormat('en', { dateStyle: 'medium' }).format(new Date(account.data.created_at))}</p>
          <Button className="mt-8" variant="outline" onClick={() => void auth.logout()}>Sign out of Lingora</Button>
        </section>
      )}
    </main>
  )
}
