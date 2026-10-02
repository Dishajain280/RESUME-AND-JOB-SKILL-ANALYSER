// Shared TypeScript types mirroring the backend Pydantic schemas

export type SkillCategory =
  | 'Programming Languages'
  | 'Frameworks & Libraries'
  | 'Databases'
  | 'Cloud & DevOps'
  | 'Tools & Platforms'
  | 'Soft Skills'
  | 'Domain Knowledge'
  | 'Other'

export type ExperienceLevel =
  | 'intern'
  | 'junior'
  | 'mid'
  | 'senior'
  | 'lead'
  | 'principal'

export interface SkillItem {
  name: string
  category: SkillCategory
  confidence: number
  years_experience?: number
}

export interface ResumeSection {
  contact_info: Record<string, string>
  summary?: string
  skills: SkillItem[]
  experience: Array<{
    title: string
    company: string
    date_range: string
    bullets: string[]
  }>
  education: Array<{
    degree: string
    institution: string
    year: string
    field: string
  }>
  certifications: string[]
  raw_text: string
}

export interface ResumeUploadResponse {
  resume_id: string
  filename: string
  parsed: ResumeSection
  word_count: number
  page_count: number
}

export interface JobDescriptionRequest {
  title: string
  company?: string
  description: string
  experience_level: ExperienceLevel
  location?: string
}

export interface SkillMatch {
  skill: string
  category: SkillCategory
  status: 'matched' | 'missing' | 'partial'
  confidence: number
  candidate_proficiency?: number
  importance: string
}

export interface SkillGapCategory {
  category: string
  matched: number
  missing: number
  score: number
}

export interface RecommendedCourse {
  title: string
  provider: string
  url: string
  skill_covered: string
  difficulty: string
  duration_hours?: number
}

export interface AnalysisResult {
  analysis_id: string
  resume_id: string
  job_title: string
  company?: string
  overall_score: number
  skill_match_score: number
  experience_score: number
  education_score: number
  keyword_score: number
  skill_matches: SkillMatch[]
  gap_by_category: SkillGapCategory[]
  matched_skills: string[]
  missing_skills: string[]
  bonus_skills: string[]
  recommendations: string[]
  recommended_courses: RecommendedCourse[]
  ats_tips: string[]
  strengths: string[]
  weaknesses: string[]
}

export interface AnalysisListItem {
  analysis_id: string
  resume_id: string
  job_title: string
  company?: string
  overall_score: number
  created_at: string
}

export interface AnalysisHistoryResponse {
  items: AnalysisListItem[]
  /** Count of ALL matching rows (for pagination controls) */
  total: number
  /** Page size actually applied (echoed back) */
  limit: number
  /** Row offset actually applied (echoed back) */
  offset: number
}

export interface JobRoleTemplate {
  id: string
  title: string
  category: string
  experience_level: 'intern' | 'junior' | 'mid' | 'senior' | 'lead' | 'principal'
  description: string
}

export interface AnalyseRequest {
  resume_id: string
  job: JobDescriptionRequest
}
