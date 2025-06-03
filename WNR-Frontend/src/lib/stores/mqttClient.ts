import { writable } from 'svelte/store';

export const mqttData = writable<any[]>([]);
export const livedata = writable<any[]>([]);

let client: any;

export function initMqtt() {
  if (typeof window === 'undefined') return;
  if (!window.mqtt) {
    console.error('MQTT global not found: no mqtt.min.js import found');
    return;
  }
  client = window.mqtt.connect('ws://localhost:9001');

  client.on('connect', () => {
    console.log('Connected to MQTT');
    client.subscribe('dobot/data/all');
  });

  client.on('message', (topic, message) => {
    try {
      const data = JSON.parse(message.toString());
      mqttData.update((items) => [data, ...items]);
    } catch (e) {
      console.error('Invalid JSON from MQTT', e);
    }
  });
}