<script>
    import '../app.css'
    import Navbar from '$lib/Navbar.svelte';
    import Footer from '$lib/Footer.svelte';
</script>

<Navbar />
<slot />
<Footer />

<style>
    :global(body) {
        font-family: 'Poppins', sans-serif;
    }
</style>