import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import { get, post } from "../api/client";

interface Repo {
  id: string;
  name: string;
  description: string | null;
  stars: number;
  forks: number;
  language_stats: Record<string, number>;
  last_commit_at: string | null;
  is_stale: boolean;
}

export function RepositoriesPage() {
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState("");

  async function fetchRepos() {
    setError("");
    try {
      const data = await get<Repo[]>("/repositories");
      setRepos(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load repos");
    } finally {
      setLoading(false);
    }
  }

  async function handleSync() {
    setSyncing(true);
    setError("");
    try {
      const data = await post<{ repos: Repo[] }>("/repositories/sync");
      setRepos(data.repos);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Sync failed");
    } finally {
      setSyncing(false);
    }
  }

  useEffect(() => {
    fetchRepos();
  }, []);

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Repositories</h2>
        <button
          onClick={handleSync}
          disabled={syncing}
          className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 transition-colors text-sm font-medium"
        >
          {syncing ? "Syncing..." : "Sync from GitHub"}
        </button>
      </div>

      {error && (
        <p className="text-red-400 text-sm bg-red-900/30 px-3 py-2 rounded mb-4">
          {error}
        </p>
      )}

      {loading && (
        <p className="text-yellow-400 animate-pulse">Loading repositories...</p>
      )}

      <div className="space-y-3">
        {!loading && repos.length === 0 && (
          <p className="text-gray-500">
            No repositories yet. Click "Sync from GitHub" to import them.
          </p>
        )}
        {repos.map((repo) => (
          <div
            key={repo.id}
            className="bg-gray-800 rounded p-4 border border-gray-700 flex items-start justify-between"
          >
            <div className="min-w-0 flex-1">
              <h3 className="font-semibold truncate">{repo.name}</h3>
              {repo.description && (
                <p className="text-sm text-gray-400 mt-1 line-clamp-2">
                  {repo.description}
                </p>
              )}
              <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                <span>★ {repo.stars}</span>
                <span>⑂ {repo.forks}</span>
                {repo.last_commit_at && (
                  <span>
                    Last commit: {new Date(repo.last_commit_at).toLocaleDateString()}
                  </span>
                )}
              </div>
            </div>
            {repo.is_stale && (
              <span className="shrink-0 ml-3 px-2 py-0.5 rounded text-xs bg-yellow-900/50 text-yellow-400 border border-yellow-700">
                stale
              </span>
            )}
          </div>
        ))}
      </div>
    </Layout>
  );
}
