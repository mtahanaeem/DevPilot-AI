import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import { get } from "../api/client";

interface PortfolioSummary {
  total_repos: number;
  total_stars: number;
  total_forks: number;
  top_language: string;
  languages: Record<string, number>;
  stale_repos: number;
}

interface PortfolioItem {
  id: string;
  name: string;
  owner: string;
  description: string;
  language_stats: Record<string, number>;
  stars: number;
  forks: number;
  last_commit_at: string | null;
  is_stale: boolean;
}

interface Portfolio {
  generated_at: string;
  summary: PortfolioSummary;
  repositories: PortfolioItem[];
}

export function PortfolioPage() {
  const [portfolio, setPortfolio] = useState<Portfolio | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    get<Portfolio>("/portfolio")
      .then(setPortfolio)
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Portfolio</h2>
        <div className="flex gap-2">
          <a
            href="/api/portfolio/export?fmt=json"
            target="_blank"
            className="px-3 py-1.5 rounded bg-gray-700 hover:bg-gray-600 text-sm transition-colors"
          >
            JSON
          </a>
          <a
            href="/api/portfolio/export?fmt=markdown"
            target="_blank"
            className="px-3 py-1.5 rounded bg-gray-700 hover:bg-gray-600 text-sm transition-colors"
          >
            Markdown
          </a>
          <a
            href="/api/portfolio/export?fmt=html"
            target="_blank"
            className="px-3 py-1.5 rounded bg-gray-700 hover:bg-gray-600 text-sm transition-colors"
          >
            HTML
          </a>
        </div>
      </div>

      {error && (
        <p className="text-red-400 text-sm bg-red-900/30 px-3 py-2 rounded mb-4">{error}</p>
      )}

      {loading ? (
        <p className="text-yellow-400 animate-pulse">Loading portfolio...</p>
      ) : portfolio ? (
        <>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
            <div className="bg-gray-800 rounded p-3 border border-gray-700 text-center">
              <p className="text-xs text-gray-400">Repos</p>
              <p className="text-xl font-semibold">{portfolio.summary.total_repos}</p>
            </div>
            <div className="bg-gray-800 rounded p-3 border border-gray-700 text-center">
              <p className="text-xs text-gray-400">Stars</p>
              <p className="text-xl font-semibold">{portfolio.summary.total_stars}</p>
            </div>
            <div className="bg-gray-800 rounded p-3 border border-gray-700 text-center">
              <p className="text-xs text-gray-400">Forks</p>
              <p className="text-xl font-semibold">{portfolio.summary.total_forks}</p>
            </div>
            <div className="bg-gray-800 rounded p-3 border border-gray-700 text-center">
              <p className="text-xs text-gray-400">Top Language</p>
              <p className="text-xl font-semibold">{portfolio.summary.top_language}</p>
            </div>
            <div className="bg-gray-800 rounded p-3 border border-gray-700 text-center">
              <p className="text-xs text-gray-400">Stale</p>
              <p className="text-xl font-semibold text-yellow-400">{portfolio.summary.stale_repos}</p>
            </div>
          </div>

          <div className="space-y-2">
            {portfolio.repositories.map((repo) => (
              <div key={repo.id} className="bg-gray-800 rounded p-3 border border-gray-700 flex items-start justify-between">
                <div>
                  <h3 className="font-semibold">{repo.name}</h3>
                  {repo.description && (
                    <p className="text-sm text-gray-400 mt-0.5">{repo.description}</p>
                  )}
                  <p className="text-xs text-gray-500 mt-1">
                    ★ {repo.stars} | ⑂ {repo.forks}
                  </p>
                </div>
                {repo.is_stale && (
                  <span className="shrink-0 ml-3 px-2 py-0.5 rounded text-xs bg-yellow-900/50 text-yellow-400 border border-yellow-700">
                    stale
                  </span>
                )}
              </div>
            ))}
          </div>
        </>
      ) : null}
    </Layout>
  );
}
