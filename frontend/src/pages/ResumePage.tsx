import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import {
  uploadResume,
  listResumes,
  addJob,
  listJobs,
  optimizeResume,
  scoreResume,
  type Resume,
  type JobDescription,
  type SuggestionResult,
  type ScoreResult,
} from "../api/resume";

export function ResumePage() {
  const [resumes, setResumes] = useState<Resume[]>([]);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [resumeText, setResumeText] = useState("");
  const [jobText, setJobText] = useState("");
  const [sourceUrl, setSourceUrl] = useState("");
  const [selectedResume, setSelectedResume] = useState("");
  const [selectedJob, setSelectedJob] = useState("");
  const [customJobText, setCustomJobText] = useState("");
  const [suggestion, setSuggestion] = useState<SuggestionResult | null>(null);
  const [score, setScore] = useState<ScoreResult | null>(null);
  const [submitting, setSubmitting] = useState("");
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const [r, j] = await Promise.all([listResumes(), listJobs()]);
      setResumes(r);
      setJobs(j);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
    }
  }

  useEffect(() => { load(); }, []);

  async function handleUploadResume() {
    if (!resumeText.trim()) return;
    setSubmitting("resume");
    setError("");
    try {
      await uploadResume(resumeText);
      setResumeText("");
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setSubmitting("");
    }
  }

  async function handleAddJob() {
    if (!jobText.trim()) return;
    setSubmitting("job");
    setError("");
    try {
      await addJob(jobText, sourceUrl);
      setJobText("");
      setSourceUrl("");
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Add job failed");
    } finally {
      setSubmitting("");
    }
  }

  async function handleOptimize() {
    const jobId = selectedJob;
    const jobText = customJobText.trim();
    if (!selectedResume || (!jobId && !jobText)) return;
    setSubmitting("optimize");
    setError("");
    setSuggestion(null);
    setScore(null);
    try {
      const [s, sc] = await Promise.all([
        optimizeResume(selectedResume, jobId, jobText),
        scoreResume(selectedResume, jobId, jobText),
      ]);
      setSuggestion(s);
      setScore(sc);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Optimization failed");
    } finally {
      setSubmitting("");
    }
  }

  return (
    <Layout>
      <h2 className="text-2xl font-bold mb-6">Resume Optimizer</h2>

      {error && (
        <p className="text-red-400 text-sm bg-red-900/30 px-3 py-2 rounded mb-4">{error}</p>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        <div className="bg-gray-800 rounded p-4 border border-gray-700">
          <h3 className="font-semibold mb-3">Upload Resume</h3>
          <textarea
            value={resumeText}
            onChange={(e) => setResumeText(e.target.value)}
            placeholder="Paste your resume text here..."
            rows={6}
            className="w-full px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm mb-3"
          />
          <button
            onClick={handleUploadResume}
            disabled={!resumeText.trim() || submitting === "resume"}
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm transition-colors"
          >
            {submitting === "resume" ? "Uploading..." : "Upload"}
          </button>
          {resumes.length > 0 && (
            <div className="mt-3 text-xs text-gray-400">
              {resumes.length} resume(s) saved
            </div>
          )}
        </div>

        <div className="bg-gray-800 rounded p-4 border border-gray-700">
          <h3 className="font-semibold mb-3">Add Job Description</h3>
          <textarea
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
            placeholder="Paste the job description here..."
            rows={4}
            className="w-full px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm mb-2"
          />
          <input
            type="text"
            value={sourceUrl}
            onChange={(e) => setSourceUrl(e.target.value)}
            placeholder="Source URL (optional)"
            className="w-full px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm mb-3"
          />
          <button
            onClick={handleAddJob}
            disabled={!jobText.trim() || submitting === "job"}
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm transition-colors"
          >
            {submitting === "job" ? "Adding..." : "Add Job"}
          </button>
          {jobs.length > 0 && (
            <div className="mt-3 text-xs text-gray-400">
              {jobs.length} job(s) saved
            </div>
          )}
        </div>
      </div>

      <div className="bg-gray-800 rounded p-4 border border-gray-700 mb-6">
        <h3 className="font-semibold mb-3">Optimize Resume</h3>
        <div className="flex flex-wrap gap-3 items-end">
          <div className="w-full">
            <label className="block text-xs text-gray-400 mb-1">Resume</label>
            <select
              value={selectedResume}
              onChange={(e) => setSelectedResume(e.target.value)}
              className="px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm min-w-[200px]"
            >
              <option value="">Select a resume...</option>
              {resumes.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.created_at.slice(0, 10)} — {r.raw_text.slice(0, 50)}...
                </option>
              ))}
            </select>
          </div>
          <div className="w-full">
            <label className="block text-xs text-gray-400 mb-1">Job Description</label>
            <textarea
              value={customJobText}
              onChange={(e) => { setCustomJobText(e.target.value); setSelectedJob(""); }}
              placeholder="Paste a job description directly..."
              rows={4}
              className="w-full px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm mb-2"
            />
            <div className="flex items-center gap-2 text-gray-500 text-xs mb-2">
              <span className="flex-1 h-px bg-gray-600" />
              <span>OR select a saved job</span>
              <span className="flex-1 h-px bg-gray-600" />
            </div>
            <select
              value={selectedJob}
              onChange={(e) => { setSelectedJob(e.target.value); setCustomJobText(""); }}
              className="px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm w-full"
            >
              <option value="">Select a saved job...</option>
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.created_at.slice(0, 10)} — {j.raw_text.slice(0, 50)}...
                </option>
              ))}
            </select>
          </div>
          <button
            onClick={handleOptimize}
            disabled={!selectedResume || (!selectedJob && !customJobText.trim()) || submitting === "optimize"}
            className="px-4 py-2 rounded bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-sm transition-colors"
          >
            {submitting === "optimize" ? "Analyzing..." : "Analyze Match"}
          </button>
        </div>
      </div>

      {score && (
        <div className="bg-gray-800 rounded p-4 border border-gray-700 mb-6">
          <h3 className="font-semibold mb-3">Match Score</h3>
          <div className="flex items-center gap-4 mb-3">
            <span className={`text-3xl font-bold ${
              score.score >= 70 ? "text-green-400" : score.score >= 40 ? "text-yellow-400" : "text-red-400"
            }`}>
              {score.score}/100
            </span>
            <p className="text-sm text-gray-400">{score.summary}</p>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-xs text-gray-500 uppercase mb-1">Strengths</h4>
              <ul className="text-sm text-green-400 list-disc list-inside">
                {score.strengths.map((s, i) => <li key={i}>{s}</li>)}
                {score.strengths.length === 0 && <li className="text-gray-500">None identified</li>}
              </ul>
            </div>
            <div>
              <h4 className="text-xs text-gray-500 uppercase mb-1">Gaps</h4>
              <ul className="text-sm text-red-400 list-disc list-inside">
                {score.gaps.map((g, i) => <li key={i}>{g}</li>)}
                {score.gaps.length === 0 && <li className="text-gray-500">None identified</li>}
              </ul>
            </div>
          </div>
        </div>
      )}

      {suggestion && (
        <div className="bg-gray-800 rounded p-4 border border-gray-700">
          <h3 className="font-semibold mb-3">Suggestions</h3>
          <pre className="text-sm text-gray-300 whitespace-pre-wrap bg-gray-900 rounded p-3 border border-gray-700 max-h-96 overflow-auto">
            {suggestion.suggestions}
          </pre>
        </div>
      )}
    </Layout>
  );
}
