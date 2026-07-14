import { useEffect, useState, useCallback } from "react";
import { Layout } from "../components/Layout";
import {
  generatePost,
  listPosts,
  approvePost,
  type SocialPost,
} from "../api/social";
import { get } from "../api/client";

interface Repo {
  id: string;
  name: string;
}

export function SocialPage() {
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [generateRepo, setGenerateRepo] = useState("");
  const [platform, setPlatform] = useState("linkedin");
  const [tone, setTone] = useState("professional");
  const [submitting, setSubmitting] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const [p, r] = await Promise.all([
        listPosts(),
        get<Repo[]>("/repositories"),
      ]);
      setPosts(p);
      setRepos(r);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleGenerate() {
    if (!generateRepo) return;
    setSubmitting("generate");
    setError("");
    try {
      await generatePost(generateRepo, platform, tone);
      setGenerateRepo("");
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setSubmitting("");
    }
  }

  async function handleApprove(postId: string) {
    setSubmitting(postId);
    setError("");
    try {
      await approvePost(postId);
      setPosts((prev) =>
        prev.map((p) => (p.id === postId ? { ...p, status: "approved" } : p))
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setSubmitting("");
    }
  }

  const platformIcon = (p: string) =>
    p === "linkedin" ? "in" : p === "twitter" || p === "x" ? "𝕏" : p;

  return (
    <Layout>
      <h2 className="text-2xl font-bold mb-6">Social Posts</h2>

      {error && (
        <p className="text-red-400 text-sm bg-red-900/30 px-3 py-2 rounded mb-4">{error}</p>
      )}

      <div className="bg-gray-800 rounded p-4 border border-gray-700 mb-6">
        <h3 className="font-semibold mb-3">Generate New Post</h3>
        <div className="flex flex-wrap gap-3 items-end">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Repository</label>
            <select
              value={generateRepo}
              onChange={(e) => setGenerateRepo(e.target.value)}
              className="px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm min-w-[200px]"
            >
              <option value="">Select a repo...</option>
              {repos.map((r) => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Platform</label>
            <select
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm"
            >
              <option value="linkedin">LinkedIn</option>
              <option value="twitter">Twitter / X</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Tone</label>
            <select
              value={tone}
              onChange={(e) => setTone(e.target.value)}
              className="px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm"
            >
              <option value="professional">Professional</option>
              <option value="casual">Casual</option>
              <option value="technical">Technical</option>
            </select>
          </div>
          <button
            onClick={handleGenerate}
            disabled={!generateRepo || submitting === "generate"}
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm transition-colors"
          >
            {submitting === "generate" ? "Generating..." : "Generate"}
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-yellow-400 animate-pulse">Loading posts...</p>
      ) : posts.length === 0 ? (
        <p className="text-gray-500">No posts yet. Generate one above.</p>
      ) : (
        <div className="space-y-3">
          {posts.map((post) => (
            <div key={post.id} className="bg-gray-800 rounded p-4 border border-gray-700">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs bg-gray-700 px-2 py-0.5 rounded">
                    {platformIcon(post.platform)}
                  </span>
                  <span className="text-xs text-gray-500">{post.created_at.slice(0, 10)}</span>
                </div>
                {post.status === "draft" ? (
                  <button
                    onClick={() => handleApprove(post.id)}
                    disabled={submitting === post.id}
                    className="px-3 py-1 rounded bg-green-600 hover:bg-green-500 disabled:opacity-50 text-xs transition-colors"
                  >
                    {submitting === post.id ? "..." : "Approve"}
                  </button>
                ) : (
                  <span className="px-2 py-0.5 rounded text-xs border bg-green-900/50 text-green-400 border-green-700">
                    approved
                  </span>
                )}
              </div>
              <pre className="text-sm text-gray-300 whitespace-pre-wrap bg-gray-900 rounded p-3 border border-gray-700 max-h-48 overflow-auto">
                {post.content}
              </pre>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
