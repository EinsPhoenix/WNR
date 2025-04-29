<script lang="ts">
    import { onMount } from "svelte";
  
    let isSticky = false;
  
    onMount(() => {
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
    </div>
  </nav>
  
  <main></main>
  
  <style>
    :root {
      --navbar-height: 100px;
    }
  
    .wnrlogo {
      background: none;
      border: none;
    }
  
    nav {
        background-color: var(--background-color);
        height: var(--navbar-height);
        transition: all 0.3s ease;
        width: 100%;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 1000;
        box-shadow: 0px 0px 10px 2px rgba(0,0,0,0.75);
        -webkit-box-shadow: 0px 0px 10px 2px rgba(0,0,0,0.75);
        -moz-box-shadow: 0px 0px 10px 2px rgba(0,0,0,0.75);
    }
  
    main {
      padding-top: var(--navbar-height);
    }
  
    .nav-content {
        display: flex;
        flex-direction: row;
        justify-content: center;
        height: 100%;
    }
  
    .app-name {
      display: flex;
      align-self: center;
      margin-top: 8px;
      margin-left: 2rem;
      transform: rotate(-3deg);
    }
  
    .group1 {
      display: flex;
      flex-direction: row;
      width: 75%;
    }
  
    @media (max-width: 768px) {
  
      .app-name {
        align-items: end;
        width: 100%;
        justify-content: end;
        margin: 0;
      }
  
      .wnrlogo {
        display: none;
      }
  
      .nav-content {
        flex-direction: column;
        height: auto;
        padding: 1rem;
      }
  
      nav {
        position: static;
        height: auto;
      }
  
      main {
        padding-top: 0;
      }
  
      .group1 {
          display: flex;
          flex-direction: column;
          width: 100%;
          align-items: end;
      }
    }
  </style>