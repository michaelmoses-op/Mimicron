const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type TokenPair = { access_token: string; refresh_token: string };

export async function register(email: string, password: string): Promise<TokenPair> {
  const res = await fetch(`${API}/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function login(email: string, password: string): Promise<TokenPair> {
  const res = await fetch(`${API}/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export function authHeaders(token: string): HeadersInit {
  return { Authorization: `Bearer ${token}`, "Content-Type": "application/json" };
}

export async function listRuns(token: string) {
  const res = await fetch(`${API}/v1/runs`, { headers: authHeaders(token) });
  return res.json();
}

export async function mintStreamToken(token: string) {
  const res = await fetch(`${API}/v1/stream-tokens`, { method: "POST", headers: authHeaders(token) });
  return res.json();
}
