import { useEffect, useState } from "react";
import { Layout } from "../components/Layout";
import {
  listNotifications,
  markRead,
  markAllRead,
  type Notification,
} from "../api/notifications";

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const n = await listNotifications();
      setNotifications(n);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  async function handleMarkRead(id: string) {
    try {
      await markRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, status: "sent" } : n))
      );
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to mark read");
    }
  }

  async function handleMarkAllRead() {
    try {
      await markAllRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, status: "sent" })));
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to mark all read");
    }
  }

  const pendingCount = notifications.filter((n) => n.status === "pending").length;

  return (
    <Layout>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold">Notifications</h2>
        {pendingCount > 0 && (
          <button
            onClick={handleMarkAllRead}
            className="px-3 py-1.5 rounded bg-blue-600 hover:bg-blue-500 text-sm transition-colors"
          >
            Mark All Read ({pendingCount})
          </button>
        )}
      </div>

      {error && <p className="text-red-400 text-sm bg-red-900/30 px-3 py-2 rounded mb-4">{error}</p>}

      {loading ? (
        <p className="text-yellow-400 animate-pulse">Loading notifications...</p>
      ) : notifications.length === 0 ? (
        <p className="text-gray-500">No notifications yet.</p>
      ) : (
        <div className="space-y-2">
          {notifications.map((n) => (
            <div
              key={n.id}
              className={`bg-gray-800 rounded p-4 border transition-colors ${
                n.status === "pending" ? "border-blue-600" : "border-gray-700"
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      n.status === "pending"
                        ? "bg-blue-900/50 text-blue-300"
                        : "bg-gray-700 text-gray-400"
                    }`}>
                      {n.status}
                    </span>
                    <span className="text-xs text-gray-500">{n.event_type}</span>
                    <span className="text-xs text-gray-500">{n.channel}</span>
                  </div>
                  <p className="text-xs text-gray-500">{n.created_at.slice(0, 10)}</p>
                </div>
                {n.status === "pending" && (
                  <button
                    onClick={() => handleMarkRead(n.id)}
                    className="text-xs px-2 py-1 rounded bg-green-700 hover:bg-green-600 transition-colors shrink-0"
                  >
                    Mark Read
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </Layout>
  );
}
