import { useQuery } from '@tanstack/react-query'
import { ArrowUpRight, BookOpen, Check, Globe2, LoaderCircle, MessageCircle, RotateCw } from 'lucide-react'
import { Button } from '../../components/ui/button'
import { getHealth } from '../../lib/api'

export function WelcomePage() {
  const health = useQuery({ queryKey: ['health'], queryFn: getHealth, retry: false })
  const connected = health.isSuccess && health.data.status === 'ok'

  return (
    <main id="main" className="mx-auto max-w-6xl px-6 pb-16 pt-12 sm:px-10 sm:pt-20">
      <div className="grid items-center gap-14 lg:grid-cols-[1.12fr_1fr] lg:gap-20">
        <section aria-labelledby="welcome-title">
          <p className="mb-7 flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
            <span className="h-1.5 w-1.5 rounded-full bg-primary" /> A little curiosity goes a long way
          </p>
          <h1 id="welcome-title" className="font-display text-[clamp(3.5rem,7vw,6rem)] leading-[1.04] tracking-[-0.05em]">
            Your world.<br />
            <span className="text-primary">In English.</span>
          </h1>
          <p className="mt-7 max-w-md text-lg leading-relaxed text-muted-foreground">
            Turn the things you care about into opportunities to learn. A personal space for
            meaningful lessons, curious conversations, and steady progress.
          </p>
          <div className="mt-9 flex items-center gap-3 text-sm font-medium">
            <span className="flex h-9 w-9 items-center justify-center rounded-full border border-border bg-white/60">
              <Globe2 size={18} aria-hidden="true" />
            </span>
            A new way to practice is taking shape.
          </div>
        </section>

        <section aria-labelledby="preview-title" className="relative">
          <div aria-hidden="true" className="absolute -right-4 -top-4 h-24 w-24 rounded-full border border-primary/15 sm:-right-7 sm:-top-7 sm:h-36 sm:w-36" />
          <div className="relative rounded-[2rem] border border-border bg-card p-7 shadow-[0_16px_60px_-32px_#233c2e50] sm:p-9">
            <div className="mb-9 flex items-center justify-between">
              <span className="text-xs font-semibold uppercase tracking-[0.16em] text-muted-foreground">A fresh start</span>
              <span className="rounded-full bg-muted px-3 py-1 text-xs font-medium text-primary">Early preview</span>
            </div>
            <h2 id="preview-title" className="font-display text-3xl leading-tight tracking-tight">Follow your curiosity.<br />Find your words.</h2>
            <div className="my-8 space-y-6">
              <Feature icon={<BookOpen size={21} aria-hidden="true" />} title="Read what interests you" description="English practice inspired by news and ideas from your world." />
              <Feature icon={<MessageCircle size={21} aria-hidden="true" />} title="Make room for conversation" description="Build confidence through practice that meets you where you are." />
            </div>
            <div className="border-t border-border pt-6">
              <div role="status" aria-live="polite" className="flex items-center gap-2 text-sm">
                {health.isPending || health.isFetching ? (
                  <><LoaderCircle size={16} className="animate-spin text-primary" aria-hidden="true" /> Checking connection…</>
                ) : connected ? (
                  <><Check size={16} className="text-primary" aria-hidden="true" /> Connection ready</>
                ) : (
                  <span className="text-destructive">We couldn’t connect. Please try again.</span>
                )}
              </div>
              <p className="mt-3 text-sm leading-relaxed text-muted-foreground">Sign in to explore news briefs and practise with lessons. Connected ChatGPT conversation is coming next.</p>
              <Button variant="outline" size="sm" className="mt-5" onClick={() => void health.refetch()} disabled={health.isFetching}>
                <RotateCw size={14} aria-hidden="true" />
                {health.isError ? 'Try again' : 'Check connection'}
              </Button>
            </div>
          </div>
        </section>
      </div>
      <div className="mt-16 flex items-center justify-between border-t border-border pt-7 text-xs text-muted-foreground sm:mt-24">
        <p>Small discoveries. Lasting progress.</p>
        <ArrowUpRight size={18} aria-hidden="true" />
      </div>
    </main>
  )
}

function Feature({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="flex gap-4">
      <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-muted text-primary">{icon}</span>
      <div>
        <h3 className="text-sm font-semibold">{title}</h3>
        <p className="mt-1 text-sm leading-relaxed text-muted-foreground">{description}</p>
      </div>
    </div>
  )
}
