<script>
    import '../app.css'
    import Navbar from '$lib/Navbar.svelte';
    import Footer from '$lib/Footer.svelte';
    import Loader from '$lib/Loader.svelte';
    import { onMount } from 'svelte';

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

<Navbar />
<slot />
<!-- <Footer /> -->

<style>
    :global(body) {
        font-family: 'Poppins', sans-serif;
    }
</style>