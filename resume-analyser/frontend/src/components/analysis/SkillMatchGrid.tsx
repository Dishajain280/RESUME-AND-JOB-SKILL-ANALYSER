import type { SkillMatch } from '@/types/api'
import { CheckCircle2, XCircle, AlertCircle } from 'lucide-react'
import { categoryColor } from '@/lib/utils'
import { useState } from 'react'

interface SkillMatchGridProps {
  matches: SkillMatch[]
}

const STATUS_CONFIG = {
  matched: {
    icon: CheckCircle2,
    color: 'text-green-600',
    bg: 'bg-green-50 border-green-200',
    label: 'Matched',
  },
  partial: {
    icon: AlertCircle,
    color: 'text-yellow-600',
    bg: 'bg-yellow-50 border-yellow-200',
    label: 'Partial',
  },
  missing: {
    icon: XCircle,
    color: 'text-red-500',
    bg: 'bg-red-50 border-red-200',
    label: 'Missing',
  },
}

type FilterStatus = 'all' | 'matched' | 'partial' | 'missing'

export default function SkillMatchGrid({ matches }: SkillMatchGridProps) {
  const [filter, setFilter] = useState<FilterStatus>('all')

  const counts = {
    matched: matches.filter(m => m.status === 'matched').length,
    partial: matches.filter(m => m.status === 'partial').length,
    missing: matches.filter(m => m.status === 'missing').length,
  }

  const filtered = filter === 'all' ? matches : matches.filter(m => m.status === filter)

  return (
    <div className="space-y-4">
      {/* Filter tabs */}
      <div className="flex gap-2 flex-wrap">
        {(['all', 'matched', 'partial', 'missing'] as FilterStatus[]).map((f) => {
          const count = f === 'all' ? matches.length : counts[f]
          const active = filter === f
          return (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                active
                  ? 'bg-brand-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)} ({count})
            </button>
          )
        })}
      </div>

      {/* Grid */}
      <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
        {filtered.map((m) => {
          const cfg = STATUS_CONFIG[m.status]
          const Icon = cfg.icon
          return (
            <div
              key={m.skill}
              className={`flex items-center gap-3 p-3 rounded-xl border ${cfg.bg}`}
            >
              <Icon className={`w-4 h-4 shrink-0 ${cfg.color}`} />
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium text-gray-800 truncate">{m.skill}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <span
                    className="text-[10px] font-medium px-1.5 py-0.5 rounded-full text-white"
                    style={{ backgroundColor: categoryColor(m.category) }}
                  >
                    {m.category}
                  </span>
                  {m.importance === 'required' && (
                    <span className="text-[10px] text-gray-500">required</span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {filtered.length === 0 && (
        <p className="text-sm text-gray-400 text-center py-6">No skills in this category.</p>
      )}
    </div>
  )
}
