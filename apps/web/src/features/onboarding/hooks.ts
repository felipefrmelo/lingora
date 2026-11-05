import { useQuery } from '@tanstack/react-query'
import { useBlocker } from '@tanstack/react-router'
import { useCallback, useRef } from 'react'
import { useAuth } from '../../auth/context'
import { privateKey } from '../../auth/private-api'
import { createLearningApi } from './api'

export function useLearningApi() {
  const auth = useAuth()
  return createLearningApi(auth.getAccessToken, auth.subject || '')
}

export function useProfile() {
  const auth = useAuth()
  const api = useLearningApi()
  return useQuery({ queryKey: privateKey(auth.subject, 'profile'), queryFn: ({ signal }) => api.profile(signal), retry: false })
}

export function useUnsavedChanges(dirty: boolean) {
  const allowNavigation = useRef(false)
  useBlocker({
    shouldBlockFn: () => dirty && !allowNavigation.current && !window.confirm('Discard your unsaved changes?'),
    enableBeforeUnload: () => dirty && !allowNavigation.current,
  })
  return useCallback(() => { allowNavigation.current = true }, [])
}

