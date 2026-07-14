import { get, post } from "./client";

export interface Question {
  id: number;
  category: string;
  question: string;
  difficulty: string;
}

export interface InterviewSession {
  id: string;
  job_description_id: string;
  questions: Question[];
  created_at: string;
}

export interface SessionSummary {
  id: string;
  job_description_id: string;
  question_count: number;
  answer_count: number;
  created_at: string;
}

export interface ModelAnswer {
  session_id: string;
  question_id: number;
  question: string;
  model_answer: string;
}

export function generateQuestions(jobId: string): Promise<InterviewSession> {
  return post(`/interview/generate/${jobId}`);
}

export function submitAnswer(
  sessionId: string,
  questionId: number,
  answer: string
): Promise<{ session_id: string; question_id: number; status: string }> {
  return post(
    `/interview/${sessionId}/answer?question_id=${questionId}&answer=${encodeURIComponent(answer)}`
  );
}

export function getModelAnswer(
  sessionId: string,
  questionId: number
): Promise<ModelAnswer> {
  return get(`/interview/${sessionId}/model-answer?question_id=${questionId}`);
}

export function listSessions(): Promise<SessionSummary[]> {
  return get("/interview");
}

export function getSession(sessionId: string): Promise<InterviewSession> {
  return get(`/interview/${sessionId}`);
}
