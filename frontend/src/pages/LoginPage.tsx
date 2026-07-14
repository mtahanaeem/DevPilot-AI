import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [pat, setPat] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(pat);
      navigate("/", { replace: true });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold">DevPilot AI</h1>
          <p className="text-gray-400 mt-1">GitHub Portfolio Growth Agent</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm text-gray-400 mb-1">
              GitHub Personal Access Token
            </label>
            <input
              type="password"
              value={pat}
              onChange={(e) => setPat(e.target.value)}
              placeholder="ghp_..."
              required
              className="w-full px-3 py-2 rounded bg-gray-800 border border-gray-700 focus:border-blue-500 focus:outline-none text-gray-100"
            />
          </div>

          {error && (
            <p className="text-red-400 text-sm bg-red-900/30 px-3 py-2 rounded">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 transition-colors font-medium"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="text-xs text-gray-500 text-center">
          Create a PAT at{" "}
          <a
            href="https://github.com/settings/tokens"
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 underline"
          >
            github.com/settings/tokens
          </a>{" "}
          with <code className="text-gray-400">repo</code> and{" "}
          <code className="text-gray-400">read:user</code> scopes.
        </p>
      </div>
    </div>
  );
}
