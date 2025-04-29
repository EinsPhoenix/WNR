<div class="loader-wrapper">
    <div class="loader-image">
        <img src="/wnrcutealpha.png" alt="wnr logo" width="100" height="100" />
    </div>
</div>

<style>
    .loader-wrapper {
        height: 100vh;
        background-color: var(--background-color);
    }

    .loader-image {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 100%;
        height: 100%;
    }

    img {
        height: 500px;
        width: 500px;
        animation: rotate 1.5s ease-in-out infinite;
    }

    @keyframes rotate {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }
</style>