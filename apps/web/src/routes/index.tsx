import { createRoute, createRootRoute } from '@tanstack/react-router'
import { AppLayout } from '../app/layout'
import { WelcomePage } from '../features/welcome/welcome-page'
import { AccountPage } from '../features/account/account-page'
import { CallbackPage } from '../auth/auth-status'

const rootRoute = createRootRoute({
  component: AppLayout,
  notFoundComponent: () => (
    <main id="main" className="mx-auto max-w-6xl px-10 py-20">
      <h1 className="font-display text-4xl">Page not found</h1>
      <a href="/" className="mt-5 inline-block underline">Return to Lingora</a>
    </main>
  ),
})

const indexRoute = createRoute({ getParentRoute: () => rootRoute, path: '/', component: WelcomePage })
const accountRoute = createRoute({ getParentRoute: () => rootRoute, path: '/app', component: AccountPage })
const callbackRoute = createRoute({ getParentRoute: () => rootRoute, path: '/auth/callback', component: CallbackPage })
export const routeTree = rootRoute.addChildren([indexRoute, accountRoute, callbackRoute])
