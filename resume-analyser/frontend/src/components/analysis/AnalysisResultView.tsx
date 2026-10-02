import type { AnalysisResult } from '@/types/api'
import ScoreGauge from './ScoreGauge'
import SkillMatchGrid from './SkillMatchGrid'
import SkillChart from './SkillChart'
import RecommendedCourses from './RecommendedCourses'
import { Lightbulb, TrendingUp, TrendingDown, ShieldCheck, Target, Sparkles } from 'lucide-react'
import { scoreColor, scoreLabel } from '@/lib/utils'
import { useState } from 'react'

interface AnalysisResultViewProps {
  result: AnalysisResult
}

const SUB_SCORES = [
  { key: 'skill_match_score',  label: 'Skill Match'  },
  { key: 'experience_score',   label: 'Experience'   },
  { key: 'education_score',    label: 'Education'    },
  { key: 'keyword_score',      label: 'Keywords'     },
] as const

export default function AnalysisResultView({ result }: AnalysisResultViewProps) {
  const [chartType, setChartType] = useState<'bar' | 'radar'>('bar')

  return (
    <div className="space-y-8 animate-slide-up">

      {/* ── Hero Score ─────────────────────────────────────────────────────── */}
      <section className="card flex flex-col sm:flex-row items-center gap-8">
        <ScoreGauge score={result.overall_score} size="lg" label="Overall Match" />

        <div className="flex-1 w-full">
          <h2 className="text-xl font-bold text-gray-900">
            {result.job_title}
            {result.company && <span className="text-gray-500 font-normal"> @ {result.company}</span>}
          </h2>
          <p className={`text-sm font-semibold mt-1 ${scoreColor(result.overall_score)}`}>
            {scoreLabel(result.overall_score)} match
          </p>

          {/* Sub-scores */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
            {SUB_SCORES.map(({ key, label }) => (
              <div key={key} className="text-center">
                <ScoreGauge score={result[key]} size="sm" label={label} />
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Matched / Missing / Bonus ─────────────────────────────────────── */}
      <div className="grid sm:grid-cols-3 gap-4">
        <SkillPillCard
          title="✅ Matched Skills"
          skills={result.matched_skills}
          className="bg-green-50 border-green-200"
          pillClass="bg-green-100 text-green-800"
        />
        <SkillPillCard
          title="❌ Missing Skills"
          skills={result.missing_skills}
          className="bg-red-50 border-red-200"
          pillClass="bg-red-100 text-red-700"
        />
        <SkillPillCard
          title="⭐ Bonus Skills"
          skills={result.bonus_skills}
          className="bg-blue-50 border-blue-200"
          pillClass="bg-blue-100 text-blue-700"
        />
      </div>

      {/* ── Skill Match Detail ────────────────────────────────────────────── */}
      <section className="card">
        <h3 className="font-semibold text-gray-800 text-lg mb-4 flex items-center gap-2">
          <Target className="w-5 h-5 text-brand-500" /> Skill-by-Skill Analysis
        </h3>
        <SkillMatchGrid matches={result.skill_matches} />
      </section>

      {/* ── Category Breakdown Chart ──────────────────────────────────────── */}
      {result.gap_by_category.length > 0 && (
        <section className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-800 text-lg">Category Breakdown</h3>
            <div className="flex gap-1 p-1 bg-gray-100 rounded-lg">
              {(['bar', 'radar'] as const).map((t) => (
                <button
                  key={t}
                  onClick={() => setChartType(t)}
                  className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                    chartType === t ? 'bg-white shadow-sm text-gray-800' : 'text-gray-500'
                  }`}
                >
                  {t.charAt(0).toUpperCase() + t.slice(1)}
                </button>
              ))}
            </div>
          </div>
          <SkillChart data={result.gap_by_category} type={chartType} />
        </section>
      )}

      {/* ── Strengths & Weaknesses ────────────────────────────────────────── */}
      <div className="grid sm:grid-cols-2 gap-4">
        <section className="card">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2 mb-4">
            <TrendingUp className="w-4 h-4 text-green-500" /> Strengths
          </h3>
          <ul className="space-y-2">
            {result.strengths.map((s, i) => (
              <li key={i} className="text-sm text-gray-700 flex gap-2">
                <span className="text-green-500 mt-0.5">●</span> {s}
              </li>
            ))}
          </ul>
        </section>
        <section className="card">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2 mb-4">
            <TrendingDown className="w-4 h-4 text-red-400" /> Areas to Improve
          </h3>
          <ul className="space-y-2">
            {result.weaknesses.map((w, i) => (
              <li key={i} className="text-sm text-gray-700 flex gap-2">
                <span className="text-red-400 mt-0.5">●</span> {w}
              </li>
            ))}
          </ul>
        </section>
      </div>

      {/* ── Recommendations ──────────────────────────────────────────────── */}
      <section className="card">
        <h3 className="font-semibold text-gray-800 text-lg flex items-center gap-2 mb-4">
          <Lightbulb className="w-5 h-5 text-yellow-500" /> Recommendations
        </h3>
        <ol className="space-y-3">
          {result.recommendations.map((rec, i) => (
            <li key={i} className="flex gap-3 text-sm text-gray-700">
              <span className="w-6 h-6 rounded-full bg-brand-100 text-brand-700 text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                {i + 1}
              </span>
              {rec}
            </li>
          ))}
        </ol>
      </section>

      {/* ── Course Recommendations ────────────────────────────────────────── */}
      {result.recommended_courses.length > 0 && (
        <section className="card">
          <h3 className="font-semibold text-gray-800 text-lg flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-purple-500" /> Recommended Courses
          </h3>
          <RecommendedCourses courses={result.recommended_courses} />
        </section>
      )}

      {/* ── ATS Tips ─────────────────────────────────────────────────────── */}
      <section className="card border-dashed border-brand-200 bg-brand-50">
        <h3 className="font-semibold text-brand-800 flex items-center gap-2 mb-4">
          <ShieldCheck className="w-5 h-5 text-brand-600" /> ATS Optimisation Tips
        </h3>
        <ul className="space-y-2">
          {result.ats_tips.map((tip, i) => (
            <li key={i} className="text-sm text-brand-700 flex gap-2">
              <span className="text-brand-400">→</span> {tip}
            </li>
          ))}
        </ul>
      </section>
    </div>
  )
}

function SkillPillCard({
  title,
  skills,
  className,
  pillClass,
}: {
  title: string
  skills: string[]
  className: string
  pillClass: string
}) {
  return (
    <div className={`rounded-2xl border p-4 ${className}`}>
      <p className="text-sm font-semibold text-gray-700 mb-3">{title} <span className="font-normal text-gray-500">({skills.length})</span></p>
      <div className="flex flex-wrap gap-1.5">
        {skills.length === 0 ? (
          <span className="text-xs text-gray-400">None</span>
        ) : skills.map((s) => (
          <span key={s} className={`px-2.5 py-1 rounded-full text-xs font-medium ${pillClass}`}>
            {s}
          </span>
        ))}
      </div>
    </div>
  )
}
