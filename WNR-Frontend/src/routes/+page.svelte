<div class="wrapper">
    <div class="box box1">

        <div class="information-wrapper">
            <div class="energy-cost">
                Energie Kosten
                <div class="cost-number">
                    254 €
                </div>
                <div class="cost-percentage">
                    -33%
                </div>
            </div>

            <div class="border"></div>

            <div class="speed">
                Geschwindigkeit:
                <div class="speed-number">
                    52/h
                </div>
                <div class="speed-percentage">
                    +0%
                </div>
            </div>

            <div class="border"></div>

            <div class="fail">
                Fehlschläge:
                <div class="fail-number">
                    0
                </div>
                <div class="fail-percentage">
                    -12%
                </div>
            </div>
        </div>
    </div>

    <div class="box box2">
        <div class="box-title">
            Bauteilinformationen
        </div>

        <div class="box2-wrapper">
            <div class="build">
                Fertigung:
                <div class="build-number">
                    24.04.2025
                </div>
            </div>

            <div class="color">
                Farbe:
                <div class="color-number">
                    Blau
                </div>
            </div>

            <div class="index">
                Bauteilnummer:
                <div class="index-number">
                    X1234
                </div>
            </div>
        </div>
    </div>

    <div class="box box3">
        Box 3
    </div>

    <div class="box box4">
        Box 4
    </div>

    <div class="box box5">
        <div class="box-title">
            Energiekosten
        </div>
    </div>
</div>

<style>
    .build {
        display: flex;
        width: 100%;
        align-items: center;
        justify-content: space-between;
    }

    .build-number {
        padding: 0.5rem;
        width: 150px;
    }

    .color {
        display: flex;
        width: 100%;
        align-items: center;
        justify-content: space-between;
    }

    .color-number {
        background-color: blue;
        padding: 0.5rem;
        border-radius: 8px;
        width: 150px;
        font-weight: bold;
    }

    .index {
        display: flex;
        width: 100%;
        align-items: center;
        justify-content: space-between;
    }

    .index-number {
        padding: 0.5rem;
        width: 150px;
    }

    .box2-wrapper {
        display: flex;
        flex-direction: column;
        align-items: start;
        height: 80%;
        justify-content: space-evenly;
        font-size: 20px;
    }

    .box-title {
        font-weight: bold;
        font-size: 35px;
        display: flex;
        align-items: center;
        justify-content: start;
    }

    .border {
        border: solid 1px var(--pastel-pink-color);
        height: 60%;
    }

    .energy-cost {
        display: flex;
        flex-direction: column;
        text-align: start;
    }

    .cost-number {
        font-weight: bold;
        font-size: 30px;
    }

    .cost-percentage {
        color: var(--pastel-green-color);
    }

    .speed {
        display: flex;
        flex-direction: column;
        text-align: start;
    }

    .speed-number {
        font-weight: bold;
        font-size: 30px;
    }

    .speed-percentage {
        color: var(--pastel-green-color);
    }

    .fail {
        display: flex;
        flex-direction: column;
        text-align: start;
    }

    .fail-number {
        font-weight: bold;
        font-size: 30px;
    }

    .fail-percentage {
        color: var(--pastel-red-color);
    }

    .information-wrapper {
        display: flex;
        align-items: center;
        justify-content: space-evenly;
        height: 100%;
    }

    .wrapper {
        flex: 1;
        display: grid;
        gap: 10px;
        grid-template-columns: repeat(22, 1fr);
        grid-template-rows: repeat(22, 1fr);
        margin-left: var(--navbar-width);
    }

    .box {
        border: solid 2px;
        padding: 20px;
        text-align: center;
        background-color: var(--pastel-white-color);
        border-radius: 8px;
    }

    .box1 {
        grid-row: 2 / span 3;
        grid-column: 2 / span 20;

        padding: 0;
        background-color: rgb(26, 26, 26);
        color: var(--pastel-pink-color);
    }

    .box2 {
        grid-row: 5 / span 7;
        grid-column: 2 / span 12;

        background-color: rgb(26, 26, 26);
        color: var(--pastel-pink-color);
    }

    .box3 {
        grid-row: 12 / span 10;
        grid-column: 2 / span 12;
    }

    .box4 {
        grid-row: 11 / span 11;
        grid-column: 14 / span 8;
    }

    .box5 {
        grid-row: 5 / span 6;
        grid-column: 14 / span 8;
    }


    @media (max-width: 768px) {
        .wrapper {
            margin-left: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .box {
            min-width: 0;
            min-height: 400px;
            margin: 20px;
        }
    }

    @media (max-width: 1100px) {
        .wrapper {
            display: flex;
            flex-direction: column;
            height: 100vh;
        }

        .box {
            min-width: 0;
            min-height: 400px;
            margin: 20px;
        }
    }

    @media (max-width: 1200px) {
        .box-title {
            font-size: 30px;
        }
    }
</style>