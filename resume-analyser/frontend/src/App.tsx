import { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from '@/components/layout/Layout'
import RouteFallback from '@/components/RouteFallback'

// Route-level code splitting: each page ships as its own chunk, so the
// initial bundle only pays for the home page.
const HomePage = lazy(() => import('@/pages/HomePage'))
const AnalysePage = lazy(() => import('@/pages/AnalysePage'))
const ResultsPage = lazy(() => import('@/pages/ResultsPage'))
const HistoryPage = lazy(() => import('@/pages/HistoryPage'))
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

export default function App() {
  return (
    <Suspense fallback={<RouteFallback />}>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="analyse" element={<AnalysePage />} />
          <Route path="results/:analysisId" element={<ResultsPage />} />
          <Route path="history" element={<HistoryPage />} />
          <Route path="404" element={<NotFoundPage />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Route>
      </Routes>
    </Suspense>
  )
}
