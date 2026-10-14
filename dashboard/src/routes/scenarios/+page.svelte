<script lang="ts">
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import { listScenarios, startRun } from "$lib/api";

  type ScenarioRow = { id: string; name: string; current_version: number };

  let token = $state("");
  let scenarios = $state<ScenarioRow[]>([]);
  let message = $state("");
  let error = $state("");

  onMount(async () => {
    token = localStorage.getItem("access_token") ?? "";
    if (!token) {
      await goto("/login");
      return;
    }
    const page = await listScenarios(token);
    scenarios = page.items ?? [];
  });

  async function launch(scenarioId: string) {
    error = "";
    message = "";
    try {
      const run = await startRun(token, scenarioId, {
        mode_override: "accelerated",
        speed_override: 120,
      });
      message = `Started run ${run.id} (${run.status})`;
    } catch (e) {
      error = String(e);
    }
  }
</script>

<h1>Scenarios</h1>
<p>Start an accelerated run against a saved scenario (same defaults as <code>make demo</code>).</p>
{#if error}<p class="err">{error}</p>{/if}
{#if message}<p class="ok">{message}</p>{/if}
<ul>
  {#each scenarios as s}
    <li>
      <strong>{s.name}</strong> — v{s.current_version}
      <button onclick={() => launch(s.id)}>Start run</button>
    </li>
  {/each}
</ul>
{#if scenarios.length === 0}
  <p>No scenarios yet. Run <code>make demo</code> or POST <code>/v1/scenarios</code> via the API.</p>
{/if}

<style>
  ul {
    list-style: none;
    padding: 0;
  }
  li {
    display: flex;
    align-items: center;
    gap: 0.75rem;
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
  .ok {
    color: #86efac;
  }
</style>
