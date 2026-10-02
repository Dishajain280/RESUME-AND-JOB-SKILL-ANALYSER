import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { listAnalyses } from '@/services/apiService'
import { Loader2, AlertCircle, FileText, ArrowRight, ChevronLeft, ChevronRight } from 'lucide-react'
import { scoreColor, scoreLabel, formatDate } from '@/lib/utils'

const PAGE_SIZE = 10

export default function HistoryPage() {
  const [offset, setOffset] = useState(0)

  const { data, isLoading, isError } = useQuery({
    queryKey: ['analysis-history', offset],
    queryFn: () => listAnalyses(undefined, PAGE_SIZE, offset),
    staleTime: 60_000,
    placeholderData: (prev) => prev, // keep the current page visible while loading the next
  })

  const total = data?.total ?? 0
  const items = data?.items ?? []
  const hasPrev = offset > 0
  const hasNext = offset + items.length < total
  const page = Math.floor(offset / PAGE_SIZE) + 1
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE))

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 animate-fade-in">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Analysis History</h1>
          <p className="text-sm text-gray-500 mt-1">
            All your past resume analyses — {total} total
          </p>
        </div>
        <Link to="/analyse" className="btn-primary flex items-center gap-2 text-sm">
          New Analysis
        </Link>
      </div>

      {isLoading && !data && (
        <div className="flex items-center justify-center py-20 text-gray-400">
          <Loader2 className="w-8 h-8 animate-spin mr-3" />
          <span className="text-sm">Loading history…</span>
        </div>
      )}

      {isError && (
        <div className="flex items-center gap-3 text-red-500 text-sm bg-red-50 rounded-xl p-4">
          <AlertCircle className="w-5 h-5 shrink-0" />
          Failed to load history. Make sure the backend is running.
        </div>
      )}

      {data && items.length === 0 && (
        <div className="card text-center py-20">
          <FileText className="w-12 h-12 text-gray-200 mx-auto mb-4" />
          <h3 className="font-semibold text-gray-600">No analyses yet</h3>
          <p className="text-sm text-gray-400 mt-2">Upload your resume to get started.</p>
          <Link to="/analyse" className="btn-primary inline-flex mt-6">
            Analyse My Resume
          </Link>
        </div>
      )}

      {items.length > 0 && (
        <>
          <div className="space-y-3">
            {items.map((item) => (
              <Link
                key={item.analysis_id}
                to={`/results/${item.analysis_id}`}
                className="card flex items-center gap-4 hover:shadow-md hover:border-brand-200 transition-all group"
              >
                {/* Score circle */}
                <div className={`w-14 h-14 rounded-2xl flex flex-col items-center justify-center shrink-0 font-bold ${
                  item.overall_score >= 80 ? 'bg-green-50' :
                  item.overall_score >= 60 ? 'bg-yellow-50' : 'bg-red-50'
                }`}>
                  <span className={`text-lg leading-none ${scoreColor(item.overall_score)}`}>
                    {Math.round(item.overall_score)}
                  </span>
                  <span className="text-[10px] text-gray-400">/ 100</span>
                </div>

                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-gray-800 truncate">
                    {item.job_title}
                    {item.company && <span className="font-normal text-gray-500"> @ {item.company}</span>}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {formatDate(item.created_at)}
                  </p>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <span className={`text-sm font-medium ${scoreColor(item.overall_score)}`}>
                    {scoreLabel(item.overall_score)}
                  </span>
                  <ArrowRight className="w-4 h-4 text-gray-300 group-hover:text-brand-500 transition-colors" />
                </div>
              </Link>
            ))}
          </div>

          {/* Pagination */}
          {pageCount > 1 && (
            <div className="mt-8 flex items-center justify-between">
              <button
                onClick={() => setOffset(Math.max(0, offset - PAGE_SIZE))}
                disabled={!hasPrev}
                className="flex items-center gap-1 text-sm font-medium text-gray-600 hover:text-brand-600 disabled:opacity-40 disabled:pointer-events-none"
              >
                <ChevronLeft className="w-4 h-4" /> Previous
              </button>
              <span className="text-sm text-gray-400">
                Page {page} of {pageCount}
              </span>
              <button
                onClick={() => setOffset(offset + PAGE_SIZE)}
                disabled={!hasNext}
                className="flex items-center gap-1 text-sm font-medium text-gray-600 hover:text-brand-600 disabled:opacity-40 disabled:pointer-events-none"
              >
                Next <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  )
}
