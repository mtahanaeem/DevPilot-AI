import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import { get } from "../api/client";
import { listDocuments } from "../api/documents";
import { listPosts } from "../api/social";

export function DashboardPage() {
  const [repoCount, setRepoCount] = useState<number | null>(null);
  const [docCount, setDocCount] = useState<number>(0);
  const [postCount, setPostCount] = useState<number>(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [repos, docs, posts] = await Promise.all([
          get<unknown[]>("/repositories"),
          listDocuments(),
          listPosts(),
        ]);
        setRepoCount(repos.length);
        setDocCount(docs.length);
        setPostCount(posts.length);
      } catch {
        // silently fail on stats
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const stats = [
    { label: "Repositories", value: repoCount ?? "-" },
    { label: "Documents Generated", value: docCount },
    { label: "Social Posts", value: postCount },
  ];

  return (
    <Layout>
      <h2 className="text-2xl font-bold mb-6">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        {stats.map((s) => (
          <div key={s.label} className="bg-gray-800 rounded p-4 border border-gray-700">
            <p className="text-gray-400 text-sm">{s.label}</p>
            <p className="text-2xl font-semibold mt-1">
              {loading ? (
                <span className="text-gray-600 animate-pulse">...</span>
              ) : (
                s.value
              )}
            </p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <a
          href="/repositories"
          className="block bg-gray-800 rounded p-4 border border-gray-700 hover:border-blue-500 transition-colors"
        >
          <h3 className="font-semibold text-lg">Repositories</h3>
          <p className="text-sm text-gray-400 mt-1">
            Sync repos, flag stale ones, and manage your portfolio.
          </p>
        </a>
        <a
          href="/documents"
          className="block bg-gray-800 rounded p-4 border border-gray-700 hover:border-blue-500 transition-colors"
        >
          <h3 className="font-semibold text-lg">AI Documents</h3>
          <p className="text-sm text-gray-400 mt-1">
            Generate, review, and commit READMEs and docs.
          </p>
        </a>
        <a
          href="/resume"
          className="block bg-gray-800 rounded p-4 border border-gray-700 hover:border-blue-500 transition-colors"
        >
          <h3 className="font-semibold text-lg">Resume Optimizer</h3>
          <p className="text-sm text-gray-400 mt-1">
            Upload your resume, paste job descriptions, get AI suggestions.
          </p>
        </a>
        <a
          href="/social"
          className="block bg-gray-800 rounded p-4 border border-gray-700 hover:border-blue-500 transition-colors"
        >
          <h3 className="font-semibold text-lg">Social Posts</h3>
          <p className="text-sm text-gray-400 mt-1">
            Generate LinkedIn/Twitter posts for your repos.
          </p>
        </a>
      </div>
    </Layout>
  );
}
