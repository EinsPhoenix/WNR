<script lang="ts">
    import { onMount } from "svelte";
    import { goto } from '$app/navigation';
    import { mqttData, initMqtt } from "$lib/stores/mqttClient";
  
    let isSticky = false;
  
    onMount(() => {
      initMqtt();
      const navbar = document.querySelector("nav");
      if (navbar) {
        const sticky = navbar.offsetTop;
  
        window.onscroll = () => {
          isSticky = window.pageYOffset > sticky;
        };
      }
    });
  
    function goHome() {
      window.location.href = '/';
    }

    function handleAccountClick() {
      goto('/account');
    }
  </script>
  
  <nav class:sticky={isSticky}>
    <div class="nav-content">
      <div class="group1">
          <!-- LOGO -->
          <button class="wnrlogo" on:click={goHome}>
              <img src="/wnrcutealpha.png" alt="wnr logo" width="80" height="auto" />
          </button>
  
          <!-- TITEL -->
          <!-- <div class="app-name">Why no REST?</div> -->
          <img class="app-name" src="/wrnlogo2.png" alt="wnr logo" width="400" height="auto" />
      </div>
      
      <div class="group2">
        {#each $mqttData as msg}
          <button class="btn">
            <div class="item">
              [{new Date(msg.timestamp).toLocaleTimeString()}]
              Item
              #{msg.part_number}
              produced
            </div>
          </button>
        {/each}
      </div>

      <div class="group3">

        <button class="nav-item btn">
          <div class="content">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M121 32C91.6 32 66 52 58.9 80.5L1.9 308.4C.6 313.5 0 318.7 0 323.9L0 416c0 35.3 28.7 64 64 64l384 0c35.3 0 64-28.7 64-64l0-92.1c0-5.2-.6-10.4-1.9-15.5l-57-227.9C446 52 420.4 32 391 32L121 32zm0 64l270 0 48 192-51.2 0c-12.1 0-23.2 6.8-28.6 17.7l-14.3 28.6c-5.4 10.8-16.5 17.7-28.6 17.7l-120.4 0c-12.1 0-23.2-6.8-28.6-17.7l-14.3-28.6c-5.4-10.8-16.5-17.7-28.6-17.7L73 288 121 96z"/></svg>
            Inbox
          </div>
        </button>

        <button class="nav-item btn">
          <div class="content">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M224 0c-17.7 0-32 14.3-32 32l0 19.2C119 66 64 130.6 64 208l0 18.8c0 47-17.3 92.4-48.5 127.6l-7.4 8.3c-8.4 9.4-10.4 22.9-5.3 34.4S19.4 416 32 416l384 0c12.6 0 24-7.4 29.2-18.9s3.1-25-5.3-34.4l-7.4-8.3C401.3 319.2 384 273.9 384 226.8l0-18.8c0-77.4-55-142-128-156.8L256 32c0-17.7-14.3-32-32-32zm45.3 493.3c12-12 18.7-28.3 18.7-45.3l-64 0-64 0c0 17 6.7 33.3 18.7 45.3s28.3 18.7 45.3 18.7s33.3-6.7 45.3-18.7z"/></svg>
            Alerts
          </div>
        </button>

        <button class="nav-item btn" on:click={goHome}>
          <div class="content">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M32 32c17.7 0 32 14.3 32 32l0 336c0 8.8 7.2 16 16 16l400 0c17.7 0 32 14.3 32 32s-14.3 32-32 32L80 480c-44.2 0-80-35.8-80-80L0 64C0 46.3 14.3 32 32 32zm96 96c0-17.7 14.3-32 32-32l192 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-192 0c-17.7 0-32-14.3-32-32zm32 64l128 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-128 0c-17.7 0-32-14.3-32-32s14.3-32 32-32zm0 96l256 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-256 0c-17.7 0-32-14.3-32-32s14.3-32 32-32z"/></svg>
            Reports
          </div>
        </button>

      </div>

      <div class="group4">
        <button class="user btn" on:click={handleAccountClick}>
          <div class="user-icon"> 
            MM
          </div>
          <div class="user-name">
            Max Mustermann
          </div>
        </button>
      </div>

    </div>
  </nav>
  
  <style>
    :root {
      --navbar-width: 300px;
    }

    .btn {
      width: 100%;
      padding: 1rem;
      margin-top: 0.5rem;
      background-color: var(--pastel-white-color);
      width: 100%;
      border-top: solid 2px;
      border-bottom: solid 2px;
    }

    .btn:hover {
      cursor: pointer;
      background-color: rgb(194, 194, 194);
    }

    /* .item {
      background-color: var(--pastel-white-color);
      width: 100%;
      border-top: solid 2px;
      border-bottom: solid 2px;
    } */

    /* .item:hover {
      background-color: rgb(194, 194, 194);
    } */
  
    .wnrlogo {
      background: none;
      border: none;
    }
  
    nav {
        height: 100%;
        transition: all 0.3s ease;
        width: var(--navbar-width);
        position: fixed;
        top: 0;
        left: 0;
        z-index: 1000;
        box-shadow: 0px 0px 10px 2px rgba(0,0,0,0.75);
        -webkit-box-shadow: 0px 0px 10px 2px rgba(0,0,0,0.75);
        -moz-box-shadow: 0px 0px 10px 2px rgba(0,0,0,0.75);
    }
  
    .nav-content {
        display: flex;
        flex-direction: column;
        align-items: center;
        height: 100%;
    }
  
    .app-name {
      transform: rotate(-3deg);
      width: 240px;
      height: auto;
    }
  
    .group1 {
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: center;
      width: 100%;
      background-color: var(--pastel-purple-color);
      height: 150px;
    }

    .group2 {
      display: flex;
      flex-direction: column;
      width: 100%;
      height: 100%;
      align-items: start;
      background-color: var(--pastel-pink-color);
      border-top: solid 2px;
      overflow: auto;
    }

    .group3 {
      border-top: solid 2px;
      background-color: var(--pastel-pink-color);
      width: 100%;
      height: 100%;
    }

    .nav-item {
      height: 4rem;
      display: flex;
      align-items: center;
      border-top: solid 2px;
      border-bottom: solid 2px;
      margin-top: 0.5rem;
      background-color: var(--pastel-white-color);
    }

    .nav-item:hover {
      background-color: rgb(194, 194, 194);
    }

    .content {
      margin-left: 1rem;
      width: 100%;
      display: flex;
    }

    svg {
      width: 25px;
      height: auto;
      margin-right: 1rem;
    }

    .group4 {
      border-top: solid 2px;
      background-color: var(--pastel-pink-color);
      width: 100%;
      height: 200px;
    }

    .user {
      display: flex;
      flex-direction: row;
      align-items: center;
      justify-content: start;
      height: 100%;
      padding: 1rem;
      background-color: white;
    }

    .user-icon {
      border: solid 1px black;
      border-radius: 25px;
      height: 50px;
      width: 50px;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      background-color: var(--pastel-red-color);
      color: white;
    }

    .user-name {
      margin-left: 1rem;
      font-size: 22px;
    }
  
    @media (max-width: 768px) {

      /* HIDE FOR NOW */
      .group3 {
        display: none;
      }

      .group4 {
        display: none;
      }

      .wnrlogo {
        min-width: 100px;
        height: 100px;
      }

      .app-name {
        min-width: 250px;
      }
  
      .nav-content {
        flex-direction: row;
        height: 100%;
      }
  
      nav {
        position: static;
        width: 100%;
        height: 100px;
      }
  
      .group1 {
          display: flex;
          flex-direction: row;
          width: 100%;
          height: 100%;
          align-items: center;
          box-shadow: none;
      }

      .group2 {
        display: none;
      }
    }
  </style>