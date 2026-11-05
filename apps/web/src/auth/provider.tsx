import { Auth0Provider, useAuth0 } from '@auth0/auth0-react'
import { useQueryClient } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import type { AuthConfig } from './config'
import { AuthContext, SignInRequired, classifyAuthError, type AuthErrorCode, type AuthState } from './context'
import { cancelPrivateRequests } from './private-api'

const unavailable: AuthState = {
  configured: false,
  isLoading: false,
  isAuthenticated: false,
  error: null,
  login: async () => { throw new SignInRequired() },
  logout: async () => {},
  getAccessToken: async () => { throw new SignInRequired() },
}

export function AuthProvider({ config, onRedirect, children }: {
  config: AuthConfig | null
  onRedirect: () => void
  children: ReactNode
}) {
  if (!config) return <AuthContext.Provider value={unavailable}>{children}</AuthContext.Provider>
  return (
    <Auth0Provider
      domain={config.domain}
      clientId={config.clientId}
      authorizationParams={{
        audience: config.audience,
        redirect_uri: config.redirectUri,
        scope: 'openid profile email profile:read profile:write',
      }}
      cacheLocation="memory"
      useRefreshTokens={false}
      createAnonymousSessionOnFailedSilentAuth={false}
      onRedirectCallback={onRedirect}
    >
      <SdkBridge>{children}</SdkBridge>
    </Auth0Provider>
  )
}

function SdkBridge({ children }: { children: ReactNode }) {
  const sdk = useAuth0()
  const queryClient = useQueryClient()
  const [operationError, setOperationError] = useState<AuthErrorCode | null>(null)
  const subject = sdk.user?.sub
  const previousSubject = useRef(subject)

  useEffect(() => {
    if (previousSubject.current && previousSubject.current !== subject) {
      cancelPrivateRequests(previousSubject.current)
      queryClient.getMutationCache().clear()
    }
    previousSubject.current = subject
    queryClient.removeQueries({
      predicate: (query) => query.queryKey[0] === 'private' && query.queryKey[1] !== subject,
    })
  }, [queryClient, subject])

  useEffect(() => {
    if (sdk.error && window.location.pathname === '/auth/callback') {
      window.history.replaceState(null, '', '/auth/callback')
    }
  }, [sdk.error])

  const login = useCallback(async (signup = false) => {
    setOperationError(null)
    try {
      await sdk.loginWithRedirect({ authorizationParams: signup ? { screen_hint: 'signup' } : {} })
    } catch (error) {
      setOperationError(classifyAuthError(error))
    }
  }, [sdk])

  const logout = useCallback(async () => {
    cancelPrivateRequests()
    queryClient.removeQueries({ queryKey: ['private'] })
    queryClient.getMutationCache().clear()
    setOperationError(null)
    try {
      await sdk.logout({ logoutParams: { returnTo: window.location.origin } })
    } catch (error) {
      setOperationError(classifyAuthError(error))
    }
  }, [sdk, queryClient])

  const getAccessToken = useCallback(async (force = false) => {
    try {
      const token = await sdk.getAccessTokenSilently({ cacheMode: force ? 'off' : 'on' })
      if (!token) throw new SignInRequired()
      return token
    } catch (error) {
      if (classifyAuthError(error) === 'interaction_required') throw new SignInRequired()
      throw error
    }
  }, [sdk])

  const value = useMemo<AuthState>(() => ({
    configured: true,
    isLoading: sdk.isLoading,
    isAuthenticated: sdk.isAuthenticated,
    subject,
    name: sdk.user?.name,
    email: sdk.user?.email,
    error: operationError || (sdk.error ? classifyAuthError(sdk.error) : null),
    login,
    logout,
    getAccessToken,
  }), [sdk.isLoading, sdk.isAuthenticated, sdk.user, sdk.error, subject, operationError, login, logout, getAccessToken])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
