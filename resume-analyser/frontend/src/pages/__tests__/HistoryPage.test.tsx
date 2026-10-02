import { describe, it, expect, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter } from 'react-router-dom'
import HistoryPage from '@/pages/HistoryPage'
import { recordHistory } from '@/lib/persistence'

// HistoryPage is fully localStorage-driven — unit tests seed the
// browser store via the same persistence module the app uses.

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

/** Seed the browser history with items 1..n, displayed in order. */
function seedHistory(n: number) {
  // recordHistory prepends, so seed in reverse to end up ordered.
  for (let i = n; i >= 1; i--) recordHistory(makeItem(i))
}

function renderPage() {
  return render(
    <MemoryRouter>
      <HistoryPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  localStorage.clear()
})

describe('HistoryPage', () => {
  it('shows the empty state when there are no analyses', () => {
    renderPage()
    expect(screen.getByText('No analyses yet')).toBeInTheDocument()
  })

  it('renders items and hides pagination when everything fits on one page', () => {
    seedHistory(3)
    renderPage()
    expect(screen.getByText('Backend Engineer #1')).toBeInTheDocument()
    expect(screen.getByText('Backend Engineer #3')).toBeInTheDocument()
    expect(screen.queryByText(/Page 1 of/)).not.toBeInTheDocument()
  })

  it('paginates to the next page with a fresh offset', async () => {
    const user = userEvent.setup()
    seedHistory(12)
    renderPage()
    expect(screen.getByText('Backend Engineer #1')).toBeInTheDocument()
    expect(screen.queryByText('Backend Engineer #11')).not.toBeInTheDocument()

    const next = screen.getByRole('button', { name: /next/i })
    expect(next).toBeEnabled()
    await user.click(next)

    expect(await screen.findByText('Backend Engineer #11')).toBeInTheDocument()
    // Page label reflects the new page
    expect(screen.getByText(/Page 2 of 2/)).toBeInTheDocument()
    // Page-1 items are no longer rendered
    expect(screen.queryByText('Backend Engineer #1')).not.toBeInTheDocument()
  })

  it('disables Previous on the first page', () => {
    seedHistory(12)
    renderPage()
    expect(screen.getByRole('button', { name: /previous/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /next/i })).toBeEnabled()
  })

  it('returns to the first page via Previous', async () => {
    const user = userEvent.setup()
    seedHistory(12)
    renderPage()
    await user.click(screen.getByRole('button', { name: /next/i }))
    expect(screen.getByText(/Page 2 of 2/)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: /previous/i }))
    expect(screen.getByText('Backend Engineer #1')).toBeInTheDocument()
    expect(screen.getByText(/Page 1 of 2/)).toBeInTheDocument()
  })
})
