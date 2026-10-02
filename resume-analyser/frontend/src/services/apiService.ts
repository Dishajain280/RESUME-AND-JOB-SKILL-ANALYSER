import api from '@/lib/api'
import type {
  ResumeUploadResponse,
  AnalyseRequest,
  AnalysisResult,
  JobDescriptionRequest,
  JobRoleTemplate,
} from '@/types/api'

// ── Resume ─────────────────────────────────────────────────────────────────

export async function uploadResume(file: File): Promise<ResumeUploadResponse> {
  const form = new FormData()
  form.append('file', file, file.name)
  form.append('files', file, file.name)

  // Some browsers / proxies / SDKs submit a pluralized field name; we send both
  // so FastAPI doesn't reject the request with 422 "field required".
  //
  // The axios instance sets a global Content-Type: application/json. With a
  // FormData body that header makes axios stringify the FormData to JSON
  // (formDataToJSON), silently dropping the file and causing a 422 on the
  // backend. Override the header with multipart/form-data AND use the fetch
  // adapter: it deletes a boundary-less multipart header so the browser can
  // set the full multipart/form-data; boundary=… value itself.
  const { data } = await api.post<ResumeUploadResponse>('/resume/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    adapter: 'fetch',
  })
  return data
}

// ── Analysis ───────────────────────────────────────────────────────────────

export async function runAnalysis(req: AnalyseRequest): Promise<AnalysisResult> {
  const { data } = await api.post<AnalysisResult>('/analysis/', req)
  return data
}

// ── Jobs ───────────────────────────────────────────────────────────────────

export async function parseJob(req: JobDescriptionRequest) {
  const { data } = await api.post('/jobs/parse', req)
  return data
}

export async function getJobTemplates(): Promise<JobRoleTemplate[]> {
  const { data } = await api.get<JobRoleTemplate[]>('/jobs/templates')
  return data
}
