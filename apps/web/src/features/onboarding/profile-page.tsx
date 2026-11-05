import { Navigate } from '@tanstack/react-router'
import { ProfileForm } from './profile-form'
import { RequestFailure } from './shared'
import { useProfile } from './hooks'

export function ProfilePage({ wizard = false }: { wizard?: boolean }) {
  const profile = useProfile()
  if (profile.isPending) return <p role="status">Loading your learning profile…</p>
  if (profile.isError) return <RequestFailure error={profile.error} retry={() => void profile.refetch()} />
  if (wizard && profile.data.onboarding_status === 'completed') return <Navigate to="/app" replace />
  return <ProfileForm profile={profile.data} wizard={wizard} />
}
