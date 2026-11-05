import { lazy } from 'react'
import { AccountBoundary } from '../account/account-page'
const Catalog = lazy(() => import('./catalog-page').then(module => ({ default: module.CatalogPage })))
const Job = lazy(() => import('./job-page').then(module => ({ default: module.JobPage })))
const Lesson = lazy(() => import('./lesson-page').then(module => ({ default: module.LessonPage })))
export function LearningPage() { return <AccountBoundary><Catalog /></AccountBoundary> }
export function PreparationPage({ jobId }: { jobId: string }) { return <AccountBoundary><Job key={jobId} jobId={jobId} /></AccountBoundary> }
export function PracticePage({ lessonId }: { lessonId: string }) { return <AccountBoundary><Lesson lessonId={lessonId} /></AccountBoundary> }
