<script lang="ts">
  import { onMount } from "svelte";
  import { listRuns, mintStreamToken } from "$lib/api";

  let runs = $state<any[]>([]);
  let live = $state<string[]>([]);
  let token = "";

  onMount(async () => {
    token = localStorage.getItem("access_token") ?? "";
    if (!token) return;
    const page = await listRuns(token);
    runs = page.items ?? [];
  });

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
<ul>
  {#each runs as run}
    <li>{run.id} — {run.status} — devices {run.device_count} — events {run.events_emitted}</li>
  {/each}
</ul>
<h2>Live telemetry</h2>
<pre>{live.join("\n")}</pre>
