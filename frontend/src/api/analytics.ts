import { get, post } from "./client";

export interface RepoStats {
  name: string;
  owner: string;
  stars: number;
  forks: number;
  language: string;
  last_commit_at: string | null;
  is_stale: boolean;
}

export interface DashboardData {
  total_repos: number;
  total_stars: number;
  total_forks: number;
  stale_count: number;
  active_count: number;
  language_distribution: { language: string; count: number }[];
  repos: RepoStats[];
}

export interface WeeklyReport {
  id: string;
  period: string;
  summary: string;
  highlights: string[];
  recommendations: string[];
  metrics: {
    total_repos: number;
    total_stars: number;
    total_forks: number;
    stale_count: number;
  };
  created_at: string;
}

export function getDashboard(): Promise<DashboardData> {
  return get("/analytics/dashboard");
}

export function generateWeeklyReport(): Promise<WeeklyReport> {
  return post("/analytics/weekly-report");
}

export function listReports(): Promise<WeeklyReport[]> {
  return get("/analytics/reports");
}
