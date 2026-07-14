import { get, post } from "./client";

export interface Resume {
  id: string;
  raw_text: string;
  file_path: string | null;
  created_at: string;
}

export interface JobDescription {
  id: string;
  raw_text: string;
  source_url: string | null;
  created_at: string;
}

export interface SuggestionResult {
  resume_id: string;
  job_id: string;
  suggestions: string;
}

export interface ScoreResult {
  resume_id: string;
  job_id: string;
  score: number;
  strengths: string[];
  gaps: string[];
  summary: string;
}

export function uploadResume(text: string): Promise<Resume> {
  const form = new URLSearchParams();
  form.set("text", text);
  return post<Resume>("/resume/upload", form, "application/x-www-form-urlencoded");
}

export function listResumes(): Promise<Resume[]> {
  return get<Resume[]>("/resume");
}

export function addJob(text: string, sourceUrl = ""): Promise<JobDescription> {
  const qs = sourceUrl ? `?source_url=${encodeURIComponent(sourceUrl)}` : "";
  const form = new URLSearchParams();
  form.set("text", text);
  return post<JobDescription>(`/resume/jobs${qs}`, form, "application/x-www-form-urlencoded");
}

export function listJobs(): Promise<JobDescription[]> {
  return get<JobDescription[]>("/resume/jobs");
}

export function autoDetectJobs(): Promise<JobDescription[]> {
  return post<JobDescription[]>("/resume/jobs/auto-detect");
}

export function optimizeResume(resumeId: string, jobId: string, jobText = ""): Promise<SuggestionResult> {
  const params = new URLSearchParams();
  if (jobText) params.set("job_text", jobText);
  else params.set("job_id", jobId);
  return post<SuggestionResult>(`/resume/${resumeId}/optimize?${params}`);
}

export function scoreResume(resumeId: string, jobId: string, jobText = ""): Promise<ScoreResult> {
  const params = new URLSearchParams();
  if (jobText) params.set("job_text", jobText);
  else params.set("job_id", jobId);
  return post<ScoreResult>(`/resume/${resumeId}/score?${params}`);
}
