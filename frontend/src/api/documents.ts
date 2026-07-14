import { get, post } from "./client";

export interface Document {
  id: string;
  repository_id: string;
  type: string;
  content: string;
  status: string;
  created_at: string;
}

export function generateDocument(repoId: string, docType = "readme"): Promise<Document> {
  return post<Document>(`/documents/generate?doc_type=${docType}`, { repo_id: repoId });
}

export function listDocuments(repoId?: string): Promise<Document[]> {
  const qs = repoId ? `?repo_id=${repoId}` : "";
  return get<Document[]>(`/documents${qs}`);
}

export function getDocument(id: string): Promise<Document> {
  return get<Document>(`/documents/${id}`);
}

export function approveDocument(id: string): Promise<Document> {
  return post<Document>(`/documents/${id}/approve`);
}

export function regenerateDocument(id: string, feedback: string): Promise<Document> {
  return post<Document>(`/documents/${id}/regenerate`, { feedback });
}
