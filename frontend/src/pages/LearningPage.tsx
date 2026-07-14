import { useEffect, useState, useCallback } from "react";
import { Layout } from "../components/Layout";
import {
  generatePlan,
  listPlans,
  getPlan,
  updateItemStatus,
  type LearningPlan,
} from "../api/learning";

export function LearningPage() {
  const [plans, setPlans] = useState<LearningPlan[]>([]);
  const [selectedPlan, setSelectedPlan] = useState<LearningPlan | null>(null);
  const [goals, setGoals] = useState("");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setError("");
    try {
      const p = await listPlans();
      setPlans(p);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleGenerate() {
    setGenerating(true);
    setError("");
    try {
      const plan = await generatePlan(goals);
      setPlans((prev) => [plan, ...prev]);
      setSelectedPlan(plan);
      setGoals("");
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Generation failed");
    } finally {
      setGenerating(false);
    }
  }

  async function handleSelect(planId: string) {
    setError("");
    try {
      const plan = await getPlan(planId);
      setSelectedPlan(plan);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Load failed");
    }
  }

  async function toggleTopic(weekIdx: number, topicIdx: number, currentlyCompleted: boolean) {
    if (!selectedPlan) return;
    setError("");
    try {
      await updateItemStatus(selectedPlan.id, weekIdx, topicIdx, !currentlyCompleted);
      const updated = await getPlan(selectedPlan.id);
      setSelectedPlan(updated);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Update failed");
    }
  }

  const isCompleted = (plan: LearningPlan, weekIdx: number, topicIdx: number) => {
    return (plan.completed_items || []).some(
      (c) => c.week === weekIdx && c.topic === topicIdx
    );
  };

  return (
    <Layout>
      <h2 className="text-2xl font-bold mb-6">Learning Planner</h2>

      {error && <p className="text-red-400 text-sm bg-red-900/30 px-3 py-2 rounded mb-4">{error}</p>}

      <div className="bg-gray-800 rounded p-4 border border-gray-700 mb-6">
        <h3 className="font-semibold mb-3">Generate New Plan</h3>
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="block text-xs text-gray-400 mb-1">Goals / Context (optional)</label>
            <input
              type="text"
              value={goals}
              onChange={(e) => setGoals(e.target.value)}
              placeholder="e.g., Want to learn TypeScript and React"
              className="w-full px-3 py-2 rounded bg-gray-700 border border-gray-600 text-sm"
            />
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="px-4 py-2 rounded bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-sm transition-colors shrink-0"
          >
            {generating ? "Generating..." : "Generate Plan"}
          </button>
        </div>
      </div>

      {loading ? (
        <p className="text-yellow-400 animate-pulse">Loading plans...</p>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="space-y-2">
            <h3 className="font-semibold text-sm text-gray-400 uppercase">Plans</h3>
            {plans.length === 0 && <p className="text-gray-500 text-sm">No plans yet.</p>}
            {plans.map((p) => (
              <div
                key={p.id}
                onClick={() => handleSelect(p.id)}
                className={`bg-gray-800 rounded p-3 border cursor-pointer transition-colors ${
                  selectedPlan?.id === p.id ? "border-blue-500" : "border-gray-700 hover:border-gray-600"
                }`}
              >
                <p className="font-medium text-sm">{p.title}</p>
                <p className="text-xs text-gray-500">{p.created_at.slice(0, 10)}</p>
              </div>
            ))}
          </div>

          <div className="lg:col-span-2">
            {selectedPlan ? (
              <div className="bg-gray-800 rounded border border-gray-700 p-4">
                <h3 className="text-lg font-semibold mb-1">{selectedPlan.title}</h3>
                <p className="text-sm text-gray-400 mb-4">{selectedPlan.goal}</p>

                {selectedPlan.weeks.map((week) => (
                  <div key={week.week} className="mb-4 bg-gray-900 rounded p-3 border border-gray-700">
                    <h4 className="font-semibold text-sm text-blue-400">
                      Week {week.week}: {week.focus}
                    </h4>
                    <p className="text-xs text-gray-500 mt-1">{week.milestone}</p>
                    <ul className="mt-2 space-y-1">
                      {week.topics.map((topic, tIdx) => {
                        const done = isCompleted(selectedPlan, week.week - 1, tIdx);
                        return (
                          <li key={tIdx} className="flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={done}
                              onChange={() => toggleTopic(week.week - 1, tIdx, done)}
                              className="accent-blue-500"
                            />
                            <span className={done ? "line-through text-gray-500" : ""}>{topic}</span>
                          </li>
                        );
                      })}
                    </ul>
                    {week.resources.length > 0 && (
                      <div className="mt-2 text-xs text-gray-500">
                        <span className="text-gray-400">Resources:</span> {week.resources.join(", ")}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 text-center py-12">Select a plan to view details</p>
            )}
          </div>
        </div>
      )}
    </Layout>
  );
}
