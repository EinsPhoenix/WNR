<script lang="ts">
  import { createEventDispatcher } from 'svelte';

  export let message: { id: number; sender: string; preview: string; content: string; color: string; shape: string };
  export let isOpen: boolean;

  const dispatch = createEventDispatcher();

  function handleClick() {
    if (!isOpen) {
      dispatch('open');
    }
  }

  function handleInnerClick(event: MouseEvent) {
    event.stopPropagation();
  }

  function handleClose() {
    dispatch('close');
  }
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div
  class="letter-container {message.color} {message.shape}"
  class:is-open={isOpen}
  on:click|stopPropagation={handleClick}
>
  {#if !isOpen}
    <div class="letter-closed">
      <div class="letter-flap"></div>
      <div class="letter-body">
        <p class="sender">{message.sender}</p>
        <p class="preview">{message.preview}</p>
      </div>
      <div class="letter-bottom-flap"></div>
      <span class="cute-icon">💌</span>
    </div>
  {:else}
    <div class="letter-open" on:click={handleInnerClick}>
      <div class="paper-content">
        <div class="header">
          <h3>Von: {message.sender}</h3>
          <button class="close-button" on:click|stopPropagation={handleClose}>❌</button>
        </div>
        <p class="message-content">{message.content}</p>
        <div class="paper-texture"></div>
      </div>
    </div>
  {/if}
</div>

<style>
  .letter-container {
    width: 450px;
    height: 250px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
    cursor: pointer;
    transition: all 0.4s cubic-bezier(0.68, -0.55, 0.27, 1.55);
    position: relative;
    transform-origin: center;
    border: 1px solid rgba(255, 255, 255, 0.8);
  }

  .rounded-full { border-radius: 9999px; }
  .rounded-md { border-radius: 0.375rem; }
  .rounded-lg { border-radius: 0.5rem; }

  .bg-rose-100 { background-color: #ffe4e6; }
  .bg-blue-100 { background-color: #e0f2f7; }
  .bg-green-100 { background-color: #e6ffe6; }

  .letter-closed {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    padding: 10px;
    color: #444;
  }

  .letter-flap {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 50%;
    background-color: rgba(255, 255, 255, 0.5);
    transform-origin: top;
    transition: transform 0.3s ease;
    clip-path: polygon(0 0, 100% 0, 50% 100%);
    z-index: 2;
  }

  .letter-body {
    z-index: 1;
    text-align: center;
  }

  .letter-bottom-flap {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 50%;
    background-color: rgba(255, 255, 255, 0.5);
    clip-path: polygon(0 100%, 100% 100%, 50% 0);
    z-index: 2;
  }

  .sender {
    font-weight: bold;
    margin-bottom: 5px;
    font-size: 0.9em;
  }

  .preview {
    font-style: italic;
    font-size: 0.8em;
    color: #666;
  }

  .cute-icon {
    position: absolute;
    bottom: 5px;
    right: 5px;
    font-size: 1.2em;
    z-index: 3;
  }

  .letter-open {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(1);
    width: 80vw;
    max-width: 600px;
    height: auto;
    max-height: 80vh;
    background-color: #fffaf0;
    border-radius: 8px;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    padding: 30px;
    z-index: 30;
    display: flex;
    flex-direction: column;
    opacity: 1;
    transform-origin: center;
    transition: transform 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275), opacity 0.3s ease;
    overflow-y: auto;
  }

  .paper-content {
    position: relative;
    z-index: 2;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 15px;
    border-bottom: 1px dashed #ccc;
    padding-bottom: 10px;
  }

  .header h3 {
    margin: 0;
    color: #333;
    font-size: 1.2em;
  }

  .close-button {
    background: none;
    border: none;
    font-size: 1.5em;
    cursor: pointer;
    color: #666;
    transition: transform 0.2s ease;
  }

  .close-button:hover {
    transform: scale(1.1);
  }

  .message-content {
    white-space: pre-wrap;
    line-height: 1.6;
    color: #333;
    font-size: 1.1em;
  }

  .paper-texture {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-image: url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgdmlld0JveD0iMCAwIDIwMCAyMDAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGcgZmlsbD0iIzAwMDAwMCIgZmlsbC1vcGFjaXR5PSIwLjA1Ij48cGF0aCBkPSJNMCAxOTlsMTAwLTEwMGgxMDB2MTAwSDB6bTAgLTY2bTY2IDY2TDUwIDE1MCAyNCAxNzZsMjYtMjZ6TTUwIDUwTDEwMCAwIDIwMCAwdi01MGgtNTAuMDhsLTEwMC0xMDBoLTMuOTJWMTAwaDQ4LjA4eiIgLz48L2c+PC9zdmc+');
    background-repeat: repeat;
    opacity: 0.1;
    pointer-events: none;
    z-index: 1;
    border-radius: 8px;
  }
</style>