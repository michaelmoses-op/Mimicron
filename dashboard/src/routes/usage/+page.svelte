<script lang="ts">
  import { onMount } from "svelte";
  import { authHeaders } from "$lib/api";

  const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

  let token = $state("");
  let quota = $state<Record<string, number>>({});
  let daily = $state<{ day: string; events_ingested: number; api_calls: number }[]>([]);
  let error = $state("");

  onMount(() => {
    token = localStorage.getItem("access_token") ?? "";
    if (token) void load();
  });

  async function load() {
    error = "";
    const res = await fetch(`${API}/v1/usage`, { headers: authHeaders(token) });
    if (!res.ok) {
      error = await res.text();
      return;
    }
    const body = await res.json();
    quota = body.quota ?? {};
    daily = body.daily ?? [];
  }
</script>

<h1>Usage</h1>
{#if !token}
  <p><a href="/login">Sign in</a> to view usage.</p>
{:else}
  <section class="card">
    <h2>Quota</h2>
    <ul>
      {#each Object.entries(quota) as [k, v]}
        <li>{k}: {v}</li>
      {/each}
    </ul>
  </section>
  <section class="card">
    <h2>Daily</h2>
    <table>
      <thead><tr><th>Day</th><th>Events ingested</th><th>API calls</th></tr></thead>
      <tbody>
        {#each daily as row}
          <tr>
            <td>{row.day}</td>
            <td>{row.events_ingested}</td>
            <td>{row.api_calls}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </section>
{/if}
{#if error}<p class="err">{error}</p>{/if}

<style>
  .card { margin: 1rem 0; padding: 1rem; border: 1px solid #1e293b; border-radius: 8px; }
  table { width: 100%; border-collapse: collapse; }
  th, td { text-align: left; padding: 0.35rem; border-bottom: 1px solid #1e293b; }
  .err { color: #ff8a8a; }
</style>
