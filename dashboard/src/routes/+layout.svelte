<script lang="ts">
  import { page } from "$app/stores";

  let { children } = $props();
</script>

<svelte:head>
  <title>Mimicron</title>
</svelte:head>

<header class="top">
  <a class="brand" href="/">Mimicron</a>
  <nav>
    <a href="/runs" class:active={$page.url.pathname.startsWith("/runs")}>Runs</a>
    <a href="/traffic" class:active={$page.url.pathname.startsWith("/traffic")}>Traffic</a>
    <a href="/scenarios" class:active={$page.url.pathname.startsWith("/scenarios")}>Scenarios</a>
    <a href="/anomalies" class:active={$page.url.pathname.startsWith("/anomalies")}>Anomalies</a>
    <a href="/usage" class:active={$page.url.pathname.startsWith("/usage")}>Usage</a>
    <a href="/api-keys" class:active={$page.url.pathname.startsWith("/api-keys")}>API keys</a>
    <a href="/login">Login</a>
  </nav>
</header>
<main class="wrap">
  {@render children()}
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: system-ui, sans-serif;
    background: #0b1020;
    color: #e8eefc;
  }
  .top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1.5rem;
    border-bottom: 1px solid #1e293b;
  }
  .brand {
    color: #e8eefc;
    font-weight: 600;
    text-decoration: none;
  }
  nav {
    display: flex;
    gap: 1rem;
  }
  nav a {
    color: #94a3b8;
    text-decoration: none;
  }
  nav a.active,
  nav a:hover {
    color: #e8eefc;
  }
  .wrap {
    max-width: 960px;
    margin: 0 auto;
    padding: 1.5rem;
  }
</style>
