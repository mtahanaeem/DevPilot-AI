import { get, post } from "./client";

export interface GapAnalysis {
  id: string;
  job_description_id: string;
  current_skills: string[];
  gaps: string[];
  present_skills: string[];
  overall_match: number;
  recommendations: string[];
  created_at: string;
}

export function inferSkills(): Promise<{ skills: string[] }> {
  return get("/skills/infer");
}

export function analyzeGaps(jobId: string): Promise<GapAnalysis> {
  return post(`/skills/analyze/${jobId}`);
}

export function listReports(): Promise<GapAnalysis[]> {
  return get("/skills/reports");
}
