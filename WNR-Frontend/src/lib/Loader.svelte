<div class="loader-wrapper">
    <div class="loader-image">
        <img src="/wnrcutealpha.png" alt="wnr logo" width="100" height="100" />
    </div>
</div>

<style>
    .loader-wrapper {
        height: 100vh;
        background-color: rgb(26, 26, 26);
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
        margin-left: 400px;
    }

    @keyframes rotate {
        from {
            transform: rotate(0deg);
        }
        to {
            transform: rotate(360deg);
        }
    }


    @media (max-width: 768px) {
        .loader-wrapper {
            overflow: hidden;
        }

        .loader-image {
            width: 100%;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }

        img {
            height: 200px;
            width: 200px;
        }
    }

    @media (max-width: 1100px) {
        .loader-wrapper {
            overflow: hidden;
        }

        .loader-image {
            width: 100%;
            justify-content: center;
            align-items: center;
            overflow: hidden;
        }

        img {
            height: 500px;
            width: 500px;
            margin-left: 400px;
        }
    }
</style>