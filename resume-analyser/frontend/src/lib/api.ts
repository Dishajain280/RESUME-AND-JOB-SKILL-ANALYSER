import axios from 'axios'

// User-facing generic message shown when the server error is not safe to display
const GENERIC_ERROR = 'Something went wrong. Please try again.'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30_000,
  headers: { 'Content-Type': 'application/json' },
})

// Response interceptor — surface safe error messages from FastAPI, hide internals
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status: number | undefined = err?.response?.status
    const detail = err?.response?.data?.detail

    // FastAPI validation errors are arrays — stringify them safely
    if (Array.isArray(detail)) {
      err.message = detail.map((d: { msg?: string }) => d.msg ?? String(d)).join('; ')
      return Promise.reject(err)
    }

    // 4xx errors have safe, user-intended messages (e.g. "File too large", "Not found")
    if (typeof detail === 'string' && status && status >= 400 && status < 500) {
      err.message = detail
      return Promise.reject(err)
    }

    // 5xx or unknown — never expose raw server internals to the UI
    if (status && status >= 500) {
      err.message = GENERIC_ERROR
      return Promise.reject(err)
    }

    // Network / timeout errors
    if (!err.response) {
      err.message = 'Network error — make sure the server is running.'
      return Promise.reject(err)
    }

    err.message = GENERIC_ERROR
    return Promise.reject(err)
  },
)

export default api
