import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import ResumeUploader from '@/components/resume/ResumeUploader'
import ParsedResumeView from '@/components/resume/ParsedResumeView'
import JobDescriptionForm from '@/components/analysis/JobDescriptionForm'
import { runAnalysis } from '@/services/apiService'
import { loadUpload, saveResult, recordHistory, saveUpload } from '@/lib/persistence'
import type { ResumeUploadResponse, JobDescriptionRequest } from '@/types/api'
import { ChevronRight, ChevronLeft } from 'lucide-react'
import { cn } from '@/lib/utils'

// Wizard only needs 2 steps — Step 3 was unreachable dead UI, removed.
type Step = 1 | 2

export default function AnalysePage() {
  const navigate = useNavigate()
  // Restore the last upload from browser storage so a refresh
  // doesn't lose the parsed resume (no server-side database).
  const [restoredUpload] = useState<ResumeUploadResponse | null>(() => loadUpload())
  const [step, setStep] = useState<Step>(restoredUpload ? 2 : 1)
  const [upload, setUpload] = useState<ResumeUploadResponse | null>(restoredUpload)
  const [isAnalysing, setIsAnalysing] = useState(false)

  const handleUploaded = (data: ResumeUploadResponse) => {
    setUpload(data)
    saveUpload(data)
    // Auto-advance to step 2 once uploaded
    setTimeout(() => setStep(2), 600)
  }

  const handleAnalyse = async (jobReq: JobDescriptionRequest) => {
    if (!upload) return
    setIsAnalysing(true)
    try {
      // `parsed` makes the request stateless: the backend can
      // analyse without a server-side resume lookup (needed
      // on serverless hosting, where the store is ephemeral).
      const result = await runAnalysis({
        resume_id: upload.resume_id,
        job: jobReq,
        parsed: upload.parsed,
      })
      saveResult(result)
      recordHistory({
        analysis_id: result.analysis_id,
        resume_id: result.resume_id,
        job_title: result.job_title,
        company: result.company,
        overall_score: result.overall_score,
        created_at: new Date().toISOString(),
      })
      navigate(`/results/${result.analysis_id}`)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Analysis failed. Please try again.'
      toast.error(msg)
    } finally {
      setIsAnalysing(false)
    }
  }

  const steps = [
    { n: 1, label: 'Upload Resume' },
    { n: 2, label: 'Job Description & Analyse' },
  ]

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-10 animate-fade-in">
      {/* Page header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Analyse Your Resume</h1>
        <p className="text-sm text-gray-500 mt-1">
          Upload your resume and paste a job description to get your AI-powered match analysis.
        </p>
      </div>

      {/* Step indicator */}
      <div className="flex items-center gap-2 mb-10">
        {steps.map(({ n, label }, idx) => (
          <div key={n} className="flex items-center gap-2">
            <button
              onClick={() => n < step && setStep(n as Step)}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                step === n ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-500',
                n < step && 'cursor-pointer hover:bg-gray-200',
              )}
              disabled={n > step}
            >
              <span className={cn(
                'w-5 h-5 rounded-full text-xs font-bold flex items-center justify-center',
                step === n ? 'bg-white/20 text-white' : n < step ? 'bg-green-500 text-white' : 'bg-gray-300 text-gray-500',
              )}>
                {n < step ? '✓' : n}
              </span>
              <span className="hidden sm:block">{label}</span>
            </button>
            {idx < steps.length - 1 && (
              <ChevronRight className="w-4 h-4 text-gray-300" />
            )}
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-5 gap-8">
        {/* ── Main content ─────────────────────────────────────────────── */}
        <div className="lg:col-span-3">
          {step === 1 && (
            <div className="card animate-slide-up">
              <h2 className="font-semibold text-gray-800 mb-4">Step 1: Upload Your Resume</h2>
              <ResumeUploader onUploaded={handleUploaded} />
              {upload && (
                <div className="mt-4 flex justify-end">
                  <button onClick={() => setStep(2)} className="btn-primary flex items-center gap-2">
                    Continue <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              )}
            </div>
          )}

          {step === 2 && (
            <div className="card animate-slide-up">
              <div className="flex items-center justify-between mb-4">
                <h2 className="font-semibold text-gray-800">Step 2: Paste Job Description &amp; Analyse</h2>
                <button onClick={() => setStep(1)} className="btn-secondary text-sm py-1.5 flex items-center gap-1">
                  <ChevronLeft className="w-3.5 h-3.5" /> Back
                </button>
              </div>
              <JobDescriptionForm onSubmit={handleAnalyse} isLoading={isAnalysing} />
            </div>
          )}
        </div>

        {/* ── Sidebar: parsed resume preview ───────────────────────────── */}
        <div className="lg:col-span-2">
          {upload ? (
            <div>
              <h3 className="font-semibold text-gray-700 mb-3 text-sm uppercase tracking-wide">
                Resume Preview
              </h3>
              <ParsedResumeView parsed={upload.parsed} />
            </div>
          ) : (
            <div className="card text-center py-12 border-dashed text-gray-400">
              <p className="text-sm">Your parsed resume will appear here after upload.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
