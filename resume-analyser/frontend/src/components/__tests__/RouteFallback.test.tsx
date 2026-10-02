import { describe, it, expect } from 'vitest'
import { render } from '@testing-library/react'
import RouteFallback from '@/components/RouteFallback'

describe('RouteFallback', () => {
  it('renders a loading spinner', () => {
    const { container } = render(<RouteFallback />)
    // lucide Loader2 renders an svg carrying the animate-spin class
    const spinner = container.querySelector('svg.animate-spin')
    expect(spinner).toBeInTheDocument()
  })
})
