<script lang="ts">
  import { onMount } from 'svelte';
  import { initMqtt, sendRequest, mqttData, livedata, loading, summary } from '$lib/stores/mqttClient';

  let selectedData = [];
  $: selectedData = $mqttData;

  onMount(() => {
    initMqtt();
  });

  function getAll() {
    sendRequest({ request: 'all', client_id: 'client-1' });
  }

  function getByColor(color: string) {
    sendRequest({ request: 'color', client_id: 'client-1', data: color });
  }

  // not needed (yet)
  function getLiveData() {
    // placeholder
  }
</script>

<button on:click={getAll}>Get All</button>
<button on:click={() => getByColor('blue')}>Get Blue</button>

{#if $loading}
  <p>Loading...</p>
{/if}

<ul>
  {#each selectedData as item}
    <li>{JSON.stringify(item)}</li>
  {/each}
</ul>
