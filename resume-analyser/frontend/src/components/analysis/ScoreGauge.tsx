import { cn, scoreLabel, scoreColor } from '@/lib/utils'

interface ScoreGaugeProps {
  score: number
  size?: 'sm' | 'md' | 'lg'
  showLabel?: boolean
  label?: string
}

export default function ScoreGauge({ score, size = 'md', showLabel = true, label }: ScoreGaugeProps) {
  const radius = size === 'lg' ? 52 : size === 'md' ? 40 : 30
  const stroke = size === 'lg' ? 8 : size === 'md' ? 6 : 5
  const circumference = 2 * Math.PI * radius
  const progress = (score / 100) * circumference
  const svgSize = (radius + stroke) * 2 + 4

  const colorClass = scoreColor(score)
  const bgBarColor = score >= 80 ? '#dcfce7' : score >= 60 ? '#fef9c3' : '#fee2e2'
  const fgBarColor = score >= 80 ? '#22c55e' : score >= 60 ? '#eab308' : '#ef4444'
  const fontSize = size === 'lg' ? 'text-3xl' : size === 'md' ? 'text-2xl' : 'text-lg'

  return (
    <div className="flex flex-col items-center gap-2">
      <div className="relative inline-flex items-center justify-center">
        <svg width={svgSize} height={svgSize} className="-rotate-90">
          {/* Background circle */}
          <circle
            cx={svgSize / 2}
            cy={svgSize / 2}
            r={radius}
            fill="none"
            stroke={bgBarColor}
            strokeWidth={stroke}
          />
          {/* Progress arc */}
          <circle
            cx={svgSize / 2}
            cy={svgSize / 2}
            r={radius}
            fill="none"
            stroke={fgBarColor}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={`${progress} ${circumference}`}
            className="transition-all duration-700 ease-out"
          />
        </svg>
        {/* Score text in the centre */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={cn('font-bold leading-none', fontSize, colorClass)}>
            {Math.round(score)}
          </span>
          {size === 'lg' && <span className="text-xs text-gray-400 mt-0.5">/ 100</span>}
        </div>
      </div>
      {showLabel && (
        <div className="text-center">
          {label && <p className="text-xs text-gray-500">{label}</p>}
          <p className={cn('text-xs font-semibold', colorClass)}>{scoreLabel(score)}</p>
        </div>
      )}
    </div>
  )
}
