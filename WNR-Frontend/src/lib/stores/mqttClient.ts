// import { writable } from 'svelte/store';

// export const mqttData = writable<any[]>([]);
// export const livedata = writable<any[]>([]);
// export const loading = writable(false);
// export const summary = writable<any>(null);

// let client: any;
// const clientId = 'client-1';
// const pendingRequests = new Map<string, any[]>();

// export function initMqtt() {
//   if (typeof window === 'undefined') return;
//   if (!window.mqtt) {
//     console.error('MQTT global not found: no mqtt.min.js import found');
//     return;
//   }

//   client = window.mqtt.connect('ws://localhost:9001');

//   client.on('connect', () => {
//     console.log('Connected to MQTT');
//     client.subscribe(`rust/response/livedata`);
//     client.subscribe(`rust/response/${clientId}/#`);
//     client.subscribe(`rust/uuid/${clientId}`);
//   });

//   client.on('message', (topic: string, message: Uint8Array) => {
//     const payload = message.toString();
//     try {
//       const data = JSON.parse(payload);

//       if (topic === 'rust/response/livedata') {
//         livedata.set(data.data);
//         return;
//       }

//       if (topic.startsWith(`rust/uuid/${clientId}`)) {
//         mqttData.update((items) => [data, ...items]);
//         return;
//       }

//       const match = topic.match(/rust\/response\/[^/]+\/([^/]+)(\/page\/(\d+))?/);
//       if (!match) return;
//       const [_, request, __, page] = match;
      
//       if (data.type === 'summary') {
//         summary.set(data);
//         loading.set(false);
//         return;
//       }

//       if (data.type === 'paginated') {
//         const reqId = data.request_id;
//         const items = pendingRequests.get(reqId) || [];
//         items.push(...data.data);
//         pendingRequests.set(reqId, items);

//         if (data.page >= data.total_pages) {
//           mqttData.set(pendingRequests.get(reqId));
//           pendingRequests.delete(reqId);
//           loading.set(false);
//         }
//       } else {
//         mqttData.set(Array.isArray(data) ? data : [data]);
//         loading.set(false);
//       }
//     } catch (e) {
//       console.error('MQTT JSON Error:', e);
//     }
//   });
// }

// export function sendRequest(req: any) {
//   if (!client) return;
//   loading.set(true);
//   client.publish('rust/request', JSON.stringify(req));
// }



// ----------------------------------------------------------------------



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

  const options = {
    username: 'admin',
    password: 'admin',
    protocol: 'ws',
  };

  client = window.mqtt.connect('ws://192.168.1.100:9001', options);

  client.on('connect', () => {
    console.log('Connected to MQTT');
    client.subscribe('rust/response/livedata');
  });

  client.on('reconnect', () => {
    console.log("mqtt reconnecting");
  })

  client.on('message', (topic, message) => {
    try {
      const data = JSON.parse(message.toString());
      let storage_data = localStorage.setItem("data", data);
      mqttData.update((items) => [data, ...items]);
      // console.log(data);
    } catch (e) {
      console.error('Invalid JSON from MQTT', e);
    }
  });
}