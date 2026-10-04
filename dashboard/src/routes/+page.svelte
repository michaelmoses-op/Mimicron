<script lang="ts">
  import { goto } from "$app/navigation";
  import { onMount } from "svelte";

  onMount(() => {
    const token = localStorage.getItem("access_token");
    goto(token ? "/runs" : "/login");
  });
</script>

<p>Loading…</p>
