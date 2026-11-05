import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { RouterProvider } from '@tanstack/react-router'
import { router } from './app/router'
import { AuthProvider } from './auth/provider'
import { readAuthConfig } from './auth/config'
import './styles.css'

const queryClient = new QueryClient()
const root = document.getElementById('root')
const authConfig = readAuthConfig(import.meta.env, window.location.origin)
if (!root) throw new Error('Application root is missing')

createRoot(root).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider config={authConfig} onRedirect={() => {
        window.history.replaceState(null, '', '/app')
        void router.navigate({ to: '/app', replace: true })
      }}>
        <RouterProvider router={router} />
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>,
)
