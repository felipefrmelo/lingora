import { Link } from '@tanstack/react-router'
import { Button } from '../components/ui/button'
import { useAuth } from './context'

export function AuthControls() {
  const auth = useAuth()
  if (auth.isLoading) return <span className="text-sm text-muted-foreground">Checking sign-in…</span>
  if (!auth.configured) return <span className="text-xs text-muted-foreground">Sign-in is temporarily unavailable</span>
  if (auth.isAuthenticated) {
    return (
      <nav aria-label="Account" className="flex items-center gap-3">
        <Link to="/app" className="text-sm font-medium">My account</Link>
        <Button variant="outline" size="sm" onClick={() => void auth.logout()}>Sign out</Button>
      </nav>
    )
  }
  return (
    <nav aria-label="Sign in" className="flex items-center gap-2">
      <Button variant="outline" size="sm" onClick={() => void auth.login()}>Sign in</Button>
      <Button size="sm" onClick={() => void auth.login(true)}>Create account</Button>
    </nav>
  )
}
