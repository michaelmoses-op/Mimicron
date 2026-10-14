<script lang="ts">
  import { onMount } from "svelte";
  import { authHeaders } from "$lib/api";

  const API = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

  let token = $state("");
  let items = $state<{ id: string; name: string; scopes: string[]; prefix: string }[]>([]);
  let name = $state("dev-key");
  let scopes = $state("read,ingest");
  let newSecret = $state("");
  let error = $state("");

  onMount(() => {
    token = localStorage.getItem("access_token") ?? "";
    if (token) void refresh();
  });

  async function refresh() {
    error = "";
    newSecret = "";
    const res = await fetch(`${API}/v1/api-keys`, { headers: authHeaders(token) });
    if (!res.ok) {
      error = await res.text();
      return;
    }
    const body = await res.json();
    items = body.items ?? [];
  }

  async function createKey() {
    error = "";
    newSecret = "";
    const res = await fetch(`${API}/v1/api-keys`, {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({
        name,
        scopes: scopes.split(",").map((s) => s.trim()).filter(Boolean),
      }),
    });
    if (!res.ok) {
      error = await res.text();
      return;
    }
    const body = await res.json();
    newSecret = body.secret;
    await refresh();
  }

  async function revoke(id: string) {
    await fetch(`${API}/v1/api-keys/${id}`, { method: "DELETE", headers: authHeaders(token) });
    await refresh();
  }
</script>

<h1>API keys</h1>
<p>Machine credentials for ingest, read, and simulate. The secret is shown once when created.</p>

{#if !token}
  <p><a href="/login">Sign in</a> to manage keys.</p>
{:else}
  <section class="card">
    <h2>Create key</h2>
    <label>Name <input bind:value={name} /></label>
    <label>Scopes (comma-separated) <input bind:value={scopes} /></label>
    <button onclick={createKey}>Create</button>
    {#if newSecret}
      <p class="secret">Secret (copy now): <code>{newSecret}</code></p>
    {/if}
  </section>

  <section class="card">
    <h2>Active keys</h2>
    <ul>
      {#each items as k}
        <li>
          <strong>{k.name}</strong> ({k.prefix}…) — {k.scopes.join(", ")}
          <button class="link" onclick={() => revoke(k.id)}>Revoke</button>
        </li>
      {/each}
    </ul>
  </section>
{/if}
{#if error}<p class="err">{error}</p>{/if}

<style>
  .card { margin: 1rem 0; padding: 1rem; border: 1px solid #1e293b; border-radius: 8px; }
  label { display: block; margin: 0.5rem 0; }
  input { width: 100%; padding: 0.4rem; }
  button { margin-top: 0.5rem; padding: 0.4rem 0.8rem; cursor: pointer; }
  button.link { margin-left: 0.5rem; background: transparent; border: none; color: #94a3b8; }
  .secret { color: #86efac; word-break: break-all; }
  .err { color: #ff8a8a; }
</style>
