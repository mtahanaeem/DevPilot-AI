import { useEffect, useState, useCallback } from "react";
import { Layout } from "../components/Layout";
import {
  generateQuestions,
  submitAnswer,
  getModelAnswer,
  listSessions,
  getSession,
  type InterviewSession,
  type SessionSummary,
  type ModelAnswer,
} from "../api/interview";
import { listJobs, type JobDescription } from "../api/resume";

export function InterviewPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([]);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [selectedJob, setSelectedJob] = useState("");
  const [activeSession, setActiveSession] = useState<InterviewSession | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [currentQ, setCurrentQ] = useState(0);
  const [answer, setAnswer] = useState("");
  const [modelAnswer, setModelAnswer] = useState<ModelAnswer | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const [s, j] = await Promise.all([listSessions(), listJobs()]);
      setSessions(s);
      setJobs(j);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleGenerate() {
    if (!selectedJob) return;
    setGenerating(true);
    setError("");
    setModelAnswer(null);
    try {
      const session = await generateQuestions(selectedJob);
      setActiveSession(session);
      setSessions((prev) => [{
        id: session.id,
        job_description_id: session.job_description_id,
        question_count: session.questions.length,
        answer_count: 0,
        created_at: session.created_at,
      }, ...prev]);
      setCurrentQ(0);
      setAnswer("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  async function handleSubmitAnswer() {
    if (!activeSession || !answer.trim()) return;
    setError("");
    try {
      await submitAnswer(activeSession.id, activeSession.questions[currentQ].id, answer);
      setAnswer("");
      if (currentQ < activeSession.questions.length - 1) {
        setCurrentQ((prev) => prev + 1);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Submit failed");
    }
  }

  async function handleShowModelAnswer() {
    if (!activeSession) return;
    setError("");
    try {
      const ma = await getModelAnswer(activeSession.id, activeSession.questions[currentQ].id);
      setModelAnswer(ma);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load model answer");
    }
  }

  async function handleSelectSession(sessionId: string) {
    setError("");
    setModelAnswer(null);
    setAnswer("");
    setCurrentQ(0);
    try {
      const s = await getSession(sessionId);
      setActiveSession(s);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }

  return (
    <Layout>
      <h2 className="text-2xl font-bold mb-6">Interview Question Generator</h2>

      {error && <p className="text-red-400 text-sm bg-red-900/30 px-3 py-2 rounded mb-4">{error}</p>}

      <div className="bg-gray-800 rounded p-4 border border-gray-700 mb-6">
        <h3 className="font-semibold mb-3">Start New Interview Session</h3>
        <div className="flex gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Target Job</label>
            <select
              value={selectedJob}
              onChange={(e) => setSelectedJob(e.target.value)}
              className="px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm min-w-[250px]"
            >
              <option value="">Select a job...</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.created_at.slice(0, 10)} — {j.raw_text.slice(0, 60)}...
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleGenerate}
            disabled={!selectedJob || generating}
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm transition-colors"
          >
            {generating ? "Generating..." : "Generate Questions"}
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-yellow-400 animate-pulse">Loading...</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="space-y-2">
            <h3 className="font-semibold text-sm text-gray-400 uppercase">Sessions</h3>
            {sessions.length === 0 && <p className="text-gray-500 text-sm">No sessions yet.</p>}
            {sessions.map((s) => (
              <div
                key={s.id}
                onClick={() => handleSelectSession(s.id)}
                className={`bg-gray-800 rounded p-3 border cursor-pointer transition-colors ${
                  activeSession?.id === s.id ? "border-blue-500" : "border-gray-700 hover:border-gray-600"
                }`}
              >
                <p className="text-xs text-gray-500">{s.created_at.slice(0, 10)}</p>
                <p className="text-xs text-gray-400">{s.question_count} questions</p>
              </div>
            ))}
          </div>

          <div className="lg:col-span-2">
            {activeSession ? (
              <div className="bg-gray-800 rounded border border-gray-700 p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold">
                    Question {currentQ + 1} of {activeSession.questions.length}
                  </h3>
                  <span className="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-300">
                    {activeSession.questions[currentQ].difficulty} · {activeSession.questions[currentQ].category}
                  </span>
                </div>

                <p className="text-gray-200 mb-4">{activeSession.questions[currentQ].question}</p>

                <textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  placeholder="Type your answer..."
                  rows={4}
                  className="w-full px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm mb-3"
                />

                <div className="flex gap-2">
                  <button
                    onClick={handleSubmitAnswer}
                    disabled={!answer.trim()}
                    className="px-3 py-1.5 rounded bg-green-600 hover:bg-green-500 disabled:opacity-50 text-sm transition-colors"
                  >
                    {currentQ < activeSession.questions.length - 1 ? "Submit & Next" : "Submit Answer"}
                  </button>
                  <button
                    onClick={handleShowModelAnswer}
                    className="px-3 py-1.5 rounded bg-yellow-600 hover:bg-yellow-500 text-sm transition-colors"
                  >
                    Show Model Answer
                  </button>
                </div>

                {modelAnswer && (
                  <div className="mt-4 bg-gray-900 rounded p-3 border border-gray-700">
                    <h4 className="text-sm font-semibold text-blue-400 mb-2">Model Answer</h4>
                    <pre className="text-sm text-gray-300 whitespace-pre-wrap">{modelAnswer.model_answer}</pre>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-12">Generate questions or select a session</p>
            )}
          </div>
        </div>
      )}
    </Layout>
  );
}
