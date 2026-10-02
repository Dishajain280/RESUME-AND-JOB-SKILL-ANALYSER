import { BrainCircuit } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="border-t border-gray-100 bg-white mt-16">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <BrainCircuit className="w-4 h-4 text-brand-500" />
          <span>ResumeAI &copy; {new Date().getFullYear()} — AI Resume &amp; Job Skill Analyser</span>
        </div>
        <div className="flex items-center gap-4 text-sm text-gray-400">
          <span>Built with React + FastAPI</span>
        </div>
      </div>
    </footer>
  )
}
