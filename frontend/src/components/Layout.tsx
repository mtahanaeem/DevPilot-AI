import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const navItems = [
  { path: "/", label: "Dashboard" },
  { path: "/repositories", label: "Repositories" },
  { path: "/analytics", label: "Analytics" },
  { path: "/documents", label: "AI Documents" },
  { path: "/portfolio", label: "Portfolio" },
  { path: "/resume", label: "Resume" },
  { path: "/social", label: "Social Posts" },
  { path: "/skills", label: "Skill Gaps" },
  { path: "/learning", label: "Learning" },
  { path: "/interview", label: "Interview" },
  { path: "/opensource", label: "Open Source" },
  { path: "/notifications", label: "Notifications" },
];

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100 flex">
      <aside className="w-56 bg-gray-800 p-4 flex flex-col border-r border-gray-700">
        <h1 className="text-xl font-bold mb-6">DevPilot AI</h1>
        <nav className="flex flex-col gap-1 flex-1">
          {navItems.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`px-3 py-2 rounded transition-colors ${
                location.pathname === item.path
                  ? "bg-blue-600 text-white"
                  : "text-gray-300 hover:bg-gray-700"
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="border-t border-gray-700 pt-3 mt-3 text-sm">
          <p className="text-gray-400 truncate">{user?.github_username}</p>
          <button
            onClick={logout}
            className="mt-1 text-red-400 hover:text-red-300 transition-colors"
          >
            Logout
          </button>
        </div>
      </aside>
      <main className="flex-1 p-6 overflow-auto">{children}</main>
    </div>
  );
}
