import { Link } from 'react-router-dom'
import { BrainCircuit, Upload, Target, BookOpen, TrendingUp, CheckCircle2, Zap } from 'lucide-react'

const FEATURES = [
  {
    icon: Upload,
    title: 'Smart Resume Parsing',
    desc: 'Upload PDF, DOCX, or TXT. Our AI extracts skills, experience, and education automatically.',
    color: 'bg-blue-100 text-blue-600',
  },
  {
    icon: Target,
    title: 'Skill Gap Analysis',
    desc: 'Compare your skills against any job description and see exactly what matches or is missing.',
    color: 'bg-purple-100 text-purple-600',
  },
  {
    icon: TrendingUp,
    title: 'Match Score',
    desc: 'Get an overall match score with breakdowns for skills, experience, education, and keywords.',
    color: 'bg-green-100 text-green-600',
  },
  {
    icon: BookOpen,
    title: 'Learning Recommendations',
    desc: 'Receive curated course suggestions to close your skill gaps from top providers.',
    color: 'bg-orange-100 text-orange-600',
  },
  {
    icon: CheckCircle2,
    title: 'ATS Optimisation',
    desc: 'Get actionable tips to make your resume pass Applicant Tracking Systems.',
    color: 'bg-pink-100 text-pink-600',
  },
  {
    icon: Zap,
    title: 'Instant Results',
    desc: 'Analysis completes in seconds. No sign-up required — just upload and analyse.',
    color: 'bg-yellow-100 text-yellow-600',
  },
]

const STEPS = [
  { step: '01', title: 'Upload Resume', desc: 'Drag and drop your resume file (PDF, DOCX, or TXT).' },
  { step: '02', title: 'Paste Job Description', desc: 'Copy the job posting you want to apply for.' },
  { step: '03', title: 'Get Your Analysis', desc: 'Review your match score, gaps, and personalised recommendations.' },
]

export default function HomePage() {
  return (
    <div className="animate-fade-in">
      {/* ── Hero ──────────────────────────────────────────────────────────── */}
      <section className="relative overflow-hidden bg-gradient-to-br from-brand-600 to-brand-800 text-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-24 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 text-sm font-medium mb-6">
            <BrainCircuit className="w-4 h-4" /> AI-Powered Resume Intelligence
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight">
            Know exactly how well<br />your resume fits
          </h1>
          <p className="mt-6 text-lg sm:text-xl text-blue-100 max-w-2xl mx-auto">
            Upload your resume, paste a job description, and get an instant AI-powered analysis
            with skill gap detection, match scoring, and learning recommendations.
          </p>
          <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/analyse" className="inline-flex items-center justify-center gap-2 bg-white text-brand-700 font-semibold px-8 py-3.5 rounded-xl hover:bg-blue-50 transition-colors">
              <Upload className="w-4 h-4" /> Analyse My Resume
            </Link>
            <Link to="/history" className="inline-flex items-center justify-center gap-2 bg-white/10 text-white font-semibold px-8 py-3.5 rounded-xl hover:bg-white/20 transition-colors">
              View Past Analyses
            </Link>
          </div>
        </div>

        {/* Subtle decoration */}
        <div className="absolute -bottom-12 -left-12 w-64 h-64 bg-white/5 rounded-full" />
        <div className="absolute -top-12 -right-12 w-96 h-96 bg-white/5 rounded-full" />
      </section>

      {/* ── How it works ──────────────────────────────────────────────────── */}
      <section className="max-w-5xl mx-auto px-4 sm:px-6 py-20">
        <h2 className="text-2xl font-bold text-center text-gray-900 mb-12">How It Works</h2>
        <div className="grid sm:grid-cols-3 gap-8">
          {STEPS.map((s) => (
            <div key={s.step} className="text-center">
              <div className="w-12 h-12 rounded-full bg-brand-100 text-brand-700 font-bold text-lg flex items-center justify-center mx-auto mb-4">
                {s.step}
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{s.title}</h3>
              <p className="text-sm text-gray-500">{s.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────────────────── */}
      <section className="bg-gray-50 border-y border-gray-100">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 py-20">
          <h2 className="text-2xl font-bold text-center text-gray-900 mb-12">Everything You Need</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {FEATURES.map((f) => {
              const Icon = f.icon
              return (
                <div key={f.title} className="card hover:shadow-md transition-shadow">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${f.color}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="font-semibold text-gray-900 mb-2">{f.title}</h3>
                  <p className="text-sm text-gray-500">{f.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────────────────── */}
      <section className="max-w-3xl mx-auto px-4 sm:px-6 py-20 text-center">
        <h2 className="text-3xl font-bold text-gray-900">Ready to land your dream job?</h2>
        <p className="mt-4 text-gray-500">Start with your resume and get actionable insights in seconds.</p>
        <Link to="/analyse" className="inline-flex items-center gap-2 btn-primary mt-8 py-3.5 px-10 text-base">
          <BrainCircuit className="w-5 h-5" /> Get Started Free
        </Link>
      </section>
    </div>
  )
}
