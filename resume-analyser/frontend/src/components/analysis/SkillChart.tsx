import type { SkillGapCategory } from '@/types/api'
import {
  RadarChart as RechartsRadar,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Cell,
} from 'recharts'
import { categoryColor } from '@/lib/utils'

interface SkillChartProps {
  data: SkillGapCategory[]
  type?: 'bar' | 'radar'
}

export default function SkillChart({ data, type = 'bar' }: SkillChartProps) {
  if (!data.length) return null

  if (type === 'radar') {
    const radarData = data.map((d) => ({
      category: d.category.replace(' & ', ' &\n'),
      score: Math.round(d.score),
    }))

    return (
      <ResponsiveContainer width="100%" height={280}>
        <RechartsRadar data={radarData}>
          <PolarGrid stroke="#e5e7eb" />
          <PolarAngleAxis
            dataKey="category"
            tick={{ fill: '#6b7280', fontSize: 11 }}
          />
          <Radar
            name="Skill Score"
            dataKey="score"
            stroke="#3b82f6"
            fill="#3b82f6"
            fillOpacity={0.25}
          />
          <Tooltip
            formatter={(v: number) => [`${v}%`, 'Score']}
            contentStyle={{ borderRadius: '12px', border: '1px solid #e5e7eb', fontSize: 12 }}
          />
        </RechartsRadar>
      </ResponsiveContainer>
    )
  }

  // Bar chart
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 24 }}>
        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} tickFormatter={(v) => `${v}%`} />
        <YAxis
          type="category"
          dataKey="category"
          width={140}
          tick={{ fontSize: 11, fill: '#4b5563' }}
        />
        <Tooltip
          formatter={(v: number) => [`${v.toFixed(0)}%`, 'Match']}
          contentStyle={{ borderRadius: '12px', border: '1px solid #e5e7eb', fontSize: 12 }}
        />
        <Bar dataKey="score" radius={[0, 6, 6, 0]} maxBarSize={24}>
          {data.map((entry) => (
            <Cell
              key={entry.category}
              fill={categoryColor(entry.category)}
              opacity={0.85}
            />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
