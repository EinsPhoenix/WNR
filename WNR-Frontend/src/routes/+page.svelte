<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import Chart from 'chart.js/auto';
  import type { ChartData, ChartOptions } from 'chart.js';
  import { BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend } from 'chart.js';
  import dayjs from 'dayjs';
  import weekday from 'dayjs/plugin/weekday.js';
  import { mqttData, liveData, initMqtt } from "$lib/stores/mqttClient";

  dayjs.extend(weekday);
  Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip, Legend);

  let chart1: Chart<'line'>;
  let energycost: HTMLCanvasElement;

  let chart2: Chart<'line'>;
  let multiAxis: HTMLCanvasElement;

  let chart3: Chart<'bar'>;
  let barChart1: HTMLCanvasElement;

  let buildNumber = '';
  let buildColor = '';
  let id = '';

  const MAX_POINTS = 30;

  const data: ChartData<'line'> = {
    labels: [],
    datasets: [{
      label: 'Energy Cost',
      cubicInterpolationMode: 'monotone',
      tension: 0.8,
      data: [],
      backgroundColor: 'rgba(220, 150, 220, 1)',
      borderColor: 'rgba(220, 150, 220, 1)',
      borderWidth: 3
    }]
  };

  const options: ChartOptions<'line'> = { responsive: true, aspectRatio: 2.1, plugins: { legend: { display: false } } };

  const data2: ChartData<'line'> = {
    labels: [],
    datasets: [
      {
        label: 'Temperature',
        cubicInterpolationMode: 'monotone',
        tension: 0.8,
        data: [],
        borderColor: '#FFADAD',
        backgroundColor: 'rgba(255,0,0,0.1)',
        yAxisID: 'y',
      },
      {
        label: 'Humidity',
        cubicInterpolationMode: 'monotone',
        tension: 0.8,
        data: [],
        borderColor: '#A0C4FF',
        backgroundColor: 'rgba(0,0,255,0.1)',
        yAxisID: 'y1',
      }
    ]
  };

  const options2: ChartOptions<'line'> = {
    responsive: true,
    aspectRatio: 2.2,
    interaction: { mode: 'index', intersect: false },
    plugins: { title: { display: true }, legend: { display: true } },
    scales: {
      y: { type: 'linear', display: true, position: 'left' },
      y1: { type: 'linear', display: true, position: 'right', grid: { drawOnChartArea: false } }
    }
  };

  const data3: ChartData<'bar'> = {
    labels: [],
    datasets: [{
      label: 'Production per day',
      data: [],
      backgroundColor: 'rgba(220, 150, 220, 1)',
      borderColor: 'rgba(220, 150, 220, 1)',
      borderWidth: 3
    }]
  };

  const options3: ChartOptions<'bar'> = { responsive: true, aspectRatio: 2.1, plugins: { legend: { display: false } } };

  function updateCharts(payload: any) {
    if (!payload?.data?.length) return;

    const latest = payload.data.at(-1);
    const timestamp = dayjs(latest.timestamp || latest.date).format('HH:mm:ss');
    buildNumber = dayjs(latest.timestamp).format('DD.MM.YYYY');
    buildColor = latest.color;
    id = payload.ids[0]?.id;

    // Chart 1
    data.labels.push(timestamp);
    data.datasets[0].data.push(latest.energy_cost);
    if (data.labels.length > MAX_POINTS) {
      data.labels.shift();
      data.datasets[0].data.shift();
    }

    // Chart 2
    data2.labels.push(timestamp);
    data2.datasets[0].data.push(latest.sensor_data?.temperature ?? null);
    data2.datasets[1].data.push(latest.sensor_data?.humidity ?? null);
    if (data2.labels.length > MAX_POINTS) {
      data2.labels.shift();
      data2.datasets[0].data.shift();
      data2.datasets[1].data.shift();
    }

    // Chart 3
    data3.labels.push(timestamp);
    data3.datasets[0].data.push(latest.energy_consume);
    if (data3.labels.length > MAX_POINTS) {
      data3.labels.shift();
      data3.datasets[0].data.shift();
    }

    chart1.update();
    chart2.update();
    chart3.update();
  }

  onMount(() => {
    initMqtt();

    chart1 = new Chart(energycost, { type: 'line', data, options });
    chart2 = new Chart(multiAxis, { type: 'line', data: data2, options: options2 });
    chart3 = new Chart(barChart1, { type: 'bar', data: data3, options: options3 });

    const unsubscribe = liveData.subscribe(value => updateCharts(value));

    return () => {
      unsubscribe();
      chart1?.destroy();
      chart2?.destroy();
      chart3?.destroy();
    };
  });

  onDestroy(() => {
    chart1?.destroy();
    chart2?.destroy();
    chart3?.destroy();
  });
</script>


<div class="wrapper">
  <div class="box box1">
    <div class="information-wrapper">
      <!-- <div class="energy-cost box-title2">
        Energy costs:
        <div class="cost-number">254 €</div>
        <div class="cost-percentage">-33%</div>
      </div> -->

      <div class="energy-cost box-title2">
        Energy costs:
        <div class="cost-number">254 €</div>
        <div class="cost-percentage">
          -33%
          <svg
            class="cost-icon"
            width="17"
            height="17"
            viewBox="0 0 10 10"
            xmlns="http://www.w3.org/2000/svg"
          >
            <polygon points="5,0 10,10 0,10" />
          </svg>
        </div>
      </div>



      <div class="border"></div>
      <div class="speed box-title2">
        Speed:
        <div class="speed-number">52/h</div>
        <div class="speed-percentage">+0%
          <svg
            class="cost-icon"
            width="17"
            height="17"
            viewBox="0 0 10 10"
            xmlns="http://www.w3.org/2000/svg"
          >
            <polygon points="5,0 10,10 0,10" />
          </svg>
        </div>
      </div>
      <div class="border"></div>
      <div class="fail box-title2">
        Failures:
        <div class="fail-number">0</div>
        <div class="fail-percentage">-12%
          <svg
            class="cost-icon-bad"
            width="17"
            height="17"
            viewBox="0 0 10 10"
            xmlns="http://www.w3.org/2000/svg"
          >
            <polygon points="5,0 10,10 0,10" />
          </svg>
        </div>
      </div>
    </div>
  </div>

  <div class="box box2">
    <div class="box-title">Component information</div>
    <div class="box2-wrapper">
      <div class="build">
        Manufacturing:
        <div class="build-number">{buildNumber}</div>
      </div>
      <div class="color">
        Color:
        <div class="color-number" style="background-color: {buildColor}">{buildColor}</div>
      </div>
      <div class="index">
        Component number:
        <div class="index-number">{id}</div>
      </div>
    </div>
  </div>

  <div class="box box3">
    <div class="box-title">Environmental conditions</div>
    <canvas bind:this={multiAxis}></canvas>
  </div>

  <div class="box box4">
    <div class="box-title">Production per day</div>
    <canvas bind:this={barChart1}></canvas>
  </div>

  <div class="box box5">
    <div class="box-title">Energy costs</div>
    <canvas bind:this={energycost}></canvas>
  </div>
</div>


<style>

    .cost-icon {
      fill: green; /* oder green */
      transform: rotate(0deg); /* oder 180deg für Pfeil nach oben */
    }

    .cost-icon-bad {
      fill: red; /* oder green */
      transform: rotate(0deg); /* oder 180deg für Pfeil nach oben */
    }

    svg {
      margin-left: 10px;
    }

    .build {
        display: flex;
        width: 100%;
        align-items: center;
        justify-content: space-between;
        color: #FB53AC;
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
        color: #FB53AC;
    }

    .color-number {
        background-color: var(--pastel-blue-color);
        padding: 0.3rem;
        border-radius: 8px;
        width: 150px;
        font-weight: bold;
        color: black;
    }

    .index {
        display: flex;
        width: 100%;
        align-items: center;
        justify-content: space-between;
        color: #FB53AC;
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
        font-weight: bolder;
        font-size: 35px;
        display: flex;
        align-items: center;
        justify-content: start;
        /* color: #fb53ac; */
        background: #ff2f9e;
        background: linear-gradient(to top, #db0075 11%, #ffa7ff 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        /* text-shadow: 0px 0px 3px #fff; */
    }

    .box-title2 {
        color: #FB53AC;
        /* background: #FB53AC;
        background: linear-gradient(to top, #FB53AC 11%, #FFC6FF 100%); */


        /* background: #ff2f9e;
        background: linear-gradient(to top, #db0075 11%, #d856d8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent; */
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
        /* color: var(--pastel-green-color); */
        /* background: var(--pastel-green-color); */
        /* -webkit-background-clip: text; */
        /* -webkit-text-fill-color: transparent; */

        /* color: var(--pastel-green-color); */
        color: rgb(87, 87, 87);
        /* text-shadow: 0px 0px 1px rgba(0, 0, 0, 0.8); */
        /* font-weight: bolder; */
        font-size: 1.2rem;
        display: flex;
        flex-direction: row;
        align-items: center;
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
        /* color: var(--pastel-green-color);
        background: var(--pastel-green-color);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent; */

        /* color: var(--pastel-green-color); */
        color: rgb(87, 87, 87);

        /* text-shadow: 0px 0px 1px rgba(0, 0, 0, 0.8); */
        /* font-weight: bolder; */
        font-size: 1.2rem;
        display: flex;
        flex-direction: row;
        align-items: center;
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
        /* color: var(--pastel-red-color);
        background: var(--pastel-red-color);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent; */



        /* color: var(--pastel-red-color); */
        /* text-shadow: 0px 0px 1px rgba(0, 0, 0, 0.8); */
        color: rgb(87, 87, 87);
        /* font-weight: bolder; */
        font-size: 1.2rem;
        display: flex;
        flex-direction: row;
        align-items: center;
    }

    .information-wrapper {
        display: flex;
        align-items: center;
        justify-content: space-evenly;
        height: 100%;
    }

    /* wip */
    .wrapper {
        margin-top: -30px;
        flex: 1;
        display: grid;
        gap: 20px;
        grid-template-columns: repeat(22, 1fr);
        grid-template-rows: repeat(22, 1fr);
        margin-left: var(--navbar-width);

        --s: 200px;
        --c1: rgba(185, 185, 185, 0.2);
        --c2: rgba(220, 220, 220, 0.2);
        --c3: rgba(250, 250, 250, 0.2);

        background: conic-gradient(
                from 75deg,
                var(--c1) 15deg,
                var(--c2) 0 30deg,
                #0000 0 180deg,
                var(--c2) 0 195deg,
                var(--c1) 0 210deg,
                #0000 0
            )
            calc(0.5 * var(--s)) calc(0.5 * var(--s) / 0.577),
            conic-gradient(
                var(--c1) 30deg,
                var(--c3) 0 75deg,
                var(--c1) 0 90deg,
                var(--c2) 0 105deg,
                var(--c3) 0 150deg,
                var(--c2) 0 180deg,
                var(--c3) 0 210deg,
                var(--c1) 0 256deg,
                var(--c2) 0 270deg,
                var(--c1) 0 286deg,
                var(--c2) 0 331deg,
                var(--c3) 0
            );
        background-size: var(--s) calc(var(--s) / 0.577);
        /* background-color: rgb(255, 187, 244); */
    }

    .box {
        /* border: solid var(--pastel-pink-color) 4px; */
        padding: 20px;
        text-align: center;
        background-color: var(--pastel-white-color);
        border-radius: 16px;
        transition: transform 0.3s ease-in-out;
    }

    .box:hover {
        transform: scale(1.02);
        box-shadow: 0 0 10px 2px #BDB2FF, 0 0 1px 4px #BDB2FF inset;
    }

    .box1 {
        grid-row: 2 / span 2;
        grid-column: 2 / span 20;

        padding: 0;
        background-color: rgb(255, 255, 255, 0.8);
        /* background-color: rgb(26, 26, 26, 0.9); */
        color: var(--pastel-pink-color);
    }

    .box2 {
        grid-row: 4 / span 4;
        grid-column: 2 / span 12;

        /* background-color: rgb(249, 246, 238, 0.9); */
        background-color: rgb(255, 255, 255, 0.8);
        /* background-color: rgb(26, 26, 26, 0.9); */
        color: var(--pastel-pink-color);
    }

    .box3 {
        grid-row: 8 / span 8;
        grid-column: 2 / span 12;

        /* background-color: rgb(249, 246, 238, 0.9); */
        background-color: rgb(255, 255, 255, 0.8);
        /* background-color: rgb(26, 26, 26, 0.9); */
        color: var(--pastel-pink-color);
    }

    .box4 {
        grid-row: 10 / span 6;
        grid-column: 14 / span 8;

        /* background-color: rgb(249, 246, 238, 0.9); */
        background-color: rgb(255, 255, 255, 0.8);
        /* background-color: rgb(26, 26, 26, 0.9); */
        color: var(--pastel-pink-color);
    }

    .box5 {
        grid-row: 4 / span 6;
        grid-column: 14 / span 8;

        /* background-color: rgb(249, 246, 238, 0.9); */
        background-color: rgb(255, 255, 255, 0.8);
        /* background-color: rgb(26, 26, 26, 0.9); */
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
            margin-top: 20px;
        }

        .box {
            min-width: 0;
            min-height: 400px;
            margin: 20px;
            /* background-color: black; */
            margin-top: 0;
            margin-bottom: 0;
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