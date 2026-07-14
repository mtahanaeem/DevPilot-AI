import { post, get } from "./client";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: { id: string; github_username: string };
}

export interface UserInfo {
  id: string;
  github_username: string;
}

export function loginWithPat(pat: string): Promise<TokenResponse> {
  return post<TokenResponse>("/auth/login", { pat });
}

export function getMe(): Promise<UserInfo> {
  return get<UserInfo>("/auth/me");
}
