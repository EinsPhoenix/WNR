<script>
    import '../app.css'
    import Navbar from '$lib/Navbar.svelte';
    import NewNavbar from '$lib/NewNavbar.svelte';
    import Footer from '$lib/Footer.svelte';
    import Loader from '$lib/Loader.svelte';
    import { onMount } from 'svelte';
    import { page } from '$app/stores';

    let hasPageLoaded = false;

    onMount(() => {
        setTimeout(() => {
            hasPageLoaded = true;
        }, 1300);
    });
</script>

{#if !hasPageLoaded}
    <Loader />
{/if}

{#if $page.url.pathname === '/' || $page.url.pathname === '/messages' || $page.url.pathname === '/notifications' || $page.url.pathname === '/settings'}
  <NewNavbar />
{/if}
<slot />

<style>
    :global(body) {
        font-family: 'Manrope', sans-serif;
    }
</style>