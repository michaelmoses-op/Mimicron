<script lang="ts">
  import { goto } from "$app/navigation";
  import { login, register } from "$lib/api";

  let email = $state("demo@mimicron.local");
  let password = $state("password1234");
  let error = $state("");

  async function doLogin() {
    error = "";
    try {
      const tokens = await login(email, password);
      localStorage.setItem("access_token", tokens.access_token);
      await goto("/runs");
    } catch (e) {
      error = String(e);
    }
  }

  async function doRegister() {
    error = "";
    try {
      const tokens = await register(email, password);
      localStorage.setItem("access_token", tokens.access_token);
      await goto("/runs");
    } catch (e) {
      error = String(e);
    }
  }
</script>

<h1>Mimicron</h1>
<p>Sign in to manage scenarios and runs.</p>
<label>Email <input bind:value={email} /></label>
<label>Password <input type="password" bind:value={password} /></label>
<div class="row">
  <button onclick={doLogin}>Login</button>
  <button onclick={doRegister}>Register</button>
</div>
{#if error}<p class="err">{error}</p>{/if}

<style>
  label { display: block; margin: 0.5rem 0; }
  input { width: 100%; padding: 0.5rem; margin-top: 0.25rem; }
  .row { display: flex; gap: 0.5rem; margin-top: 1rem; }
  button { padding: 0.5rem 1rem; cursor: pointer; }
  .err { color: #ff8a8a; }
</style>
