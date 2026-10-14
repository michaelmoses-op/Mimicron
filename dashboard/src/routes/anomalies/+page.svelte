<script lang="ts">
  import { onMount } from "svelte";
  import { authHeaders } from "$lib/api";

  const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

  let token = $state("");
  let items = $state<
    {
      time: string;
      device_id: string;
      metric: string;
      detector: string;
      severity: string;
      score: number;
    }[]
  >([]);
  let error = $state("");

  onMount(() => {
    token = localStorage.getItem("access_token") ?? "";
    if (token) void load();
  });

  async function load() {
    error = "";
    const res = await fetch(`${API}/v1/anomalies?limit=100`, { headers: authHeaders(token) });
    if (!res.ok) {
      error = await res.text();
      return;
    }
    const body = await res.json();
    items = body.items ?? [];
  }
</script>

<h1>Anomalies</h1>
<p>Recent detector hits from the stream processor (EWMA, stuck value, dropout).</p>
{#if !token}
  <p><a href="/login">Sign in</a> to view anomalies.</p>
{:else}
  <button onclick={load}>Refresh</button>
  <table>
    <thead>
      <tr><th>Time</th><th>Device</th><th>Metric</th><th>Detector</th><th>Severity</th><th>Score</th></tr>
    </thead>
    <tbody>
      {#each items as row}
        <tr>
          <td>{row.time}</td>
          <td>{row.device_id}</td>
          <td>{row.metric}</td>
          <td>{row.detector}</td>
          <td>{row.severity}</td>
          <td>{row.score.toFixed(2)}</td>
        </tr>
      {/each}
    </tbody>
  </table>
{/if}
{#if error}<p class="err">{error}</p>{/if}

<style>
  table { width: 100%; border-collapse: collapse; margin-top: 1rem; }
  th, td { text-align: left; padding: 0.35rem; border-bottom: 1px solid #1e293b; font-size: 0.9rem; }
  button { padding: 0.4rem 0.8rem; cursor: pointer; }
  .err { color: #ff8a8a; }
</style>
