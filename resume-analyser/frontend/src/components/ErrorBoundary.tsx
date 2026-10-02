import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}

interface State {
  error: Error | null
}

/**
 * Catches rendering/lifecycle errors anywhere below it and shows a recovery
 * screen instead of a blank page. Reload clears transient state; the error
 * details help when users report issues.
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Hook for Sentry or another reporter in production
    console.error('Unhandled UI error:', error, errorInfo.componentStack)
  }

  render() {
    const { error } = this.state
    if (error) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50 px-4">
          <div className="max-w-md w-full card p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-red-50 flex items-center justify-center mx-auto mb-4">
              <svg
                className="w-7 h-7 text-red-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={2}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M12 9v2m0 4h.01M10.29 3.86l-8.02 14A2 2 0 004 21h16a2 2 0 001.73-3.13l-8-14a2 2 0 00-3.44 0z"
                />
              </svg>
            </div>
            <h1 className="text-lg font-bold text-gray-900">Something went wrong</h1>
            <p className="text-sm text-gray-500 mt-2">
              An unexpected error occurred while rendering the page. Reloading usually fixes it.
            </p>
            {import.meta.env.DEV && (
              <pre className="mt-4 text-xs text-left bg-gray-50 rounded-lg p-3 overflow-auto max-h-40 text-red-600 whitespace-pre-wrap">
                {error.message}
              </pre>
            )}
            <button onClick={() => window.location.reload()} className="btn-primary mt-6">
              Reload page
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
