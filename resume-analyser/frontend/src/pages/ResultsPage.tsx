import { useParams, Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { getAnalysis } from '@/services/apiService'
import AnalysisResultView from '@/components/analysis/AnalysisResultView'
import { ArrowLeft, Download, Share2, Loader2, AlertCircle } from 'lucide-react'
import toast from 'react-hot-toast'

export default function ResultsPage() {
  const { analysisId } = useParams<{ analysisId: string }>()

  const { data, isLoading, isError, error } = useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: () => getAnalysis(analysisId!),
    enabled: !!analysisId,
    staleTime: Infinity,
  })

  const handleShare = () => {
    navigator.clipboard.writeText(window.location.href)
    // Warn the user that results persist across restarts now (SQLite backed),
    // but a direct URL share is only valid while this server session is live.
    toast.success(
      'Link copied! Results are stored in the database and will persist across restarts.',
      { duration: 4000, icon: '🔗' }
    )
  }

  const handlePrint = () => window.print()

  if (isLoading) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-gray-400">
          <Loader2 className="w-10 h-10 animate-spin" />
          <p className="text-sm">Loading analysis…</p>
        </div>
      </div>
    )
  }

  if (isError || !data) {
    return (
      <div className="min-h-[50vh] flex items-center justify-center">
        <div className="text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-red-400 mx-auto" />
          <h2 className="text-lg font-semibold text-gray-800">Analysis Not Found</h2>
          <p className="text-sm text-gray-500">{(error as Error)?.message ?? 'The analysis could not be loaded.'}</p>
          <Link to="/analyse" className="btn-primary inline-flex">Start New Analysis</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 flex-wrap gap-4">
        <div>
          <Link
            to="/analyse"
            className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 mb-2"
          >
            <ArrowLeft className="w-4 h-4" /> New Analysis
          </Link>
          <h1 className="text-2xl font-bold text-gray-900">Analysis Results</h1>
          <p className="text-sm text-gray-500 mt-1">
            {data.job_title}{data.company ? ` @ ${data.company}` : ''}
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleShare} className="btn-secondary flex items-center gap-2 text-sm">
            <Share2 className="w-4 h-4" /> Share
          </button>
          <button onClick={handlePrint} className="btn-secondary flex items-center gap-2 text-sm">
            <Download className="w-4 h-4" /> Export
          </button>
        </div>
      </div>

      <AnalysisResultView result={data} />

      {/* Bottom CTA */}
      <div className="mt-12 text-center">
        <Link to="/analyse" className="btn-primary px-10 py-3.5 text-base">
          Analyse Another Job
        </Link>
        <Link to="/history" className="btn-secondary ml-3 px-6 py-3.5 text-base">
          View History
        </Link>
      </div>
    </div>
  )
}
