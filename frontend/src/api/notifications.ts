import { get, post } from "./client";

export interface Notification {
  id: string;
  event_type: string;
  channel: string;
  sent_at: string | null;
  status: string;
  created_at: string;
}

export function listNotifications(): Promise<Notification[]> {
  return get("/notifications");
}

export function markRead(id: string): Promise<{ id: string; status: string }> {
  return post(`/notifications/${id}/read`);
}

export function markAllRead(): Promise<{ updated: number }> {
  return post("/notifications/mark-all-read");
}
