let client;

export async function connectMqtt() {
  if (typeof window === 'undefined') return;

  const mqtt = (await import('mqtt')).default;

  client = mqtt.connect('ws://192.168.1.100:9001');

  client.on('connect', () => {
    console.log('MQTT connected');
  });
}

export function publish(topic, message) {
  if (!client) return;
  client.publish(topic, message);
}