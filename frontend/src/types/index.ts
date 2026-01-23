/**
 * TypeScript type definitions for the application.
 */

export interface Job {
  id: number;
  url: string;
  title: string;
  company: string;
  location: string | null;
  remote: boolean;
  yoe_required: number;
  required_skills: string[] | null;
  nice_to_have_skills: string[] | null;
  responsibilities: string[] | null;
  job_summary: string | null;
  date_posted: string | null;
  source_domain: string | null;
  relevance_score: number;
  status: string;
  applied: boolean;
  applied_date: string | null;
  notes: string | null;
  resume_id: number | null;
  resume_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface Resume {
  id: number;
  job_id: number | null;
  job_title: string;
  company: string;
  resume_location: string | null;
  selected_projects: string[];
  tex_path: string | null;
  pdf_path: string | null;
  cloud_url: string | null;
  created_at: string;
}

export interface SearchSession {
  search_id: number;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  current_step: string | null;
  urls_found: number;
  jobs_extracted: number;
  jobs_parsed: number;
  jobs_saved: number;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface DashboardStats {
  total_jobs: number;
  applied: number;
  pending: number;
  resumes_generated: number;
  recent_searches: Array<{
    id: number;
    job_titles: string[];
    status: string;
    jobs_saved: number;
    created_at: string | null;
  }>;
}

export interface UserSettings {
  default_job_titles: string[] | null;
  default_domains: string[] | null;
  max_yoe: number;
  preferred_locations: string[] | null;
  remote_only: boolean;
  excluded_keywords: string[] | null;
  cloud_storage_config: Record<string, any> | null;
}
