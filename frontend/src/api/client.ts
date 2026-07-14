const BASE = "/api";

function getToken(): string | null {
  return localStorage.getItem("devpilot_token");
}

export function clearToken(): void {
  localStorage.removeItem("devpilot_token");
}

export function setToken(token: string): void {
  localStorage.setItem("devpilot_token", token);
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  contentType?: string,
): Promise<T> {
  const headers: Record<string, string> = {};
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (body !== undefined && contentType) {
    headers["Content-Type"] = contentType;
  } else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${BASE}${path}`, {
    method,
    headers,
    body: body !== undefined
      ? contentType && contentType !== "application/json"
        ? body as BodyInit
        : JSON.stringify(body)
      : undefined,
  });

  if (res.status === 401) {
    clearToken();
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }

  return res.json();
}

export function get<T>(path: string): Promise<T> {
  return request<T>("GET", path);
}

export function post<T>(path: string, body?: unknown, contentType?: string): Promise<T> {
  return request<T>("POST", path, body, contentType);
}
