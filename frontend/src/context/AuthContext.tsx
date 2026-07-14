import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { loginWithPat, getMe } from "../api/auth";
import { setToken, clearToken } from "../api/client";

interface User {
  id: string;
  github_username: string;
}

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (pat: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("devpilot_token");
    if (!token) {
      setIsLoading(false);
      return;
    }
    getMe()
      .then((u) => setUser(u))
      .catch(() => clearToken())
      .finally(() => setIsLoading(false));
  }, []);

  async function login(pat: string) {
    const res = await loginWithPat(pat);
    setToken(res.access_token);
    setUser(res.user);
  }

  function logout() {
    clearToken();
    setUser(null);
  }

  return (
    <AuthContext.Provider
      value={{ user, isLoading, isAuthenticated: user !== null, login, logout }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
