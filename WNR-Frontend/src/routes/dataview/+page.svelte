<script lang="ts">
    import { onMount } from "svelte";
    import { mqttData, initMqtt } from "$lib/stores/mqttClient";

    onMount(() => {
        initMqtt();
    })
</script>

<div class="data-list">
  {#each $mqttData as msg}
    <div class="data-row">
      <div class="data-cell">{msg.part_number}</div>
      <div class="data-cell">{new Date(msg.timestamp).toLocaleString()}</div>
      <div class="data-cell" data-color={msg.color}>{msg.color}</div>
      <div class="data-cell">{msg.temperature.toFixed(1)}</div>
      <div class="data-cell">{msg.humidity.toFixed(1)}</div>
      <div class="data-cell">{msg.energy.toFixed(2)}</div>
    </div>
  {/each}
</div>

<style>
    .data-list {
        padding: 1rem;
        display: flex;
        flex-direction: column;
        gap: 0.1rem;
        margin-left: var(--navbar-width);
    }

    .data-row {
        display: flex;
        gap: 0.1rem;
        padding: 0.1rem;
        border-bottom: 1px solid #ccc;
    }

    .data-cell {
        flex: 1;
    }

</style>