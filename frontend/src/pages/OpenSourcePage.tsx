import { useEffect, useState, useCallback } from "react";
import { Layout } from "../components/Layout";
import {
  searchIssues,
  bookmarkIssue,
  dismissIssue,
  listBookmarked,
  type Issue,
  type BookmarkedIssue,
} from "../api/opensource";

export function OpenSourcePage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [bookmarked, setBookmarked] = useState<BookmarkedIssue[]>([]);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState("");

  const loadBookmarked = useCallback(async () => {
    try {
      const b = await listBookmarked();
      setBookmarked(b);
    } catch {
      // ignore
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      setLoading(true);
      try {
        const [results, b] = await Promise.all([
          searchIssues(),
          listBookmarked(),
        ]);
        setIssues(results);
        setBookmarked(b);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Load failed");
      } finally {
        setLoading(false);
      }
    };
    init();
  }, []);

  async function handleSearch() {
    setSearching(true);
    setError("");
    try {
      const results = await searchIssues(query);
      setIssues(results);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setSearching(false);
    }
  }

  async function handleBookmark(issue: Issue) {
    setError("");
    try {
      await bookmarkIssue({
        github_issue_id: issue.github_issue_id,
        repo_owner: issue.repo_owner,
        repo_name: issue.repo_name,
        issue_title: issue.issue_title,
        issue_url: issue.issue_url,
        labels: issue.labels,
        score: issue.score,
      });
      setIssues((prev) =>
        prev.map((i) =>
          i.github_issue_id === issue.github_issue_id ? { ...i, is_bookmarked: true } : i
        )
      );
      await loadBookmarked();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Bookmark failed");
    }
  }

  async function handleDismiss(issueId: string) {
    setError("");
    try {
      await dismissIssue(issueId);
      await loadBookmarked();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Dismiss failed");
    }
  }

  const [activeTab, setActiveTab] = useState("search");

  return (
    <Layout>
      <h2 className="text-2xl font-bold mb-6">Open Source Issue Finder</h2>

      {error && <p className="text-red-400 text-sm bg-red-900/30 px-3 py-2 rounded mb-4">{error}</p>}

      <div className="flex gap-2 mb-4">
        <button
          onClick={() => setActiveTab("search")}
          className={`px-3 py-1.5 rounded text-sm transition-colors ${
            activeTab === "search" ? "bg-blue-600 text-white" : "bg-gray-700 text-gray-300 hover:bg-gray-600"
          }`}
        >
          Search Issues
        </button>
        <button
          onClick={() => setActiveTab("bookmarked")}
          className={`px-3 py-1.5 rounded text-sm transition-colors ${
            activeTab === "bookmarked" ? "bg-blue-600 text-white" : "bg-gray-700 text-gray-300 hover:bg-gray-600"
          }`}
        >
          Bookmarked ({bookmarked.length})
        </button>
      </div>

      {activeTab === "search" && (
        <>
          <div className="bg-gray-800 rounded p-4 border border-gray-700 mb-4">
            <div className="flex gap-3 items-end">
              <div className="flex-1">
                <label className="block text-xs text-gray-400 mb-1">Search (optional)</label>
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="e.g., good first issue, help wanted, javascript"
                  className="w-full px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm"
                />
              </div>
              <button
                onClick={handleSearch}
                disabled={searching}
                className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm transition-colors shrink-0"
              >
                {searching ? "Searching..." : "Search"}
              </button>
            </div>
          </div>

          {loading ? (
            <p className="text-yellow-400 animate-pulse">Loading issues...</p>
          ) : issues.length === 0 ? (
            <p className="text-gray-500">No issues found. Try a broader search.</p>
          ) : (
            <div className="space-y-2">
              {issues.map((issue) => (
                <div
                  key={`${issue.repo_owner}/${issue.repo_name}#${issue.github_issue_id}`}
                  className="bg-gray-800 rounded p-3 border border-gray-700"
                >
                  <div className="flex items-start justify-between">
                    <div className="min-w-0 flex-1">
                      <a
                        href={issue.issue_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="font-medium text-sm text-blue-400 hover:text-blue-300 truncate block"
                      >
                        {issue.issue_title}
                      </a>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {issue.repo_owner}/{issue.repo_name} · #{issue.github_issue_id}
                      </p>
                      {issue.labels && (
                        <div className="flex flex-wrap gap-1 mt-1">
                          {issue.labels.split(", ").filter(Boolean).map((label) => (
                            <span key={label} className="px-1.5 py-0.5 rounded text-xs bg-gray-700 text-gray-300">
                              {label}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    {issue.is_bookmarked ? (
                      <span className="shrink-0 ml-2 text-xs text-green-400">bookmarked</span>
                    ) : (
                      <button
                        onClick={() => handleBookmark(issue)}
                        className="shrink-0 ml-2 px-2 py-1 rounded text-xs bg-gray-700 hover:bg-gray-600 transition-colors"
                      >
                        Bookmark
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {activeTab === "bookmarked" && (
        <div className="space-y-2">
          {bookmarked.length === 0 ? (
            <p className="text-gray-500">No bookmarked issues.</p>
          ) : (
            bookmarked.map((issue) => (
              <div key={issue.id} className="bg-gray-800 rounded p-3 border border-gray-700">
                <div className="flex items-start justify-between">
                  <div className="min-w-0 flex-1">
                    <a
                      href={issue.issue_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="font-medium text-sm text-blue-400 hover:text-blue-300 truncate block"
                    >
                      {issue.issue_title}
                    </a>
                    <p className="text-xs text-gray-500 mt-0.5">
                      {issue.repo_owner}/{issue.repo_name}
                    </p>
                    {issue.labels && (
                      <div className="flex flex-wrap gap-1 mt-1">
                        {issue.labels.split(", ").filter(Boolean).map((label) => (
                          <span key={label} className="px-1.5 py-0.5 rounded text-xs bg-gray-700 text-gray-300">
                            {label}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <button
                    onClick={() => handleDismiss(issue.id)}
                    className="shrink-0 ml-2 px-2 py-1 rounded text-xs bg-red-900/50 text-red-400 hover:bg-red-800 transition-colors"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      )}
    </Layout>
  );
}
