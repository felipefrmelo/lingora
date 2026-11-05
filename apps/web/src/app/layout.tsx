import { Link, Outlet } from '@tanstack/react-router'
import { Sprout } from 'lucide-react'

export function AppLayout() {
  return (
    <>
      <a href="#main" className="sr-only z-50 rounded bg-primary p-3 text-primary-foreground focus:not-sr-only focus:absolute focus:left-4 focus:top-4">Skip to content</a>
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-7 sm:px-10">
        <Link to="/" aria-label="Lingora home" className="flex items-center gap-2.5 text-xl font-bold tracking-tight">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-primary text-primary-foreground"><Sprout size={22} aria-hidden="true" /></span>
          lingora<span className="-ml-2 text-primary">.</span>
        </Link>
        <span className="text-xs font-medium tracking-wide text-muted-foreground">A world of words awaits.</span>
      </header>
      <Outlet />
    </>
  )
}
