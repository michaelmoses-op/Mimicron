<script lang="ts">
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { controlRun, listRuns, mintStreamToken } from "$lib/api";

  type RunRow = {
    id: string;
    status: string;
    scenario_id?: string;
    scenario_version?: number;
    device_count?: number;
    events_emitted?: number;
  };

  let runs = $state<RunRow[]>([]);
  let live = $state<string[]>([]);
  let token = $state("");
  let error = $state("");

  async function refresh() {
    const page = await listRuns(token);
    runs = page.items ?? [];
  }

  onMount(async () => {
    token = localStorage.getItem("access_token") ?? "";
    if (!token) {
      await goto("/login");
      return;
    }
    await refresh();
  });

  async function stopRun(runId: string) {
    error = "";
    try {
      await controlRun(token, runId, "stop");
      await refresh();
    } catch (e) {
      error = String(e);
    }
  }

  async function connectStream() {
    const st = await mintStreamToken(token);
    const streamBase = import.meta.env.VITE_STREAM_URL ?? "http://localhost:8082";
    const es = new EventSource(`${streamBase}/v1/stream?token=${encodeURIComponent(st.token)}`);
    es.addEventListener("telemetry", (ev) => {
      live = [ev.data, ...live].slice(0, 20);
    });
  }
</script>

<h1>Runs</h1>
<button onclick={connectStream}>Connect live stream</button>
<button onclick={refresh}>Refresh</button>
{#if error}<p class="err">{error}</p>{/if}
<ul>
  {#each runs as run}
    <li>
      <span>{run.id.slice(0, 8)}… — {run.status}</span>
      {#if run.scenario_id}
        <span>scenario {run.scenario_id.slice(0, 8)}… v{run.scenario_version ?? "?"}</span>
      {/if}
      <span>devices {run.device_count ?? 0} — events {run.events_emitted ?? 0}</span>
      {#if run.status === "running" || run.status === "paused"}
        <button onclick={() => stopRun(run.id)}>Stop</button>
      {/if}
    </li>
  {/each}
</ul>
<h2>Live telemetry</h2>
<pre>{live.join("\n")}</pre>

<style>
  ul {
    list-style: none;
    padding: 0;
  }
  li {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem 1rem;
    padding: 0.5rem 0;
    border-bottom: 1px solid #1e293b;
  }
  button {
    padding: 0.35rem 0.75rem;
    cursor: pointer;
  }
  .err {
    color: #ff8a8a;
  }
</style>
