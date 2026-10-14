<script lang="ts">
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";
  import uPlot from "uplot";
  import "uplot/dist/uPlot.min.css";
  import { listRuns, queryTraffic } from "$lib/api";

  type Rollup = {
    time: string;
    rps: number;
    error_rate: number;
    p50_ms: number;
    p95_ms: number;
    p99_ms: number;
  };

  let token = $state("");
  let runId = $state("");
  let runs = $state<{ id: string; status: string }[]>([]);
  let rollups = $state<Rollup[]>([]);
  let error = $state("");
  let chartEl = $state<HTMLDivElement | null>(null);
  let plot: uPlot | null = null;

  function renderChart(items: Rollup[]) {
    if (!chartEl) return;
    plot?.destroy();
    if (items.length === 0) return;
    const xs = items.map((i) => new Date(i.time).getTime() / 1000);
    const rps = items.map((i) => i.rps);
    const err = items.map((i) => i.error_rate * 100);
    const p95 = items.map((i) => i.p95_ms);
    plot = new uPlot(
      {
        width: chartEl.clientWidth || 800,
        height: 280,
        series: [
          {},
          { label: "RPS", stroke: "#38bdf8" },
          { label: "Error %", stroke: "#f87171" },
          { label: "p95 ms", stroke: "#a78bfa" },
        ],
        scales: { x: { time: true } },
      },
      [xs, rps, err, p95],
      chartEl,
    );
  }

  async function load() {
    error = "";
    if (!runId) {
      error = "Select a run";
      return;
    }
    const to = new Date();
    const from = new Date(to.getTime() - 60 * 60 * 1000);
    try {
      const page = await queryTraffic(token, {
        run_id: runId,
        from: from.toISOString(),
        to: to.toISOString(),
      });
      rollups = page.items ?? [];
      renderChart(rollups);
    } catch (e) {
      error = String(e);
    }
  }

  onMount(async () => {
    token = localStorage.getItem("access_token") ?? "";
    if (!token) {
      await goto("/login");
      return;
    }
    const page = await listRuns(token);
    runs = page.items ?? [];
    const running = runs.find((r) => r.status === "running");
    if (running) runId = running.id;
  });
</script>

<h1>Traffic</h1>
<p>10s rollups: RPS, error rate, latency (from <code>/v1/traffic</code>).</p>

<label>
  Run
  <select bind:value={runId}>
    <option value="">—</option>
    {#each runs as r}
      <option value={r.id}>{r.id.slice(0, 8)}… ({r.status})</option>
    {/each}
  </select>
</label>
<button onclick={load}>Refresh</button>
{#if error}<p class="err">{error}</p>{/if}

<div bind:this={chartEl} class="chart"></div>

{#if rollups.length > 0}
  <table>
    <thead>
      <tr><th>Time</th><th>RPS</th><th>Error rate</th><th>p50</th><th>p95</th><th>p99</th></tr>
    </thead>
    <tbody>
      {#each rollups.slice(-20) as row}
        <tr>
          <td>{new Date(row.time).toLocaleTimeString()}</td>
          <td>{row.rps.toFixed(2)}</td>
          <td>{(row.error_rate * 100).toFixed(2)}%</td>
          <td>{row.p50_ms.toFixed(0)}</td>
          <td>{row.p95_ms.toFixed(0)}</td>
          <td>{row.p99_ms.toFixed(0)}</td>
        </tr>
      {/each}
    </tbody>
  </table>
{/if}

<style>
  .chart {
    margin: 1rem 0;
    min-height: 280px;
  }
  .err {
    color: #f87171;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.875rem;
  }
  th,
  td {
    border-bottom: 1px solid #334155;
    padding: 0.35rem 0.5rem;
    text-align: left;
  }
</style>
