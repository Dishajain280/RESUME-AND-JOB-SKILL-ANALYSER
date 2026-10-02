import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, FileText, X, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'
import { uploadResume } from '@/services/apiService'
import type { ResumeUploadResponse } from '@/types/api'
import toast from 'react-hot-toast'

interface ResumeUploaderProps {
  onUploaded: (data: ResumeUploadResponse) => void
}

// No client-side type filter: browsers are inconsistent about
// reporting MIME types (often 'application/octet-stream'), which
// silently blocked genuine PDF/DOCX uploads. Every file is accepted
// here; the backend validates content via extension + magic-byte
// sniffing and returns a clear message for unsupported formats.
const SUPPORTED_HINT =
  'PDF, DOCX, TXT, RTF, ODT, HTML, Markdown, CSV, JPG, PNG & more · max 10 MB'

type UploadState = 'idle' | 'uploading' | 'success' | 'error'

export default function ResumeUploader({ onUploaded }: ResumeUploaderProps) {
  const [state, setState] = useState<UploadState>('idle')
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ResumeUploadResponse | null>(null)

  const onDrop = useCallback(async (accepted: File[]) => {
    const f = accepted[0]
    if (!f) return
    setFile(f)
    setError(null)
    setState('uploading')

    try {
      const data = await uploadResume(f)
      setResult(data)
      setState('success')
      toast.success(`Parsed ${data.parsed.skills.length} skills from your resume!`)
      onUploaded(data)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Upload failed'
      setError(msg)
      setState('error')
      toast.error(msg)
    }
  }, [onUploaded])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    // No `accept` filter: every file type is accepted client-side;
    // the backend validates content and reports unsupported formats
    // with a clear, user-safe message.
    maxFiles: 1,
    maxSize: 10 * 1024 * 1024,
    disabled: state === 'uploading',
    onDropRejected: (fileRejections) => {
      const msg = fileRejections[0]?.errors?.[0]?.message || 'File not accepted'
      setError(msg)
      setState('error')
      toast.error(msg)
    },
  })

  const reset = () => {
    setFile(null)
    setError(null)
    setResult(null)
    setState('idle')
  }

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          'relative rounded-2xl border-2 border-dashed transition-all cursor-pointer',
          'flex flex-col items-center justify-center gap-3 p-10 text-center',
          isDragActive && 'border-brand-400 bg-brand-50',
          state === 'idle' && !isDragActive && 'border-gray-200 hover:border-brand-300 hover:bg-gray-50',
          state === 'uploading' && 'border-brand-300 bg-brand-50 cursor-not-allowed',
          state === 'success' && 'border-green-300 bg-green-50',
          state === 'error' && 'border-red-300 bg-red-50',
        )}
      >
        <input {...getInputProps()} />

        {state === 'uploading' && (
          <>
            <Loader2 className="w-10 h-10 text-brand-500 animate-spin" />
            <p className="text-sm text-brand-700 font-medium">Parsing your resume…</p>
          </>
        )}

        {state === 'success' && result && (
          <>
            <CheckCircle2 className="w-10 h-10 text-green-500" />
            <div>
              <p className="font-semibold text-green-800">{result.filename}</p>
              <p className="text-xs text-green-700 mt-1">
                {result.word_count} words · {result.page_count} page(s) · {result.parsed.skills.length} skills detected
              </p>
            </div>
            <button
              onClick={(e) => { e.stopPropagation(); reset() }}
              className="absolute top-3 right-3 p-1 rounded-full hover:bg-green-100"
            >
              <X className="w-4 h-4 text-green-600" />
            </button>
          </>
        )}

        {state === 'error' && (
          <>
            <AlertCircle className="w-10 h-10 text-red-500" />
            <p className="text-sm text-red-700 font-medium">{error}</p>
            <button
              onClick={(e) => { e.stopPropagation(); reset() }}
              className="text-xs text-red-600 underline"
            >
              Try again
            </button>
          </>
        )}

        {state === 'idle' && (
          <>
            <div className="w-14 h-14 rounded-2xl bg-brand-100 flex items-center justify-center">
              <Upload className="w-7 h-7 text-brand-600" />
            </div>
            <div>
              <p className="font-semibold text-gray-800">
                {isDragActive ? 'Drop your resume here' : 'Drag & drop your resume'}
              </p>
              <p className="text-sm text-gray-500 mt-1">{SUPPORTED_HINT}</p>
            </div>
            <span className="btn-secondary text-sm py-2 pointer-events-none">
              Browse file
            </span>
          </>
        )}
      </div>

      {/* File info chip */}
      {file && state !== 'idle' && state !== 'error' && (
        <div className="flex items-center gap-2 text-sm text-gray-600 bg-gray-50 rounded-xl px-4 py-2">
          <FileText className="w-4 h-4 text-gray-400" />
          <span className="truncate">{file.name}</span>
          <span className="ml-auto text-gray-400 text-xs">
            {(file.size / 1024).toFixed(0)} KB
          </span>
        </div>
      )}
    </div>
  )
}
