<script lang="ts">
    import { onMount } from "svelte";
    import { writable } from "svelte/store";
    import { initMqtt, mqttData } from "$lib/stores/mqttClient";

    const items = writable([]);
    let expandedIndex: number | null = null;

    onMount(() => {
        initMqtt();

        const stored = localStorage.getItem("mqtt_items");
        if (stored) {
            items.set(JSON.parse(stored));
        }

        mqttData.subscribe((newData) => {
            if (!newData || newData.length === 0) return;
            items.update((current) => {
                const merged = [...current, ...newData];
                localStorage.setItem("mqtt_items", JSON.stringify(merged));
                return merged;
            });
        });
    });

    function toggleExpand(i: number) {
        expandedIndex = expandedIndex === i ? null : i;
    }
</script>

<div class="list-container">
    {#each $items as msg, i}
        <button
            class="item-button"
            on:click={() => toggleExpand(i)}
            aria-expanded={expandedIndex === i}
        >
            <div class="item-card" style="--i:{i}">
                <div class="timestamp">
                    [{new Date(msg.timestamp).toLocaleTimeString()}]
                </div>
                <div class="item-text">
                    Item #{i + 1} produced
                </div>
                {#if expandedIndex === i}
                    <div class="details">
                        <h3>Summary</h3>
                        <div><strong>Type:</strong> {msg.type}</div>
                        <div><strong>Source:</strong> {msg.source}</div>
                        <div><strong>Timestamp:</strong> {msg.timestamp}</div>

                        <h4>IDs</h4>
                        <ul>
                            {#each msg.ids as id}
                                <li>
                                    <strong>ID:</strong>
                                    {id.id} <br />
                                    <small>UUID: {id.uuid}</small>
                                </li>
                            {/each}
                        </ul>

                        <h4>Data Entries ({msg.data.length})</h4>
                        {#each msg.data as entry, idx}
                            <div class="data-entry">
                                <div>
                                    <strong>Color:</strong>
                                    <span
                                        class="color-box"
                                        style="background-color: {entry.color}"
                                    ></span>
                                    {entry.color}
                                </div>
                                <div>
                                    <strong>Energy Consume:</strong>
                                    {entry.energy_consume.toFixed(8)}
                                </div>
                                <div>
                                    <strong>Energy Cost:</strong>
                                    {entry.energy_cost}
                                </div>
                                <div>
                                    <strong>Timestamp:</strong>
                                    {entry.timestamp}
                                </div>
                                <div><strong>UUID:</strong> {entry.uuid}</div>
                                <div class="sensor-data">
                                    <strong>Sensor Data:</strong>
                                    <ul>
                                        <li>
                                            Humidity: {entry.sensor_data
                                                .humidity}%
                                        </li>
                                        <li>
                                            Temperature: {entry.sensor_data
                                                .temperature} °C
                                        </li>
                                    </ul>
                                </div>
                            </div>
                        {/each}
                    </div>
                {/if}
            </div>
        </button>
    {/each}
</div>

<style>
    :root {
        --pastel-red-color: #ffadad;
        --pastel-orange-color: #ffd6a5;
        --pastel-yellow-color: #fdffb6;
        --pastel-green-color: #caffbf;
        --pastel-lightblue-color: #9bf6ff;
        --pastel-blue-color: #a0c4ff;
        --pastel-purple-color: #bdb2ff;
        --pastel-pink-color: #ffc6ff;
        --pastel-white-color: #fffffc;

        --glass-bg: rgba(255, 255, 255, 0.2);
        --glass-blur: blur(16px);
        --text-color: #2c2c2c;
    }

    .list-container {
        background: linear-gradient(
            135deg,
            var(--pastel-lightblue-color),
            var(--pastel-pink-color)
        );
        min-height: 100vh;
        width: 100vw;
        margin-left: var(--navbar-width);
        padding: 3rem;
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        backdrop-filter: var(--glass-blur);
    }

    .item-card {
        background: var(--glass-bg);
        backdrop-filter: var(--glass-blur);
        border-radius: 1.5rem;
        padding: 1.5rem 2rem;
        box-shadow:
            0 10px 25px rgba(0, 0, 0, 0.1),
            0 0 15px rgba(186, 125, 255, 0.2);
        color: var(--text-color);
        font-family: "Segoe UI", sans-serif;
        animation: fadeInUp 0.6s ease-out forwards;
        opacity: 0;
        transform: translateY(20px);
        animation-delay: calc(var(--i) * 60ms);
    }

    .item-card:hover {
        transform: scale(1.03) rotateZ(-0.5deg);
        box-shadow:
            0 20px 40px rgba(0, 0, 0, 0.15),
            0 0 30px rgba(255, 200, 255, 0.3);
        transition: all 0.3s ease;
    }

    .timestamp {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 0.4rem;
        letter-spacing: 0.5px;
    }

    .item-text {
        font-size: 1.25rem;
        font-weight: 600;
        color: #222;
    }

    button {
        cursor: pointer;
    }

    @keyframes fadeInUp {
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }

    .item-button {
        all: unset;
        display: block;
        width: 100%;
        cursor: pointer;
    }

    .details {
        margin-top: 1rem;
        background: rgba(255 255 255 / 0.15);
        padding: 1rem;
        border-radius: 1rem;
        font-family: monospace;
        max-height: 300px;
        overflow: auto;
        color: #222;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        user-select: text;
        white-space: pre-wrap;
        word-break: break-word;
    }

    .details {
        animation: fadeIn 0.3s ease forwards;
    }
    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }

    .list-container {
        background: linear-gradient(
            135deg,
            var(--pastel-lightblue-color),
            var(--pastel-pink-color)
        );
        min-height: 100vh;
        max-height: 100vh;
        overflow-y: auto;
        width: 100vw;
        margin-left: var(--navbar-width);
        padding: 3rem;
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
        backdrop-filter: var(--glass-blur);
    }

    .item-card {
        background: var(--glass-bg);
        backdrop-filter: var(--glass-blur);
        border-radius: 1.5rem;
        padding: 1.5rem 2rem;
        box-shadow:
            0 10px 25px rgba(0, 0, 0, 0.1),
            0 0 15px rgba(186, 125, 255, 0.2);
        color: var(--text-color);
        font-family: "Segoe UI", sans-serif;
        animation: fadeInUp 0.6s ease-out forwards;
        opacity: 0;
        transform: translateY(20px);
        animation-delay: calc(var(--i) * 60ms);
    }

    .item-card:hover {
        transform: scale(1.03) rotateZ(-0.5deg);
        box-shadow:
            0 20px 40px rgba(0, 0, 0, 0.15),
            0 0 30px rgba(255, 200, 255, 0.3);
        transition: all 0.3s ease;
    }

    .timestamp {
        font-size: 0.85rem;
        color: #666;
        margin-bottom: 0.4rem;
        letter-spacing: 0.5px;
    }

    .item-text {
        font-size: 1.25rem;
        font-weight: 600;
        color: #222;
    }

    button {
        cursor: pointer;
    }

    .item-button {
        all: unset;
        display: block;
        width: 100%;
        cursor: pointer;
    }

    .details {
        margin-top: 1rem;
        background: rgba(255 255 255 / 0.15);
        padding: 1rem 2rem;
        border-radius: 1rem;
        color: #222;
        font-family: "Segoe UI", sans-serif;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
        user-select: text;
        animation: fadeIn 0.3s ease forwards;
    }

    .details h3,
    .details h4 {
        margin-top: 1rem;
        margin-bottom: 0.5rem;
        color: #7b3cff;
    }

    .details ul {
        list-style: inside disc;
        margin-left: 1rem;
        margin-bottom: 1rem;
    }

    .data-entry {
        background: rgba(255 255 255 / 0.3);
        margin-bottom: 1rem;
        padding: 1rem;
        border-radius: 1rem;
    }

    .data-entry strong {
        color: #5a00ff;
    }

    .color-box {
        display: inline-block;
        width: 16px;
        height: 16px;
        border-radius: 0.3rem;
        margin-right: 0.5rem;
        vertical-align: middle;
        border: 1px solid #aaa;
    }

    .sensor-data ul {
        margin-left: 1.2rem;
        list-style: circle;
    }

    @keyframes fadeInUp {
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
</style>