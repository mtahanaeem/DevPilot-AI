import { get, post } from "./client";

export interface SocialPost {
  id: string;
  repository_id: string;
  platform: string;
  content: string;
  status: string;
  created_at: string;
}

export function generatePost(repoId: string, platform = "linkedin", tone = "professional"): Promise<SocialPost> {
  return post<SocialPost>(`/social/generate?repo_id=${repoId}&platform=${platform}&tone=${tone}`);
}

export function listPosts(): Promise<SocialPost[]> {
  return get<SocialPost[]>("/social");
}

export function approvePost(id: string): Promise<SocialPost> {
  return post<SocialPost>(`/social/${id}/approve`);
}
