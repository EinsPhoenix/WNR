<script lang="ts">
    import { onMount, tick } from "svelte";
    import { goto } from '$app/navigation';
    import { mqttData, liveData, initMqtt } from "$lib/stores/mqttClient";
  
    let isSticky = false;

    let activeIndex: number | null = null;
    let isLoggedIn = false;

  
    onMount(async () => {
        let value = localStorage.getItem('loggedIn');
        if (value === 'true') {
            isLoggedIn = true;
        } else {
            isLoggedIn = false;
            goto('/login');
        }
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

    function logout() {
        localStorage.setItem("loggedIn", "false");
        goto("/login");
    }

    function handleAccountClick() {
      goto('/account');
    }

  </script>
  
  <nav class:sticky={isSticky}>

    <div class="navbar-wrapper">

        <div class="logo-group">
            <button class="wnr-logo" on:click={goHome}>
                <img class="logo" src="/wnrcutealpha.png" alt="wnr logo" width="100" height="auto" />
                <img class="app-name" src="/wrnlogo2.png" alt="wnr logo" width="auto" height="auto" />
            </button>
        </div>

        <div class="item-wrapper">
            <button class="item-text" class:item-active={activeIndex === 0} on:click={() => activeIndex = 0}>
                <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M32 32c17.7 0 32 14.3 32 32l0 336c0 8.8 7.2 16 16 16l400 0c17.7 0 32 14.3 32 32s-14.3 32-32 32L80 480c-44.2 0-80-35.8-80-80L0 64C0 46.3 14.3 32 32 32zM160 224c17.7 0 32 14.3 32 32l0 64c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-64c0-17.7 14.3-32 32-32zm128-64l0 160c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-160c0-17.7 14.3-32 32-32s32 14.3 32 32zm64 32c17.7 0 32 14.3 32 32l0 96c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-96c0-17.7 14.3-32 32-32zM480 96l0 224c0 17.7-14.3 32-32 32s-32-14.3-32-32l0-224c0-17.7 14.3-32 32-32s32 14.3 32 32z"/></svg>
                Dashboard
            </button>
        </div>

        <div class="item-wrapper">
            <button class="item-text" class:item-active={activeIndex === 1} on:click={() => activeIndex = 1}>
                <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M48 64C21.5 64 0 85.5 0 112c0 15.1 7.1 29.3 19.2 38.4L236.8 313.6c11.4 8.5 27 8.5 38.4 0L492.8 150.4c12.1-9.1 19.2-23.3 19.2-38.4c0-26.5-21.5-48-48-48L48 64zM0 176L0 384c0 35.3 28.7 64 64 64l384 0c35.3 0 64-28.7 64-64l0-208L294.4 339.2c-22.8 17.1-54 17.1-76.8 0L0 176z"/></svg>
                Messages
                <div class="message-number">
                    8
                </div>
            </button>
        </div>

        <div class="item-wrapper">
            <button class="item-text" class:item-active={activeIndex === 2} on:click={() => activeIndex = 2}>
                <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 448 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M224 0c-17.7 0-32 14.3-32 32l0 19.2C119 66 64 130.6 64 208l0 18.8c0 47-17.3 92.4-48.5 127.6l-7.4 8.3c-8.4 9.4-10.4 22.9-5.3 34.4S19.4 416 32 416l384 0c12.6 0 24-7.4 29.2-18.9s3.1-25-5.3-34.4l-7.4-8.3C401.3 319.2 384 273.9 384 226.8l0-18.8c0-77.4-55-142-128-156.8L256 32c0-17.7-14.3-32-32-32zm45.3 493.3c12-12 18.7-28.3 18.7-45.3l-64 0-64 0c0 17 6.7 33.3 18.7 45.3s28.3 18.7 45.3 18.7s33.3-6.7 45.3-18.7z"/></svg>
                Notifications
                <div class="message-number">
                    17
                </div>
            </button>
        </div>

        <div class="item-wrapper">
            <button class="item-text" class:item-active={activeIndex === 3} on:click={() => activeIndex = 3}>
                <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M495.9 166.6c3.2 8.7 .5 18.4-6.4 24.6l-43.3 39.4c1.1 8.3 1.7 16.8 1.7 25.4s-.6 17.1-1.7 25.4l43.3 39.4c6.9 6.2 9.6 15.9 6.4 24.6c-4.4 11.9-9.7 23.3-15.8 34.3l-4.7 8.1c-6.6 11-14 21.4-22.1 31.2c-5.9 7.2-15.7 9.6-24.5 6.8l-55.7-17.7c-13.4 10.3-28.2 18.9-44 25.4l-12.5 57.1c-2 9.1-9 16.3-18.2 17.8c-13.8 2.3-28 3.5-42.5 3.5s-28.7-1.2-42.5-3.5c-9.2-1.5-16.2-8.7-18.2-17.8l-12.5-57.1c-15.8-6.5-30.6-15.1-44-25.4L83.1 425.9c-8.8 2.8-18.6 .3-24.5-6.8c-8.1-9.8-15.5-20.2-22.1-31.2l-4.7-8.1c-6.1-11-11.4-22.4-15.8-34.3c-3.2-8.7-.5-18.4 6.4-24.6l43.3-39.4C64.6 273.1 64 264.6 64 256s.6-17.1 1.7-25.4L22.4 191.2c-6.9-6.2-9.6-15.9-6.4-24.6c4.4-11.9 9.7-23.3 15.8-34.3l4.7-8.1c6.6-11 14-21.4 22.1-31.2c5.9-7.2 15.7-9.6 24.5-6.8l55.7 17.7c13.4-10.3 28.2-18.9 44-25.4l12.5-57.1c2-9.1 9-16.3 18.2-17.8C227.3 1.2 241.5 0 256 0s28.7 1.2 42.5 3.5c9.2 1.5 16.2 8.7 18.2 17.8l12.5 57.1c15.8 6.5 30.6 15.1 44 25.4l55.7-17.7c8.8-2.8 18.6-.3 24.5 6.8c8.1 9.8 15.5 20.2 22.1 31.2l4.7 8.1c6.1 11 11.4 22.4 15.8 34.3zM256 336a80 80 0 1 0 0-160 80 80 0 1 0 0 160z"/></svg>
                Settings
            </button>
        </div>

        <div class="item-wrapper">
            <button class="item-text" on:click={logout}>
                <svg class="icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><!--!Font Awesome Free 6.7.2 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2025 Fonticons, Inc.--><path d="M377.9 105.9L500.7 228.7c7.2 7.2 11.3 17.1 11.3 27.3s-4.1 20.1-11.3 27.3L377.9 406.1c-6.4 6.4-15 9.9-24 9.9c-18.7 0-33.9-15.2-33.9-33.9l0-62.1-128 0c-17.7 0-32-14.3-32-32l0-64c0-17.7 14.3-32 32-32l128 0 0-62.1c0-18.7 15.2-33.9 33.9-33.9c9 0 17.6 3.6 24 9.9zM160 96L96 96c-17.7 0-32 14.3-32 32l0 256c0 17.7 14.3 32 32 32l64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32l-64 0c-53 0-96-43-96-96L0 128C0 75 43 32 96 32l64 0c17.7 0 32 14.3 32 32s-14.3 32-32 32z"/></svg>
                Sign Out
            </button>
        </div>

        <div class="lightmode">
            <!-- From Uiverse.io by teymr --> 
            <label class="container">
            <input type="checkbox" checked="checked" />
            <div class="checkmark"></div>
            <div class="torch">
                <div class="head">
                <div class="face top">
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
                <div class="face left">
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
                <div class="face right">
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
                </div>
                <div class="stick">
                <div class="side side-left">
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
                <div class="side side-right">
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                    <div></div>
                </div>
                </div>
            </div>
            </label>
        </div>

    </div>

  </nav>
  
  <style>

    .item-active {
        background-color: #333;
        color: white;
    }

    .lightmode {
        display: flex;
        flex-direction: row;
        align-items: end;
        justify-content: start;
        position: absolute;
        bottom: 0;
        margin-left: 30px;
    }

    .message-number {
        background-color: red;
        color: white;
        font-weight: bold;
        border-radius: 50%;
        font-size: 1rem;
        width: 20px;
        height: 20px;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-left: 10px;
    }

    .icon {
        height: 25px;
        width: auto;
        padding-right: 8px;
        fill: white;
    }

    .item-text {
        color: white;
        padding-left: 0.5rem;
        font-weight: bold;
        font-size: 1.5rem;
        cursor: pointer;
        display: flex;
        align-items: center;
        width: 100%;
        padding-top: 20px;
        padding-bottom: 20px;
        padding-left: 20px;
    }

    .item-wrapper {
        display: flex;
        align-items: center;
    }

    .item-wrapper:hover {
        background-color: var(--experimental-light);
    }

    .logo-group {
        display: flex;
        justify-content: start;
        padding: 10px;
        padding-bottom: 50px;
    }

    .app-name {
        width: 100%;
        transform: translateY(-25px) rotate(-4deg);
        z-index: -9999;
    }

    .logo {
        transform: translateX(-15px) rotate(6deg);
    }

    .wnr-logo {
        display: flex;
        align-items: center;
        flex-direction: column;
    }

    .wnr-logo:hover {
        cursor: pointer;
    }

    .navbar-wrapper {
        height: 100%;
    }

    :root {
      --navbar-width: 300px;
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
  
    @media (max-width: 768px) {
      nav {
        position: static;
        width: 100%;
        height: 100px;
      }
    }



    /* From Uiverse.io by teymr */ 
    .container input {
        position: absolute;
        opacity: 0;
        cursor: pointer;
        height: 0;
        width: 0;
    }

    .container {
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
        cursor: pointer;
        user-select: none;
        transform: scale(0.5);
    }

    .torch {
        display: flex;
        justify-content: center;
        height: 150px;
    }

    .head,
    .stick {
        position: absolute;
        width: 30px;
    }

    .stick {
        position: relative;
        height: 120px;
    }

    .face {
        position: absolute;
        transform-style: preserve-3d;
        width: 30px;
        height: 30px;
        display: grid;
        grid-template-columns: 51% 49%;
        grid-template-rows: 50% 50%;
        background-color: #000000;
    }

    .top {
        transform: rotateX(90deg) translateZ(15px);
    }

    .left {
        transform: rotateY(-90deg) translateZ(15px);
    }

    .right {
        transform: rotateY(0deg) translateZ(15px);
    }

    .top div,
    .left div,
    .right div {
        width: 102%;
        height: 102%;
    }

    .top div:nth-child(1),
    .left div:nth-child(3),
    .right div:nth-child(3) {
        background-color: #ffc0cb80;
    }

    .top div:nth-child(2),
    .left div:nth-child(1),
    .right div:nth-child(1) {
        background-color: #ff69b480;
    }

    .top div:nth-child(3),
    .left div:nth-child(4),
    .right div:nth-child(4) {
        background-color: #ffe4e180;
    }

    .top div:nth-child(4),
    .left div:nth-child(2),
    .right div:nth-child(2) {
        background-color: #ff149380;
    }

    .side {
        position: absolute;
        width: 30px;
        height: 120px;
        display: grid;
        grid-template-columns: 50% 50%;
        grid-template-rows: repeat(8, 12.5%);
        cursor: pointer;
        translate: 0 22px;
    }

    .side-left {
        transform: rotateY(-90deg) translateZ(15px) translateY(8px);
    }

    .side-right {
        transform: rotateY(0deg) translateZ(15px) translateY(8px);
    }

    .side-left div,
    .side-right div {
        width: 103%;
        height: 103%;
    }

    .side div:nth-child(1) {
        background-color: #b5657580;
    }

    .side div:nth-child(2),
    .side div:nth-child(2) {
        background-color: #9b4f4f80;
    }

    .side div:nth-child(3),
    .side div:nth-child(5) {
        background-color: #c0808080;
    }

    .side div:nth-child(4),
    .side div:nth-child(10) {
        background-color: #6e3a3a80;
    }

    .side div:nth-child(6) {
        background-color: #8a4b4b80;
    }

    .side div:nth-child(7) {
        background-color: #cc6f6f80;
    }

    .side div:nth-child(8) {
        background-color: #8a4b4b80;
    }

    .side div:nth-child(9) {
        background-color: #c0808080;
    }

    .side div:nth-child(11),
    .side div:nth-child(15) {
        background-color: #75454580;
    }

    .side div:nth-child(12) {
        background-color: #6c3e3e80;
    }

    .side div:nth-child(13) {
        background-color: #c48e8e80;
    }

    .side div:nth-child(14) {
        background-color: #6b3b3b80;
    }

    .side div:nth-child(16) {
    background-color: #60363680;
    }

    .container input:checked ~ .torch .face {
        filter: drop-shadow(0px 0px 2px rgb(255, 255, 255))
            drop-shadow(0px 0px 10px rgba(255, 192, 203, 0.7))
            drop-shadow(0px 0px 25px rgba(255, 182, 193, 0.4));
    }

    .container input:checked ~ .torch .top div:nth-child(1),
    .container input:checked ~ .torch .left div:nth-child(3),
    .container input:checked ~ .torch .right div:nth-child(3) {
        background-color: #ffc0cb;
    }

    .container input:checked ~ .torch .top div:nth-child(2),
    .container input:checked ~ .torch .left div:nth-child(1),
    .container input:checked ~ .torch .right div:nth-child(1) {
        background-color: #ff69b4;
    }

    .container input:checked ~ .torch .top div:nth-child(3),
    .container input:checked ~ .torch .left div:nth-child(4),
    .container input:checked ~ .torch .right div:nth-child(4) {
        background-color: #fff0f5;
    }

    .container input:checked ~ .torch .top div:nth-child(4),
    .container input:checked ~ .torch .left div:nth-child(2),
    .container input:checked ~ .torch .right div:nth-child(2) {
        background-color: #ff1493;
    }

    .container input:checked ~ .torch .side div:nth-child(1) {
        background-color: #b56575;
    }

    .container input:checked ~ .torch .side div:nth-child(2),
    .container input:checked ~ .torch .side div:nth-child(2) {
        background-color: #9b4f4f;
    }

    .container input:checked ~ .torch .side div:nth-child(3),
    .container input:checked ~ .torch .side div:nth-child(5) {
        background-color: #c08080;
    }

    .container input:checked ~ .torch .side div:nth-child(4),
    .container input:checked ~ .torch .side div:nth-child(10) {
        background-color: #6e3a3a;
    }

    .container input:checked ~ .torch .side div:nth-child(6) {
        background-color: #8a4b4b;
    }

    .container input:checked ~ .torch .side div:nth-child(7) {
        background-color: #cc6f6f;
    }

    .container input:checked ~ .torch .side div:nth-child(8) {
        background-color: #8a4b4b;
    }

    .container input:checked ~ .torch .side div:nth-child(9) {
        background-color: #c08080;
    }

    .container input:checked ~ .torch .side div:nth-child(11),
    .container input:checked ~ .torch .side div:nth-child(15) {
        background-color: #754545;
    }

    .container input:checked ~ .torch .side div:nth-child(12) {
        background-color: #6c3e3e;
    }

    .container input:checked ~ .torch .side div:nth-child(13) {
        background-color: #c48e8e;
    }

    .container input:checked ~ .torch .side div:nth-child(14) {
        background-color: #6b3b3b;
    }

    .container input:checked ~ .torch .side div:nth-child(16) {
        background-color: #603636;
    }
  </style>