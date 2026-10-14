const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export type TokenPair = { access_token: string; refresh_token: string };

export async function register(
  email: string,
  password: string,
  tenantName?: string,
): Promise<TokenPair> {
  const res = await fetch(`${API}/v1/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      email,
      password,
      ...(tenantName ? { tenant_name: tenantName } : {}),
    }),
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

export async function listScenarios(token: string) {
  const res = await fetch(`${API}/v1/scenarios`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function startRun(
  token: string,
  scenarioId: string,
  opts?: { mode_override?: string; speed_override?: number },
) {
  const res = await fetch(`${API}/v1/runs`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ scenario_id: scenarioId, ...opts }),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function queryTraffic(
  token: string,
  params: { run_id?: string; from: string; to: string; flow?: string; region?: string },
) {
  const q = new URLSearchParams({ from: params.from, to: params.to });
  if (params.run_id) q.set("run_id", params.run_id);
  if (params.flow) q.set("flow", params.flow);
  if (params.region) q.set("region", params.region);
  const res = await fetch(`${API}/v1/traffic?${q}`, { headers: authHeaders(token) });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function controlRun(token: string, runId: string, action: "stop" | "pause" | "resume") {
  const res = await fetch(`${API}/v1/runs/${runId}/${action}`, {
    method: "POST",
    headers: authHeaders(token),
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
