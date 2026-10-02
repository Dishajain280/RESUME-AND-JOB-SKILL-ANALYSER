import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function scoreColor(score: number): string {
  if (score >= 80) return 'text-green-600'
  if (score >= 60) return 'text-yellow-600'
  return 'text-red-500'
}

export function scoreBg(score: number): string {
  if (score >= 80) return 'bg-green-500'
  if (score >= 60) return 'bg-yellow-500'
  return 'bg-red-500'
}

export function scoreLabel(score: number): string {
  if (score >= 85) return 'Excellent'
  if (score >= 70) return 'Good'
  if (score >= 55) return 'Fair'
  return 'Needs Work'
}

export function categoryColor(category: string): string {
  const map: Record<string, string> = {
    'Programming Languages': '#3b82f6',
    'Frameworks & Libraries': '#8b5cf6',
    'Databases': '#f59e0b',
    'Cloud & DevOps': '#10b981',
    'Tools & Platforms': '#6366f1',
    'Soft Skills': '#ec4899',
    'Domain Knowledge': '#14b8a6',
    'Other': '#94a3b8',
  }
  return map[category] ?? '#94a3b8'
}

export function formatDate(iso: string): string {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export function truncate(str: string, n: number): string {
  return str.length > n ? str.slice(0, n - 1) + '…' : str
}
