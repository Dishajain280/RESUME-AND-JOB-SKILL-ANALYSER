import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import JobDescriptionForm from '@/components/analysis/JobDescriptionForm'
import type { JobRoleTemplate } from '@/types/api'

vi.mock('@/services/apiService', () => ({
  getJobTemplates: vi.fn(),
}))

import { getJobTemplates } from '@/services/apiService'
const mockTemplates = vi.mocked(getJobTemplates)

const TEMPLATES: JobRoleTemplate[] = [
  {
    id: 'senior-backend-engineer',
    title: 'Senior Backend Engineer',
    category: 'Engineering',
    experience_level: 'senior',
    description:
      'We are looking for a Senior Backend Engineer with 5+ years of experience.\n\n' +
      'Required skills: Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, REST API.\n' +
      'Preferred: Terraform, Redis, GraphQL.\n\nResponsibilities:\n• Design scalable systems\n• Lead reviews',
  },
  {
    id: 'data-scientist',
    title: 'Data Scientist',
    category: 'Data & AI',
    experience_level: 'mid',
    description:
      'We are looking for a Data Scientist with 3+ years of experience.\n\n' +
      'Required skills: Python, SQL, Machine Learning, Pandas, statistics.\n' +
      'Preferred: PyTorch, Spark, A/B testing.\n\nResponsibilities:\n• Build ML models\n• Analyse datasets',
  },
]

function renderForm(onSubmit = vi.fn()) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } })
  return render(
    <QueryClientProvider client={qc}>
      <JobDescriptionForm onSubmit={onSubmit} isLoading={false} />
    </QueryClientProvider>,
  )
}

beforeEach(() => {
  mockTemplates.mockReset()
  mockTemplates.mockResolvedValue(TEMPLATES)
})

describe('JobDescriptionForm template picker', () => {
  it('renders the template picker with grouped roles', async () => {
    renderForm()
    const select = await screen.findByDisplayValue('Choose a role to pre-fill the form…')
    expect(select).toBeInTheDocument()
    // Both templates listed by title
    expect(screen.getByRole('option', { name: 'Senior Backend Engineer' })).toBeInTheDocument()
    expect(screen.getByRole('option', { name: 'Data Scientist' })).toBeInTheDocument()
  })

  it('pre-fills title, experience level, and description from a template', async () => {
    const user = userEvent.setup()
    renderForm()

    const select = await screen.findByDisplayValue('Choose a role to pre-fill the form…')
    await user.selectOptions(select, 'senior-backend-engineer')

    await waitFor(() => {
      expect(screen.getByPlaceholderText('e.g. Senior Backend Engineer')).toHaveValue(
        'Senior Backend Engineer',
      )
    })
    // Experience level switches to the template's level
    expect(screen.getByDisplayValue('Senior (5–8 yrs)')).toBeInTheDocument()
    // Description textarea filled with the template text (still editable)
    const textarea = screen.getByPlaceholderText(/Example:/i)
    expect(textarea).toHaveValue(TEMPLATES[0].description)
    // Description counter reflects the filled length
    expect(screen.getByText(`${TEMPLATES[0].description.length} / 10,000`)).toBeInTheDocument()
  })

  it('keeps the description editable after applying a template', async () => {
    const user = userEvent.setup()
    renderForm()

    const select = await screen.findByDisplayValue('Choose a role to pre-fill the form…')
    await user.selectOptions(select, 'data-scientist')

    const textarea = await screen.findByPlaceholderText(/Example:/i)
    await waitFor(() => expect(textarea).toHaveValue(TEMPLATES[1].description))

    await user.type(textarea, ' Edit away.')
    expect(textarea).toHaveValue(TEMPLATES[1].description + ' Edit away.')
  })

  it('form still validates and submits normally without picking a template', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    renderForm(onSubmit)

    await screen.findByDisplayValue('Choose a role to pre-fill the form…')
    await user.type(screen.getByPlaceholderText('e.g. Senior Backend Engineer'), 'Custom Role')
    await user.type(screen.getByPlaceholderText(/Example:/i), 'x'.repeat(60))
    await user.click(screen.getByRole('button', { name: /Analyse Match/i }))

    await waitFor(() => expect(onSubmit).toHaveBeenCalledTimes(1))
    expect(onSubmit.mock.calls[0][0]).toMatchObject({ title: 'Custom Role' })
  })
})
