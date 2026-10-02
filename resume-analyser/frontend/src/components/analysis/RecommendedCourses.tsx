import type { RecommendedCourse } from '@/types/api'
import { ExternalLink, Clock } from 'lucide-react'

const DIFFICULTY_COLOR: Record<string, string> = {
  Beginner: 'bg-green-100 text-green-700',
  Intermediate: 'bg-yellow-100 text-yellow-700',
  Advanced: 'bg-red-100 text-red-700',
}

export default function RecommendedCourses({ courses }: { courses: RecommendedCourse[] }) {
  return (
    <div className="grid sm:grid-cols-2 gap-4">
      {courses.map((course, i) => (
        <a
          key={i}
          href={course.url}
          target="_blank"
          rel="noopener noreferrer"
          className="group p-4 rounded-xl border border-gray-100 hover:border-brand-300 hover:bg-brand-50 transition-all"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm text-gray-800 group-hover:text-brand-700 truncate">
                {course.title}
              </p>
              <p className="text-xs text-gray-500 mt-0.5">{course.provider}</p>
            </div>
            <ExternalLink className="w-3.5 h-3.5 text-gray-300 group-hover:text-brand-500 shrink-0 mt-1" />
          </div>

          <div className="flex items-center gap-3 mt-3">
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-purple-100 text-purple-700">
              {course.skill_covered}
            </span>
            <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${DIFFICULTY_COLOR[course.difficulty] ?? 'bg-gray-100 text-gray-600'}`}>
              {course.difficulty}
            </span>
            {course.duration_hours && (
              <span className="text-xs text-gray-400 flex items-center gap-1 ml-auto">
                <Clock className="w-3 h-3" />
                {course.duration_hours}h
              </span>
            )}
          </div>
        </a>
      ))}
    </div>
  )
}
