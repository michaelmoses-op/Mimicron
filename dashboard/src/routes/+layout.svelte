<script lang="ts">
  let { children } = $props();
</script>

<svelte:head>
  <title>Mimicron</title>
</svelte:head>

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
  .wrap {
    max-width: 960px;
    margin: 0 auto;
    padding: 1.5rem;
  }
</style>
