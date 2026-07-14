import { useEffect, useState, useCallback } from "react";
import { Layout } from "../components/Layout";
import {
  listDocuments,
  generateDocument,
  approveDocument,
  regenerateDocument,
  type Document,
} from "../api/documents";
import { get } from "../api/client";

interface Repo {
  id: string;
  name: string;
}

export function DocumentsPage() {
  const [docs, setDocs] = useState<Document[]>([]);
  const [repos, setRepos] = useState<Repo[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedDoc, setSelectedDoc] = useState<Document | null>(null);
  const [generateRepo, setGenerateRepo] = useState("");
  const [generateType, setGenerateType] = useState("readme");
  const [feedback, setFeedback] = useState("");
  const [submitting, setSubmitting] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const [d, r] = await Promise.all([
        listDocuments(),
        get<Repo[]>("/repositories"),
      ]);
      setDocs(d);
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
      await generateDocument(generateRepo, generateType);
      setGenerateRepo("");
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setSubmitting("");
    }
  }

  async function handleApprove(docId: string) {
    setSubmitting(docId);
    setError("");
    try {
      const updated = await approveDocument(docId);
      setDocs((prev) => prev.map((d) => (d.id === docId ? updated : d)));
      if (selectedDoc?.id === docId) setSelectedDoc(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Approval failed");
    } finally {
      setSubmitting("");
    }
  }

  async function handleRegenerate(docId: string) {
    if (!feedback.trim()) return;
    setSubmitting(docId);
    setError("");
    try {
      const updated = await regenerateDocument(docId, feedback);
      setDocs((prev) => prev.map((d) => (d.id === docId ? updated : d)));
      if (selectedDoc?.id === docId) setSelectedDoc(updated);
      setFeedback("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Regeneration failed");
    } finally {
      setSubmitting("");
    }
  }

  const statusBadge = (status: string) => {
    const colors: Record<string, string> = {
      draft: "bg-yellow-900/50 text-yellow-400 border-yellow-700",
      approved: "bg-blue-900/50 text-blue-400 border-blue-700",
      committed: "bg-green-900/50 text-green-400 border-green-700",
    };
    return `px-2 py-0.5 rounded text-xs border ${colors[status] || "bg-gray-700 text-gray-400 border-gray-600"}`;
  };

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">AI Documents</h2>
      </div>

      {error && (
        <p className="text-red-400 text-sm bg-red-900/30 px-3 py-2 rounded mb-4">{error}</p>
      )}

      <div className="bg-gray-800 rounded p-4 border border-gray-700 mb-6">
        <h3 className="font-semibold mb-3">Generate New Document</h3>
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
            <label className="block text-xs text-gray-400 mb-1">Type</label>
            <select
              value={generateType}
              onChange={(e) => setGenerateType(e.target.value)}
              className="px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm"
            >
              <option value="readme">README.md</option>
              <option value="contributing">CONTRIBUTING.md</option>
              <option value="architecture">ARCHITECTURE.md</option>
            </select>
          </div>
          <button
            onClick={handleGenerate}
            disabled={!generateRepo || submitting === "generate"}
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm font-medium transition-colors"
          >
            {submitting === "generate" ? "Generating..." : "Generate"}
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-yellow-400 animate-pulse">Loading documents...</p>
      ) : docs.length === 0 ? (
        <p className="text-gray-500">No documents yet. Generate one above.</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="space-y-2">
            {docs.map((doc) => (
              <div
                key={doc.id}
                onClick={() => setSelectedDoc(doc)}
                className={`bg-gray-800 rounded p-3 border cursor-pointer transition-colors ${
                  selectedDoc?.id === doc.id
                    ? "border-blue-500"
                    : "border-gray-700 hover:border-gray-600"
                }`}
              >
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm truncate">{doc.type.toUpperCase()}</span>
                  <span className={statusBadge(doc.status)}>{doc.status}</span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  {doc.created_at.slice(0, 10)}
                </p>
              </div>
            ))}
          </div>

          <div>
            {selectedDoc ? (
              <div className="bg-gray-800 rounded border border-gray-700 p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold">{selectedDoc.type.toUpperCase()}</h3>
                  <span className={statusBadge(selectedDoc.status)}>{selectedDoc.status}</span>
                </div>
                <pre className="text-sm text-gray-300 whitespace-pre-wrap max-h-96 overflow-auto bg-gray-900 rounded p-3 border border-gray-700">
                  {selectedDoc.content}
                </pre>
                <div className="flex items-center gap-3 mt-4">
                  {selectedDoc.status === "draft" && (
                    <button
                      onClick={() => handleApprove(selectedDoc.id)}
                      disabled={submitting === selectedDoc.id}
                      className="px-3 py-1.5 rounded bg-green-600 hover:bg-green-500 disabled:opacity-50 text-sm transition-colors"
                    >
                      {submitting === selectedDoc.id ? "..." : "Approve & Commit"}
                    </button>
                  )}
                  <input
                    type="text"
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    placeholder="Feedback for regeneration..."
                    className="flex-1 px-3 py-1.5 rounded bg-gray-700 border border-gray-600 text-sm"
                  />
                  <button
                    onClick={() => handleRegenerate(selectedDoc.id)}
                    disabled={!feedback.trim() || submitting === selectedDoc.id}
                    className="px-3 py-1.5 rounded bg-yellow-600 hover:bg-yellow-500 disabled:opacity-50 text-sm transition-colors"
                  >
                    Regenerate
                  </button>
                </div>
              </div>
            ) : (
              <p className="text-gray-500 text-center py-12">
                Select a document to preview
              </p>
            )}
          </div>
        </div>
      )}
    </Layout>
  );
}
