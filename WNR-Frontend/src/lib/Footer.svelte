<script>
    const currentYear = new Date().getFullYear();
</script>

<footer>
    <div class="footer-content">
        <p class="copyright">&copy; {currentYear} WNR | Made by [WNR]</p>
    </div>
</footer>

<style>
    footer {
        background-color: var(--background-color);
        padding: 0.5rem 0;
        font-family: 'Poppins', sans-serif;
        box-shadow: 0px 0px 10px 2px rgba(0,0,0,0.75);
        -webkit-box-shadow: 0px 0px 10px 2px rgba(0,0,0,0.75);
        -moz-box-shadow: 0px 0px 10px 2px rgba(0,0,0,0.75);
    }

    .footer-content {
        max-width: 100%;
        margin: 0 auto;
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0 2rem;
    }

    .copyright {
        font-size: 0.9rem;
        margin: 0;
        color: var(--primary-color);
    }

    @media (max-width: 768px) {
        .footer-content {
            flex-direction: column;
            text-align: center;
            gap: 1rem;
        }
    }
</style>