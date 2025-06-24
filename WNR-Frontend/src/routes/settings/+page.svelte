<script lang="ts">
  import { writable } from "svelte/store";

  const darkMode = writable(false);
  const notifications = writable(true);
  const locationAccess = writable(false);
  const autoUpdate = writable(true);
  const username = writable("Max Mustermann");
  const email = writable("max@example.com");
  const language = writable("de");
  const fontSize = writable("medium");
  const privacyLevel = writable("standard");
  const timezone = writable("Europe/Berlin");
  const autoPlayVideos = writable(false);

  const languages = ["de", "en", "fr", "es"];
  const fontSizes = ["small", "medium", "large"];
  const privacyLevels = ["low", "standard", "high"];
  const timezones = [
    "Europe/Berlin",
    "America/New_York",
    "Asia/Tokyo",
    "UTC",
  ];
</script>

<div class="settings-container">
  <h1>App Settings</h1>

  <div class="section">
    <h2>Account Information</h2>
    <div class="setting-item">
      <label for="username">Username</label>
      <input id="username" type="text" bind:value={$username} placeholder="Your username" />
    </div>
    <div class="setting-item">
      <label for="email">Email Address</label>
      <input id="email" type="email" bind:value={$email} placeholder="your@example.com" />
    </div>
  </div>

  <div class="section">
    <h2>General Preferences</h2>
    <div class="setting-item toggle">
      <label for="darkMode">Dark Mode</label>
      <button id="darkMode" class:active={$darkMode} on:click={() => darkMode.update(v => !v)}>
        {$darkMode ? "On" : "Off"}
      </button>
    </div>

    <div class="setting-item toggle">
      <label for="notifications">Push Notifications</label>
      <button id="notifications" class:active={$notifications} on:click={() => notifications.update(v => !v)}>
        {$notifications ? "On" : "Off"}
      </button>
    </div>

    <div class="setting-item toggle">
      <label for="locationAccess">Location Access</label>
      <button id="locationAccess" class:active={$locationAccess} on:click={() => locationAccess.update(v => !v)}>
        {$locationAccess ? "On" : "Off"}
      </button>
    </div>

    <div class="setting-item toggle">
      <label for="autoUpdate">Auto Update App</label>
      <button id="autoUpdate" class:active={$autoUpdate} on:click={() => autoUpdate.update(v => !v)}>
        {$autoUpdate ? "On" : "Off"}
      </button>
    </div>

    <div class="setting-item toggle">
      <label for="autoPlayVideos">Autoplay Videos</label>
      <button id="autoPlayVideos" class:active={$autoPlayVideos} on:click={() => autoPlayVideos.update(v => !v)}>
        {$autoPlayVideos ? "On" : "Off"}
      </button>
    </div>
  </div>

  <div class="section">
    <h2>Display Settings</h2>
    <div class="setting-item">
      <label for="language">App Language</label>
      <select id="language" bind:value={$language}>
        {#each languages as lang}
          <option value={lang}>{lang.toUpperCase()}</option>
        {/each}
      </select>
    </div>

    <div class="setting-item">
      <label for="fontSize">Font Size</label>
      <select id="fontSize" bind:value={$fontSize}>
        {#each fontSizes as size}
          <option value={size}>{$language === 'de' ? (size === 'small' ? 'Klein' : size === 'medium' ? 'Mittel' : 'Groß') : (size.charAt(0).toUpperCase() + size.slice(1))}</option>
        {/each}
      </select>
    </div>
  </div>

  <div class="section">
    <h2>Privacy & Security</h2>
    <div class="setting-item">
      <label for="privacyLevel">Privacy Level</label>
      <select id="privacyLevel" bind:value={$privacyLevel}>
        {#each privacyLevels as level}
          <option value={level}>{level.charAt(0).toUpperCase() + level.slice(1)}</option>
        {/each}
      </select>
    </div>
    <div class="setting-item">
      <label for="timezone">Timezone</label>
      <select id="timezone" bind:value={$timezone}>
        {#each timezones as zone}
          <option value={zone}>{zone.replace("_", " ")}</option>
        {/each}
      </select>
    </div>
  </div>
</div>

<style>
  :root {
    --pastel-red-color: #FF6B6B;
    --pastel-orange-color: #FFC94A;
    --pastel-yellow-color: #FFF275;
    --pastel-green-color: #8DFFCD;
    --pastel-lightblue-color: #6CD4EE;
    --pastel-blue-color: #7B8DFF;
    --pastel-purple-color: #A06EFF;
    --pastel-pink-color: #ffffff;
    --pastel-white-color: #F8F8FF;

    --glass-bg: rgba(255, 255, 255, 0.2);
    --glass-border: rgba(255, 255, 255, 0.4);
    --glass-blur: blur(25px);
    --text-color: #333333;
    --accent-color: #7B3CFF;
    --accent-dark: #5A2BBF;
    --shadow-light: rgba(123, 60, 255, 0.1);
    --shadow-medium: rgba(123, 60, 255, 0.25);
  }

  *, *::before, *::after {
    box-sizing: border-box;
  }

  html, body {
    height: 100%;
    margin: 0;
    overflow: hidden;
  }

  .settings-container {
    background: linear-gradient(135deg, var(--pastel-lightblue-color) 0%, var(--pastel-pink-color) 100%);
    min-height: 100vh;
    max-height: 100vh;
    margin-left: var(--navbar-width);
    padding: 3rem 5vw;
    font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    color: var(--text-color);
    display: flex;
    flex-direction: column;
    gap: 2.5rem;
    overflow-y: auto;
    scroll-behavior: smooth;
    position: relative;
    z-index: 1;
  }

  .settings-container::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at top left, rgba(255,255,255,0.1) 0%, transparent 50%),
                radial-gradient(circle at bottom right, rgba(255,255,255,0.1) 0%, transparent 50%);
    pointer-events: none;
    z-index: 0;
    backdrop-filter: var(--glass-blur);
  }


  .settings-container::-webkit-scrollbar {
    width: 12px;
  }
  .settings-container::-webkit-scrollbar-thumb {
    background: var(--accent-color);
    border-radius: 10px;
    border: 3px solid transparent;
    background-clip: content-box;
  }
  .settings-container::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.1);
    border-radius: 10px;
  }
  .settings-container::-webkit-scrollbar-thumb:hover {
    background: var(--accent-dark);
  }

  h1 {
    font-size: clamp(2.5rem, 6vw, 3.8rem);
    color: var(--accent-color);
    font-weight: 800;
    margin: 0 0 1rem 0;
    text-shadow: 2px 2px 8px var(--shadow-light);
    z-index: 9999;
  }

  .section {
    background: var(--glass-bg);
    backdrop-filter: var(--glass-blur);
    border-radius: 2rem;
    padding: clamp(1.5rem, 4vw, 3rem) clamp(2rem, 5vw, 4rem);
    box-shadow: 0 15px 40px var(--shadow-medium);
    border: 1px solid var(--glass-border);
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
  }

  .section:hover {
    transform: translateY(-5px);
    box-shadow: 0 20px 50px rgba(123, 60, 255, 0.35);
  }

  .section h2 {
    font-size: clamp(1.6rem, 4vw, 2.2rem);
    font-weight: 700;
    border-bottom: 3px solid var(--accent-color);
    padding-bottom: 0.5rem;
    margin-bottom: 1.5rem;
    color: var(--accent-dark);
    letter-spacing: 0.02em;
  }

  .setting-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1.5rem;
    font-size: clamp(1rem, 2.5vw, 1.2rem);
    font-weight: 600;
    color: var(--text-color);
    padding: 0.5rem 0;
    border-bottom: 1px dashed rgba(255, 255, 255, 0.3);
  }

  .setting-item:last-child {
    border-bottom: none;
  }

  label {
    flex: 1.5;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    cursor: pointer;
  }

  input[type="text"],
  input[type="email"],
  select {
    flex: 2;
    padding: 0.7rem 1.2rem;
    font-size: clamp(1rem, 2.5vw, 1.1rem);
    border-radius: 1.5rem;
    border: 1px solid rgba(255, 255, 255, 0.6);
    background: rgba(255, 255, 255, 0.5);
    color: var(--text-color);
    box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.1);
    outline: none;
    transition: all 0.3s ease;
    min-width: 150px;
  }

  input[type="text"]::placeholder,
  input[type="email"]::placeholder {
    color: rgba(51, 51, 51, 0.6);
  }

  input[type="text"]:focus,
  input[type="email"]:focus,
  select:focus {
    border-color: var(--accent-color);
    box-shadow: 0 0 0 3px rgba(123, 60, 255, 0.3), inset 0 2px 8px rgba(0, 0, 0, 0.15);
    background: rgba(255, 255, 255, 0.7);
  }

  select {
    appearance: none;
    -webkit-appearance: none;
    -moz-appearance: none;
    background-image: url('data:image/svg+xml;utf8,<svg fill="%237B3CFF" height="24" viewBox="0 0 24 24" width="24" xmlns="http://www.w3.org/2000/svg"><path d="M7 10l5 5 5-5z"/><path d="M0 0h24v24H0z" fill="none"/></svg>'); /* Custom SVG arrow */
    background-repeat: no-repeat;
    background-position: right 1rem center;
    background-size: 1.5em;
    padding-right: 2.5rem;
  }

  .toggle button {
    background: rgba(123, 60, 255, 0.2);
    border: none;
    border-radius: 2rem;
    padding: 0.6rem 2rem;
    font-weight: 700;
    color: var(--accent-dark);
    cursor: pointer;
    transition: background 0.3s ease, color 0.3s ease, box-shadow 0.3s ease, transform 0.2s ease;
    user-select: none;
    flex-shrink: 0;
    min-width: 90px;
    text-align: center;
  }

  .toggle button.active {
    background: var(--accent-color);
    color: var(--pastel-white-color);
    box-shadow: 0 5px 15px var(--shadow-medium);
    transform: scale(1.02);
  }

  .toggle button:hover:not(.active) {
    background: rgba(123, 60, 255, 0.4);
    color: var(--accent-color);
    transform: translateY(-2px);
  }

  .toggle button.active:hover {
    background: var(--accent-dark);
    box-shadow: 0 7px 20px rgba(123, 60, 255, 0.4);
  }

  @media (max-width: 768px) {
    .settings-container {
      padding: 2rem 4vw;
      gap: 2rem;
    }

    h1 {
      font-size: clamp(2rem, 8vw, 3rem);
      text-align: center;
    }

    .section {
      padding: 1.5rem 1.8rem;
      border-radius: 1.5rem;
    }

    .section h2 {
      font-size: clamp(1.4rem, 5vw, 1.8rem);
      text-align: center;
      border-bottom: 2px solid var(--accent-color);
    }

    .setting-item {
      flex-direction: column;
      align-items: flex-start;
      gap: 0.6rem;
      padding: 0.8rem 0;
      font-size: clamp(0.9rem, 2.5vw, 1.1rem);
    }

    label {
      flex: none;
      width: 100%;
      text-align: left;
      white-space: normal;
      font-size: 1rem;
    }

    input[type="text"],
    input[type="email"],
    select,
    .toggle button {
      flex: none;
      width: 100%;
      font-size: 1rem;
      padding: 0.6rem 1rem;
    }

    .toggle button {
      min-width: unset;
      height: 45px;
    }
  }

  @media (max-width: 480px) {
    .settings-container {
      padding: 1.5rem 3vw;
      gap: 1.5rem;
    }

    h1 {
      font-size: clamp(1.8rem, 9vw, 2.5rem);
    }

    .section {
      padding: 1.2rem 1.5rem;
      border-radius: 1rem;
    }

    .section h2 {
      font-size: clamp(1.2rem, 6vw, 1.5rem);
      margin-bottom: 1rem;
    }

    .setting-item {
      padding: 0.7rem 0;
      font-size: 0.95rem;
    }

    label,
    input[type="text"],
    input[type="email"],
    select,
    .toggle button {
      font-size: 0.9rem;
    }
  }

  @media (min-width: 769px) and (max-width: 1024px) {
    .settings-container {
      padding: 2.5rem 6vw;
    }

    h1 {
      font-size: clamp(2.8rem, 5vw, 3.5rem);
    }

    .section {
      padding: 2rem 3rem;
    }

    .section h2 {
      font-size: clamp(1.7rem, 3.5vw, 2rem);
    }

    .setting-item {
      font-size: 1.1rem;
    }
  }

  @media (min-width: 1025px) {
    .settings-container {
      padding: 3rem 6rem;
    }
  }

  label {
    color: black;
  }
</style>