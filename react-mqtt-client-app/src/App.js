import React, { useState, useEffect } from 'react';
import mqtt from 'mqtt';
import MqttClientDisplay from './components/MqttClient';
import RustRequestSender from './components/RustRequestSender';
import VideoStreamButton from './components/VideoStreamButton';
import './App.css';

function App() {
  const [client, setClient] = useState(null);
  const [connectStatus, setConnectStatus] = useState('Disconnected');

  useEffect(() => {
    const host = 'ws://localhost:9001';
    const options = {
      keepalive: 60,
      clientId: `mqttjs_app_${Math.random().toString(16).substr(2, 8)}`,
      protocolId: 'MQTT',
      protocolVersion: 4,
      clean: true,
      reconnectPeriod: 1000,
      connectTimeout: 30 * 1000,
      username: 'admin',
      password: 'admin',
      rejectUnauthorized: false,
    };

    setConnectStatus('Connecting');
    const mqttClient = mqtt.connect(host, options);
    setClient(mqttClient);

    return () => {
      if (mqttClient) {
        mqttClient.end(true);
        setConnectStatus('Disconnected');
        setClient(null);
      }
    };
  }, []);

  useEffect(() => {
    if (client) {
      client.on('connect', () => {
        setConnectStatus('Connected');
        console.log('App: MQTT Client Connected');

      });

      client.on('error', (err) => {
        console.error('App: MQTT Connection error: ', err);
        setConnectStatus(`Error: ${err.message}`);
        client.end(true);
      });

      client.on('reconnect', () => {
        setConnectStatus('Reconnecting');
        console.log('App: MQTT Client Reconnecting');
      });

      client.on('close', () => {
        setConnectStatus('Disconnected');
        console.log('App: MQTT Client Disconnected');
      });

    }
  }, [client]);

  return (
    <div className="App">
      <h1>MQTT Client Application</h1>
      <MqttClientDisplay connectStatus={connectStatus} />

      {client && connectStatus === 'Connected' ? (
        <>
          <RustRequestSender mqttClient={client} />
          <VideoStreamButton />
        </>
      ) : (
        <p>Connecting to MQTT broker or MQTT client not available...</p>
      )}
    </div>
  );
}

export default App;