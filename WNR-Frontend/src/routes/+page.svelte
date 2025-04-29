<div class="wrapper">
    <div class="box box1">
        <h1 class="box-title">Manufactured at:</h1>
        <p class="box-text">
            "Manufactured at"
            indicates the exact time a product was made.
            It shows when the manufacturing process was completed
        </p>
        <h1 class="box-timestamp">14:23</h1>
    </div>
    <div class="box">
        <h1 class="box-title">Manufactured at:</h1>
    </div>
    <div class="box">
        <h1 class="box-title">Manufactured at:</h1>
    </div>
    <div class="box">
        <h1 class="box-title">Manufactured at:</h1>
    </div>
    <div class="box">
        <h1 class="box-title">Manufactured at:</h1>
    </div>
    <div class="box">
        <h1 class="box-title">Manufactured at:</h1>
    </div>
</div>

<style>
    .wrapper {
        height: 100%;
        display: flex;
        flex-wrap: wrap;
        gap: 40px;
        align-content: flex-start;
        margin: 40px;
    }

    .box {
        display: flex;
        background-color: var(--primary-color);
        height: 26rem;
        min-height: 25rem;
        flex: 0 0 calc(33.333% - 30px);
        box-sizing: border-box;
        -webkit-box-shadow: 0px 0px 20px 0px rgba(0,0,0,0.7); 
        box-shadow: 0px 0px 20px 0px rgba(0,0,0,0.7);
        border-radius: 7px;
        flex-direction: column;
    }

    .box-title {
        background-color: var(--background-color);
        border-top-right-radius: 7px;
        border-top-left-radius: 7px;
        height: 80px;
        color: #fcafbc;
        font-size: 3rem;
        text-align: start;
        padding-left: 2rem;
        font-weight: bolder;
        flex-shrink: 0;
        text-shadow: 1px 1px 1px #000;
    }

    .box-text {
        color: black;
        flex-shrink: 0;
        padding: 1rem;
        font-size: 1.3rem;
    }

    .box-timestamp {
        color: black;
        display: flex;
        align-items: flex-end;
        flex-grow: 1;
        padding: 1rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 7rem;
        font-weight: bolder;
    }

    @media (max-width: 1560px) {
        .box-title {
            font-size: 2.5rem;
        }
    }

    @media (max-width: 1350px) {
        .box-title {
            font-size: 2rem;
        }
    }

    @media (max-width: 1320px) {
        .box {
            flex: 0 0 calc(50% - 20px);
        }
    }

    @media (max-width: 900px) {
        .box {
            flex: 0 0 100%;
        }

        .box-text {
            font-size: 1rem;
        }

        .box-timestamp {
            font-size: 6rem;
        }
    }
</style>