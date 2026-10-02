import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import HistoryPage from '@/pages/HistoryPage'
import type { AnalysisHistoryResponse } from '@/types/api'

// Mock the API service — unit tests must not touch axios/network
vi.mock('@/services/apiService', () => ({
  listAnalyses: vi.fn(),
}))

import { listAnalyses } from '@/services/apiService'
const mockList = vi.mocked(listAnalyses)

function makeItem(i: number) {
  return {
    analysis_id: `id-${i}`,
    resume_id: `res-${i}`,
    job_title: `Backend Engineer #${i}`,
    company: 'TechCorp',
    overall_score: 60 + i,
    created_at: new Date(Date.UTC(2026, 0, i + 1)).toISOString(),
  }
}

function page(items: number[], total: number, offset: number): AnalysisHistoryResponse {
  return { items: items.map(makeItem), total, limit: 10, offset }
}

function renderPage() {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  })
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <HistoryPage />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  mockList.mockReset()
})

describe('HistoryPage pagination', () => {
  it('shows the empty state when there are no analyses', async () => {
    mockList.mockResolvedValue(page([], 0, 0))
    renderPage()
    expect(await screen.findByText('No analyses yet')).toBeInTheDocument()
    expect(mockList).toHaveBeenCalledWith(undefined, 10, 0)
  })

  it('renders items and hides pagination when everything fits on one page', async () => {
    mockList.mockResolvedValue(page([1, 2, 3], 3, 0))
    renderPage()
    expect(await screen.findByText('Backend Engineer #1')).toBeInTheDocument()
    expect(screen.queryByText(/Page 1 of/)).not.toBeInTheDocument()
  })

  it('paginates to the next page with a fresh offset', async () => {
    const user = userEvent.setup()
    const ids = Array.from({ length: 12 }, (_, i) => i + 1)
    mockList
      .mockResolvedValueOnce(page(ids.slice(0, 10), 12, 0)) // page 1
      .mockResolvedValueOnce(page(ids.slice(10), 12, 10)) // page 2

    renderPage()
    expect(await screen.findByText('Backend Engineer #1')).toBeInTheDocument()

    const next = screen.getByRole('button', { name: /next/i })
    expect(next).toBeEnabled()
    await user.click(next)

    await waitFor(() => {
      expect(mockList).toHaveBeenLastCalledWith(undefined, 10, 10)
    })
    expect(await screen.findByText('Backend Engineer #11')).toBeInTheDocument()
    // Page label reflects the new page
    expect(screen.getByText(/Page 2 of 2/)).toBeInTheDocument()
  })

  it('disables Previous on the first page', async () => {
    mockList.mockResolvedValue(page([1, 2], 12, 0))
    renderPage()
    await screen.findByText('Backend Engineer #1')
    expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled()
  })

  it('shows the error state when the API call fails', async () => {
    mockList.mockRejectedValue(new Error('boom'))
    renderPage()
    expect(await screen.findByText(/Failed to load history/)).toBeInTheDocument()
  })
})
