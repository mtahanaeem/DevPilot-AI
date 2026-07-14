import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import {
  getDashboard,
  generateWeeklyReport,
  listReports,
  type DashboardData,
  type WeeklyReport,
} from "../api/analytics";

export function AnalyticsPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [reports, setReports] = useState<WeeklyReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [latestReport, setLatestReport] = useState<WeeklyReport | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([getDashboard(), listReports()])
      .then(([d, r]) => {
        setData(d);
        setReports(r);
      })
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Load failed"))
      .finally(() => setLoading(false));
  }, []);

  async function handleGenerateReport() {
    setGenerating(true);
    setError("");
    try {
      const report = await generateWeeklyReport();
      setLatestReport(report);
      setReports((prev) => [report, ...prev]);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  if (loading) {
    return (
      <Layout>
        <p className="text-yellow-400 animate-pulse">Loading analytics...</p>
      </Layout>
    );
  }

  return (
    <Layout>
      <h2 className="text-2xl font-bold mb-6">Career Analytics</h2>

      {error && <p className="text-red-400 text-sm bg-red-900/30 px-3 py-2 rounded mb-4">{error}</p>}

      {data && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
            <div className="bg-gray-800 rounded p-4 border border-gray-700">
              <p className="text-xs text-gray-500 uppercase">Repos</p>
              <p className="text-2xl font-bold">{data.total_repos}</p>
            </div>
            <div className="bg-gray-800 rounded p-4 border border-gray-700">
              <p className="text-xs text-gray-500 uppercase">Stars</p>
              <p className="text-2xl font-bold text-yellow-400">{data.total_stars}</p>
            </div>
            <div className="bg-gray-800 rounded p-4 border border-gray-700">
              <p className="text-xs text-gray-500 uppercase">Forks</p>
              <p className="text-2xl font-bold text-blue-400">{data.total_forks}</p>
            </div>
            <div className="bg-gray-800 rounded p-4 border border-gray-700">
              <p className="text-xs text-gray-500 uppercase">Active (30d)</p>
              <p className="text-2xl font-bold text-green-400">{data.active_count}</p>
            </div>
            <div className="bg-gray-800 rounded p-4 border border-gray-700">
              <p className="text-xs text-gray-500 uppercase">Stale</p>
              <p className="text-2xl font-bold text-red-400">{data.stale_count}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-gray-800 rounded p-4 border border-gray-700">
              <h3 className="font-semibold mb-3">Language Distribution</h3>
              <div className="space-y-2">
                {data.language_distribution.map((l) => (
                  <div key={l.language} className="flex items-center gap-2">
                    <span className="text-sm w-28 truncate">{l.language}</span>
                    <div className="flex-1 bg-gray-700 rounded h-2">
                      <div
                        className="bg-blue-500 rounded h-2"
                        style={{ width: `${(l.count / Math.max(...data.language_distribution.map((x) => x.count))) * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-400 w-6 text-right">{l.count}</span>
                  </div>
                ))}
                {data.language_distribution.length === 0 && (
                  <p className="text-gray-500 text-sm">No language data</p>
                )}
              </div>
            </div>

            <div className="bg-gray-800 rounded p-4 border border-gray-700">
              <h3 className="font-semibold mb-3">Weekly Report</h3>
              <button
                onClick={handleGenerateReport}
                disabled={generating}
                className="px-4 py-2 rounded bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-sm transition-colors mb-3"
              >
                {generating ? "Generating..." : "Generate Weekly Report"}
              </button>

              {latestReport && (
                <div className="bg-gray-900 rounded p-3 border border-gray-700 text-sm space-y-2">
                  <p className="text-gray-200">{latestReport.summary}</p>
                  {latestReport.highlights.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase mt-2">Highlights</p>
                      <ul className="list-disc list-inside text-green-400">
                        {latestReport.highlights.map((h, i) => <li key={i}>{h}</li>)}
                      </ul>
                    </div>
                  )}
                  {latestReport.recommendations.length > 0 && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase mt-2">Recommendations</p>
                      <ul className="list-disc list-inside text-blue-400">
                        {latestReport.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>

          {reports.length > 0 && (
            <div className="bg-gray-800 rounded p-4 border border-gray-700">
              <h3 className="font-semibold mb-3">Past Reports</h3>
              <div className="space-y-2">
                {reports.map((r) => (
                  <div key={r.id} className="bg-gray-900 rounded p-3 border border-gray-700 text-sm">
                    <p className="text-xs text-gray-500">{r.created_at.slice(0, 10)}</p>
                    <p className="text-gray-300">{r.summary}</p>
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
