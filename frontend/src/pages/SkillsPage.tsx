import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import {
  inferSkills,
  analyzeGaps,
  listReports,
  type GapAnalysis,
} from "../api/skills";
import { listJobs, addJob, type JobDescription } from "../api/resume";

export function SkillsPage() {
  const [skills, setSkills] = useState<string[]>([]);
  const [jobs, setJobs] = useState<JobDescription[]>([]);
  const [reports, setReports] = useState<GapAnalysis[]>([]);
  const [selectedJob, setSelectedJob] = useState("");
  const [jobText, setJobText] = useState("");
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [result, setResult] = useState<GapAnalysis | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([inferSkills(), listJobs(), listReports()])
      .then(([s, j, r]) => {
        setSkills(s.skills);
        setJobs(j);
        setReports(r);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Load failed"))
      .finally(() => setLoading(false));
  }, []);

  async function handleAnalyze() {
    setAnalyzing(true);
    setError("");
    setResult(null);
    try {
      let jobId = selectedJob;
      if (jobText.trim()) {
        const saved = await addJob(jobText.trim());
        jobId = saved.id;
        setJobs((prev) => [saved, ...prev]);
        setJobText("");
      }
      if (!jobId) return;
      const res = await analyzeGaps(jobId);
      setResult(res);
      setReports((prev) => [res, ...prev]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Analysis failed");
    } finally {
      setAnalyzing(false);
    }
  }

  return (
    <Layout>
      <h2 className="text-2xl font-bold mb-6">Skill Gap Analyzer</h2>

      {error && <p className="text-red-400 text-sm bg-red-900/30 px-3 py-2 rounded mb-4">{error}</p>}

      {loading ? (
        <p className="text-yellow-400 animate-pulse">Loading skills...</p>
      ) : (
        <>
          <div className="bg-gray-800 rounded p-4 border border-gray-700 mb-6">
            <h3 className="font-semibold mb-2">Your Inferred Skills</h3>
            <div className="flex flex-wrap gap-2">
              {skills.map((s) => (
                <span key={s} className="px-2 py-1 rounded text-xs bg-blue-900/50 text-blue-300 border border-blue-700">
                  {s}
                </span>
              ))}
            </div>
          </div>

          <div className="bg-gray-800 rounded p-4 border border-gray-700 mb-6">
            <h3 className="font-semibold mb-3">Analyze Against Job Description</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-xs text-gray-400 mb-1">Paste a job description</label>
                <textarea
                  value={jobText}
                  onChange={(e) => setJobText(e.target.value)}
                  placeholder="Paste a job description to analyze against your skills..."
                  rows={4}
                  className="w-full px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm"
                />
              </div>
              <div className="flex items-center gap-2 text-xs text-gray-500">
                <span className="border-t border-gray-600 flex-1" />
                <span>OR select a saved job</span>
                <span className="border-t border-gray-600 flex-1" />
              </div>
              <div className="flex gap-3 items-end">
                <div className="flex-1">
                  <label className="block text-xs text-gray-400 mb-1">Saved Jobs</label>
                  <select
                    value={selectedJob}
                    onChange={(e) => setSelectedJob(e.target.value)}
                    className="w-full px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm"
                  >
                    <option value="">Select a job...</option>
                    {jobs.map((j) => (
                      <option key={j.id} value={j.id}>
                        {j.raw_text.slice(0, 80)}...
                      </option>
                    ))}
                  </select>
                </div>
                <button
                  onClick={handleAnalyze}
                  disabled={(!selectedJob && !jobText.trim()) || analyzing}
                  className="px-4 py-2 rounded bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-sm transition-colors shrink-0"
                >
                  {analyzing ? "Analyzing..." : "Analyze Gaps"}
                </button>
              </div>
            </div>
          </div>

          {result && (
            <div className="bg-gray-800 rounded p-4 border border-gray-700 mb-6">
              <h3 className="font-semibold mb-3">Analysis Result</h3>
              <div className="flex items-center gap-3 mb-3">
                <span className={`text-2xl font-bold ${result.overall_match >= 70 ? "text-green-400" : result.overall_match >= 40 ? "text-yellow-400" : "text-red-400"}`}>
                  {result.overall_match}% Match
                </span>
              </div>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <h4 className="text-xs text-gray-500 uppercase mb-1">Matching Skills</h4>
                  <div className="flex flex-wrap gap-1">
                    {result.present_skills.map((s) => (
                      <span key={s} className="px-2 py-0.5 rounded text-xs bg-green-900/50 text-green-300 border border-green-700">{s}</span>
                    ))}
                  </div>
                </div>
                <div>
                  <h4 className="text-xs text-gray-500 uppercase mb-1">Gaps</h4>
                  <ul className="text-sm text-red-400 list-disc list-inside">
                    {result.gaps.map((g, i) => <li key={i}>{g}</li>)}
                  </ul>
                </div>
              </div>
              <div>
                <h4 className="text-xs text-gray-500 uppercase mb-1">Recommendations</h4>
                <ul className="text-sm text-gray-300 list-disc list-inside">
                  {result.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            </div>
          )}

          {reports.length > 0 && (
            <div className="bg-gray-800 rounded p-4 border border-gray-700">
              <h3 className="font-semibold mb-3">Past Reports</h3>
              <div className="space-y-2">
                {reports.map((r) => (
                  <div key={r.id} className="bg-gray-900 rounded p-3 border border-gray-700 text-sm">
                    <p className="text-gray-400">{r.created_at.slice(0, 10)} — <span className={r.overall_match >= 70 ? "text-green-400" : "text-yellow-400"}>{r.overall_match}% match</span></p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      )}
    </Layout>
  );
}
