import { get, post } from "./client";

export interface Week {
  week: number;
  focus: string;
  topics: string[];
  resources: string[];
  milestone: string;
}

export interface LearningPlan {
  id: string;
  title: string;
  goal: string;
  weeks: Week[];
  completed_items?: Array<{ week: number; topic: number }>;
  created_at: string;
}

export function generatePlan(goals = ""): Promise<LearningPlan> {
  const qs = goals ? `?goals=${encodeURIComponent(goals)}` : "";
  return post(`/learning-plan/generate${qs}`);
}

export function listPlans(): Promise<LearningPlan[]> {
  return get("/learning-plan");
}

export function getPlan(id: string): Promise<LearningPlan> {
  return get(`/learning-plan/${id}`);
}

export function updateItemStatus(
  planId: string,
  weekIndex: number,
  topicIndex: number,
  completed: boolean
): Promise<{ id: string; completed_items: Array<{ week: number; topic: number }> }> {
  return post(
    `/learning-plan/${planId}/items?week_index=${weekIndex}&topic_index=${topicIndex}&completed=${completed}`
  );
}
