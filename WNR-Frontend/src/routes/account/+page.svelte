export const ssr = false
<script>
  import { onMount } from 'svelte';
  import { connectMqtt, publish } from '$lib/mqttClient';

  onMount(() => {
    connectMqtt();
  });

  function send() {
    console.log("button clicked");
    publish('rust/response/livedata', 'hello world');
  }
</script>

<button on:click={send}>Send</button>