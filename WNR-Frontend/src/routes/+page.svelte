<script lang="ts">
    import { onMount } from "svelte";
    import Chart from 'chart.js/auto';
    import type { ChartData, ChartOptions } from 'chart.js';


    let chart1: Chart<'line'>;
    let energycost: HTMLCanvasElement;

    let chart2: Chart<'line'>;
    let multiAxis: HTMLCanvasElement;

    const data: ChartData<'line'> = {
        labels: ['01.05.', '02.05.', '03.05.', '04.05.', '05.05.', '06.05.', '07.05.'],
        datasets: [
        {
            data: [12, 19, 3, 5, 2, 3, 9],
            backgroundColor: [
            'rgba(255, 198, 255, 1)',
            'rgba(255, 198, 255, 1)',
            'rgba(255, 198, 255, 1)',
            'rgba(255, 198, 255, 1)',
            'rgba(255, 198, 255, 1)',
            'rgba(255, 198, 255, 1)',
            'rgba(255, 198, 255, 1)',
            ],
            borderColor: [
            'rgba(255, 198, 255, 1)',
            'rgba(255, 198, 255, 1)',
            'rgba(255, 198, 255, 1)',
            'rgba(255, 198, 255, 1)',
            'rgba(255, 198, 255, 1)',
            'rgba(255, 198, 255, 1)',
            'rgba(255, 198, 255, 1)',
            ],
            borderWidth: 1
        }
        ]
    };

    const options: ChartOptions<'line'> = {
        responsive: true,
        plugins: {
            legend: {
                display: false
            }
        }
    };

    const data2: ChartData<'line'> = {
    labels: ['01.05.', '02.05.', '03.05.', '04.05.', '05.05.', '06.05.', '07.05.'],
    datasets: [
      {
        label: 'Temperature',
        data: [22, 21, 23, 24, 22, 25, 26],
        borderColor: '#FFADAD',
        backgroundColor: 'rgba(255,0,0,0.1)',
        yAxisID: 'y',
      },
      {
        label: 'Humidity',
        data: [40, 42, 38, 35, 37, 39, 41],
        borderColor: '#A0C4FF',
        backgroundColor: 'rgba(0,0,255,0.1)',
        yAxisID: 'y1',
      }
    ]
  };

  const options2: ChartOptions<'line'> = {
    responsive: true,
    interaction: {
      mode: 'index',
      intersect: false,
    },
    plugins: {
      title: {
        display: true,
      },
      legend: {
        display: true
      }
    },
    scales: {
      y: {
        type: 'linear',
        display: true,
        position: 'left'
      },
      y1: {
        type: 'linear',
        display: true,
        position: 'right',
        grid: {
          drawOnChartArea: false
        }
      }
    }
  };

    onMount(() => {
        chart1 = new Chart(energycost, {
        type: 'line',
        data,
        options
        });
        chart2 = new Chart(multiAxis, {
            type: 'line',
            data: data2,
            options: options2
        });
        return () => {
            chart1?.destroy();
            chart2?.destroy();
        };
    });
</script>

<div class="wrapper">
    <div class="box box1">

        <div class="information-wrapper">
            <div class="energy-cost">
                Energy costs
                <div class="cost-number">
                    254 €
                </div>
                <div class="cost-percentage">
                    -33%
                </div>
            </div>

            <div class="border"></div>

            <div class="speed">
                Speed:
                <div class="speed-number">
                    52/h
                </div>
                <div class="speed-percentage">
                    +0%
                </div>
            </div>

            <div class="border"></div>

            <div class="fail">
                Failures:
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
            Component information
        </div>

        <div class="box2-wrapper">
            <div class="build">
                Manufacturing:
                <div class="build-number">
                    24.04.2025
                </div>
            </div>

            <div class="color">
                Color:
                <div class="color-number">
                    Blue
                </div>
            </div>

            <div class="index">
                Component number:
                <div class="index-number">
                    X1234
                </div>
            </div>
        </div>
    </div>

    <div class="box box3">
        <div class="box-title">
            Environmental conditions
        </div>

        <canvas bind:this={multiAxis}></canvas>
    </div>

    <div class="box box4">
        <div class="box-title">
            Components per day
        </div>
    </div>

    <div class="box box5">
        <div class="box-title">
            Energy costs
        </div>

        <canvas bind:this={energycost}></canvas>
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
        transition: transform 0.3s ease-in-out;
    }

    .box:hover {
        transform: scale(1.02);
    }

    .box1 {
        grid-row: 2 / span 2;
        grid-column: 2 / span 20;

        padding: 0;
        background-color: rgb(26, 26, 26);
        color: var(--pastel-pink-color);
    }

    .box2 {
        grid-row: 4 / span 4;
        grid-column: 2 / span 12;

        background-color: rgb(26, 26, 26);
        color: var(--pastel-pink-color);
    }

    .box3 {
        grid-row: 8 / span 8;
        grid-column: 2 / span 12;

        background-color: rgb(26, 26, 26);
        color: var(--pastel-pink-color);
    }

    .box4 {
        grid-row: 10 / span 6;
        grid-column: 14 / span 8;

        background-color: rgb(26, 26, 26);
        color: var(--pastel-pink-color);
    }

    .box5 {
        grid-row: 4 / span 6;
        grid-column: 14 / span 8;

        background-color: rgb(26, 26, 26);
        color: var(--pastel-pink-color);
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

        .box2 {
            min-height: 0;
        }

        .box1 {
            min-height: 0;
        }

        .border {
            height: 60px;
        }
    }

    @media (max-width: 1200px) {
        .box-title {
            font-size: 30px;
        }
    }
</style>