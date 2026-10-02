import { useMemo } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useQuery } from '@tanstack/react-query'
import { Sparkles, ChevronDown } from 'lucide-react'
import { getJobTemplates } from '@/services/apiService'
import type { JobDescriptionRequest, ExperienceLevel } from '@/types/api'

const schema = z.object({
  title: z.string().min(2, 'Job title is required').max(200),
  company: z.string().max(100).optional(),
  description: z.string().min(50, 'Please provide at least 50 characters').max(10000),
  experience_level: z.enum(['intern', 'junior', 'mid', 'senior', 'lead', 'principal']),
  location: z.string().max(100).optional(),
})

type FormValues = z.infer<typeof schema>

interface JobFormProps {
  onSubmit: (values: JobDescriptionRequest) => void
  isLoading: boolean
}

const EXPERIENCE_LEVELS: { value: ExperienceLevel; label: string }[] = [
  { value: 'intern',    label: 'Intern' },
  { value: 'junior',   label: 'Junior (0–2 yrs)' },
  { value: 'mid',      label: 'Mid-Level (2–5 yrs)' },
  { value: 'senior',   label: 'Senior (5–8 yrs)' },
  { value: 'lead',     label: 'Lead / Staff (7+ yrs)' },
  { value: 'principal',label: 'Principal / Architect (10+ yrs)' },
]

const JD_PLACEHOLDER = `Example:
We are looking for a Senior Backend Engineer with 5+ years of experience.

Required skills: Python, FastAPI, PostgreSQL, Docker, Kubernetes, AWS, REST API, microservices.
Preferred: Terraform, Redis, GraphQL.

Responsibilities:
• Design and build scalable backend systems
• Lead architecture decisions and code reviews
• Collaborate with cross-functional teams in an Agile environment
• Mentor junior engineers`

export default function JobDescriptionForm({ onSubmit, isLoading }: JobFormProps) {
  const {
    register,
    handleSubmit,
    setValue,
    resetField,
    formState: { errors },
    watch,
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { experience_level: 'mid' },
  })

  // Templates come from the backend; the form stays fully usable if the
  // request fails (picker simply doesn't render its options).
  const { data: templates } = useQuery({
    queryKey: ['job-templates'],
    queryFn: getJobTemplates,
    staleTime: Infinity, // static catalogue — never refetch
  })

  const grouped = useMemo(() => {
    const byCategory = new Map<string, typeof templates>()
    for (const t of templates ?? []) {
      const list = byCategory.get(t.category) ?? []
      list.push(t)
      byCategory.set(t.category, list)
    }
    return [...byCategory.entries()]
  }, [templates])

  const descLength = watch('description')?.length ?? 0

  const applyTemplate = (id: string) => {
    const tpl = templates?.find((t) => t.id === id)
    if (!tpl) return
    setValue('title', tpl.title, { shouldValidate: true })
    setValue('experience_level', tpl.experience_level, { shouldValidate: true })
    setValue('description', tpl.description, { shouldValidate: true })
    resetField('company') // clear any stale company from a previous fill
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
      {/* Role template quick-fill */}
      {templates && templates.length > 0 && (
        <div className="relative">
          <label className="label flex items-center gap-1.5">
            <Sparkles className="w-3.5 h-3.5 text-brand-500" />
            Start from a role template
            <span className="font-normal text-gray-400">— everything stays editable</span>
          </label>
          <select
            defaultValue=""
            onChange={(e) => {
              applyTemplate(e.target.value)
              e.currentTarget.value = '' // reset so re-picking the same role re-fills
            }}
            className="input pr-9 appearance-none bg-white cursor-pointer"
          >
            <option value="" disabled>
              Choose a role to pre-fill the form…
            </option>
            {grouped.map(([category, list]) => (
              <optgroup key={category} label={category}>
                {list?.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.title}
                  </option>
                ))}
              </optgroup>
            ))}
          </select>
          <ChevronDown className="w-4 h-4 text-gray-400 absolute right-3 bottom-3 pointer-events-none" />
        </div>
      )}

      {/* Title + Company */}
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Job Title *</label>
          <input
            {...register('title')}
            placeholder="e.g. Senior Backend Engineer"
            className="input"
          />
          {errors.title && <p className="text-xs text-red-500 mt-1">{errors.title.message}</p>}
        </div>
        <div>
          <label className="label">Company</label>
          <input
            {...register('company')}
            placeholder="e.g. Acme Corp"
            className="input"
          />
        </div>
      </div>

      {/* Experience level + Location */}
      <div className="grid sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Experience Level *</label>
          <select {...register('experience_level')} className="input">
            {EXPERIENCE_LEVELS.map(({ value, label }) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Location</label>
          <input
            {...register('location')}
            placeholder="e.g. Remote / New York, NY"
            className="input"
          />
        </div>
      </div>

      {/* Job Description */}
      <div>
        <label className="label">
          Job Description *
          <span className="ml-auto text-xs text-gray-400 font-normal float-right">
            {descLength} / 10,000
          </span>
        </label>
        <textarea
          {...register('description')}
          rows={12}
          placeholder={JD_PLACEHOLDER}
          className="input resize-none font-mono text-xs leading-relaxed"
        />
        {errors.description && (
          <p className="text-xs text-red-500 mt-1">{errors.description.message}</p>
        )}
      </div>

      <button type="submit" disabled={isLoading} className="btn-primary w-full py-3 text-base">
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Analysing…
          </span>
        ) : (
          '🔍  Analyse Match'
        )}
      </button>
    </form>
  )
}
