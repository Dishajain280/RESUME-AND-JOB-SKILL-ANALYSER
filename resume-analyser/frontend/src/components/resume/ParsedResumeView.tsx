import type { ResumeSection } from '@/types/api'
import { User, Mail, Phone, Linkedin, Github, Briefcase, GraduationCap, Award, Cpu } from 'lucide-react'
import { categoryColor } from '@/lib/utils'

interface ParsedResumeViewProps {
  parsed: ResumeSection
}

export default function ParsedResumeView({ parsed }: ParsedResumeViewProps) {
  const { contact_info, summary, skills, experience, education, certifications } = parsed

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Contact */}
      <section className="card">
        <h3 className="font-semibold text-gray-800 flex items-center gap-2 mb-4">
          <User className="w-4 h-4 text-brand-500" /> Contact Info
        </h3>
        <div className="grid sm:grid-cols-2 gap-3">
          {contact_info.name && (
            <InfoRow icon={<User className="w-3.5 h-3.5" />} label="Name" value={contact_info.name} />
          )}
          {contact_info.email && (
            <InfoRow icon={<Mail className="w-3.5 h-3.5" />} label="Email" value={contact_info.email} />
          )}
          {contact_info.phone && (
            <InfoRow icon={<Phone className="w-3.5 h-3.5" />} label="Phone" value={contact_info.phone} />
          )}
          {contact_info.linkedin && (
            <InfoRow icon={<Linkedin className="w-3.5 h-3.5" />} label="LinkedIn" value={contact_info.linkedin} isLink />
          )}
          {contact_info.github && (
            <InfoRow icon={<Github className="w-3.5 h-3.5" />} label="GitHub" value={contact_info.github} isLink />
          )}
        </div>
        {!Object.keys(contact_info).length && (
          <p className="text-sm text-gray-400">No contact info detected.</p>
        )}
      </section>

      {/* Summary */}
      {summary && (
        <section className="card">
          <h3 className="font-semibold text-gray-800 mb-3">Professional Summary</h3>
          <p className="text-sm text-gray-600 leading-relaxed">{summary}</p>
        </section>
      )}

      {/* Skills */}
      <section className="card">
        <h3 className="font-semibold text-gray-800 flex items-center gap-2 mb-4">
          <Cpu className="w-4 h-4 text-brand-500" /> Detected Skills ({skills.length})
        </h3>
        {skills.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {skills.map((s) => (
              <span
                key={s.name}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium text-white"
                style={{ backgroundColor: categoryColor(s.category) }}
                title={s.category}
              >
                {s.name}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-400">No skills extracted.</p>
        )}
      </section>

      {/* Experience */}
      {experience.length > 0 && (
        <section className="card">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2 mb-4">
            <Briefcase className="w-4 h-4 text-brand-500" /> Experience
          </h3>
          <div className="space-y-4">
            {experience.map((exp, i) => (
              <div key={i} className="border-l-2 border-brand-100 pl-4">
                <p className="font-medium text-gray-800 text-sm">{exp.title}</p>
                {exp.company && <p className="text-xs text-gray-500">{exp.company}</p>}
                {exp.date_range && (
                  <p className="text-xs text-brand-600 mt-0.5">{exp.date_range}</p>
                )}
                {exp.bullets.length > 0 && (
                  <ul className="mt-2 space-y-1">
                    {exp.bullets.slice(0, 3).map((b, j) => (
                      <li key={j} className="text-xs text-gray-600">• {b}</li>
                    ))}
                  </ul>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Education */}
      {education.length > 0 && (
        <section className="card">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2 mb-4">
            <GraduationCap className="w-4 h-4 text-brand-500" /> Education
          </h3>
          <div className="space-y-3">
            {education.map((edu, i) => (
              <div key={i} className="flex justify-between items-start">
                <div>
                  <p className="font-medium text-sm text-gray-800">{edu.degree}</p>
                  {edu.institution && <p className="text-xs text-gray-500">{edu.institution}</p>}
                </div>
                {edu.year && <span className="text-xs text-gray-400">{edu.year}</span>}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Certifications */}
      {certifications.length > 0 && (
        <section className="card">
          <h3 className="font-semibold text-gray-800 flex items-center gap-2 mb-4">
            <Award className="w-4 h-4 text-brand-500" /> Certifications ({certifications.length})
          </h3>
          <ul className="space-y-1">
            {certifications.map((c, i) => (
              <li key={i} className="text-sm text-gray-600 flex gap-2">
                <span className="text-brand-400">✓</span> {c}
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}

function InfoRow({
  icon,
  label,
  value,
  isLink,
}: {
  icon: React.ReactNode
  label: string
  value: string
  isLink?: boolean
}) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="text-gray-400">{icon}</span>
      <span className="text-gray-500 w-16 shrink-0">{label}</span>
      {isLink ? (
        <a href={value} target="_blank" rel="noopener noreferrer" className="text-brand-600 hover:underline truncate">
          {value}
        </a>
      ) : (
        <span className="text-gray-800 truncate">{value}</span>
      )}
    </div>
  )
}
