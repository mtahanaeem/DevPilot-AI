import { get, post } from "./client";

export interface Issue {
  github_issue_id: number;
  repo_owner: string;
  repo_name: string;
  issue_title: string;
  issue_url: string;
  labels: string;
  score: number | null;
  is_bookmarked: boolean;
}

export interface BookmarkedIssue {
  id: string;
  github_issue_id: number;
  repo_owner: string;
  repo_name: string;
  issue_title: string;
  issue_url: string;
  labels: string;
  score: number | null;
  created_at: string;
}

export function searchIssues(query = "", limit = 20): Promise<Issue[]> {
  const qs = query
    ? `?query=${encodeURIComponent(query)}&limit=${limit}`
    : `?limit=${limit}`;
  return get(`/opensource/search${qs}`);
}

export function bookmarkIssue(issue: {
  github_issue_id: number;
  repo_owner: string;
  repo_name: string;
  issue_title: string;
  issue_url: string;
  labels?: string;
  score?: number | null;
}): Promise<{ id: string; status: string }> {
  return post("/opensource/bookmark", issue);
}

export function dismissIssue(
  issueId: string
): Promise<{ id: string; status: string }> {
  return post(`/opensource/${issueId}/dismiss`);
}

export function listBookmarked(): Promise<BookmarkedIssue[]> {
  return get("/opensource/bookmarked");
}
