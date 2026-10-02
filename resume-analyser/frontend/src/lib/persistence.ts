import type {
  AnalysisListItem,
  AnalysisResult,
  ResumeUploadResponse,
} from '@/types/api'

// The deployment runs without a database: the backend's store is
// ephemeral on serverless hosting. To keep uploaded resumes and
// analysis results alive across page refreshes, the frontend
// mirrors them into localStorage (per browser, private by design).
//
// All access is wrapped in try/catch: storage can be unavailable
// (private browsing) or full — persistence is best-effort and the
// app keeps working when it fails.

const KEY_UPLOAD = 'ra:lastUpload'
const KEY_RESULTS = 'ra:results'
const KEY_HISTORY = 'ra:history'
const HISTORY_LIMIT = 50

function read<T>(key: string): T | null {
  try {
    const raw = window.localStorage.getItem(key)
    return raw ? (JSON.parse(raw) as T) : null
  } catch {
    return null
  }
}

function write(key: string, value: unknown): void {
  try {
    window.localStorage.setItem(key, JSON.stringify(value))
  } catch {
    // storage unavailable / quota exceeded — non-fatal
  }
}

// ── Last upload (restores the analyse wizard after refresh) ────────

export function saveUpload(resp: ResumeUploadResponse): void {
  write(KEY_UPLOAD, resp)
}

export function loadUpload(): ResumeUploadResponse | null {
  return read<ResumeUploadResponse>(KEY_UPLOAD)
}

// ── Analysis results (keyed by analysis_id) ────────────────────────

export function saveResult(result: AnalysisResult): void {
  const all = read<Record<string, AnalysisResult>>(KEY_RESULTS) ?? {}
  all[result.analysis_id] = result
  // Cap: keep the most recent HISTORY_LIMIT results.
  const ids = Object.keys(all)
  if (ids.length > HISTORY_LIMIT) {
    for (const id of ids.slice(0, ids.length - HISTORY_LIMIT)) {
      delete all[id]
    }
  }
  write(KEY_RESULTS, all)
}

export function loadResult(id: string): AnalysisResult | null {
  return read<Record<string, AnalysisResult>>(KEY_RESULTS)?.[id] ?? null
}

// ── History list ───────────────────────────────────────────────────

export function recordHistory(item: AnalysisListItem): void {
  const list = read<AnalysisListItem[]>(KEY_HISTORY) ?? []
  const next = [
    item,
    ...list.filter((i) => i.analysis_id !== item.analysis_id),
  ].slice(0, HISTORY_LIMIT)
  write(KEY_HISTORY, next)
}

export function loadHistory(): AnalysisListItem[] {
  return read<AnalysisListItem[]>(KEY_HISTORY) ?? []
}
