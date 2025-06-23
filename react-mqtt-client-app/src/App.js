import React, { useState, useEffect, useRef } from 'react';
import mqtt from 'mqtt';
import Sidebar from './components/Sidebar';
import DashboardView from './views/DashboardView';
import TestView from './views/TestView';
import VideoView from './views/VideoView';
import CheapEnergyView from './views/CheapEnergyView';
import './App.css';

const generateId = () => `react-client-${Math.random().toString(16).substr(2, 8)}`;

function App() {
  const [client, setClient] = useState(null);
  const [connectStatus, setConnectStatus] = useState('Disconnected');
  const [activeView, setActiveView] = useState('dashboard');
  const [videoState, setVideoState] = useState({ isVisible: false, isMini: false });

  const [temperatureData, setTemperatureData] = useState([]);
  const [humidityData, setHumidityData] = useState([]);
  const [energyConsumptionData, setEnergyConsumptionData] = useState([]);
  const [energyCostData, setEnergyCostData] = useState([]);

  const [cheapEnergyData, setCheapEnergyData] = useState(null);
  const [isCheapEnergyLoading, setIsCheapEnergyLoading] = useState(true);
  const [cheapEnergyError, setCheapEnergyError] = useState('');
  const cheapEnergyRequested = useRef(false);

  const [videoFramesCache, setVideoFramesCache] = useState([]);
  const [videoConnectionStatus, setVideoConnectionStatus] = useState('disconnected');
  const wsRef = useRef(null);
  const frameBufferRef = useRef(new Map());
  const mqttClientRef = useRef(null);

  useEffect(() => {
    
    if (mqttClientRef.current) {
      return;
    }
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
    mqttClientRef.current = mqttClient; 
    setClient(mqttClient); 

    return () => {
      if (mqttClientRef.current) {
        console.log('App: Disconnecting MQTT client...');
        mqttClientRef.current.end(true);
        mqttClientRef.current = null;
      }
    };
  }, []); 

  useEffect(() => {
    if (!client) return;

    const handleConnect = () => setConnectStatus('Connected');
    
    const handleError = (err) => {
      
      console.error('App: MQTT Connection error: ', err);
    };

    const handleReconnect = () => setConnectStatus('Reconnecting');
    const handleClose = () => setConnectStatus('Disconnected');

    const handleMessage = (topic, message) => {
      const messageString = message.toString();
      const topicParts = topic.split('/');
      if (topic === 'rust/response/livedata') {
        handleLiveDataMessage(messageString);
      } else if (topicParts.length >= 3 && topicParts[0] === 'rust' && topicParts[1] === 'response') {
        handleCheapEnergyResponse(messageString);
      }
    };

    client.on('connect', handleConnect);
    client.on('error', handleError);
    client.on('reconnect', handleReconnect);
    client.on('close', handleClose);
    client.on('message', handleMessage);

    return () => {
      client.off('connect', handleConnect);
      client.off('error', handleError);
      client.off('reconnect', handleReconnect);
      client.off('close', handleClose);
      client.off('message', handleMessage);
    };
  }, [client]);

  useEffect(() => {
    if (client && client.connected) {
      const liveDataTopic = 'rust/response/livedata';
      client.subscribe(liveDataTopic, { qos: 0 }, (err) => {
        if (err) console.error(`[App] Subscription error to ${liveDataTopic}:`, err);
      });
      return () => {
        console.error(` Subscription error`);
        if (client.connected) client.unsubscribe(liveDataTopic);
      };
    }
  }, [client, client?.connected]);

  useEffect(() => {
    if (client && client.connected && !cheapEnergyRequested.current) {
      cheapEnergyRequested.current = true;
      setIsCheapEnergyLoading(true);
      setCheapEnergyError('');

      const requestingClientId = generateId();
      const subscriptionTopic = `rust/response/${requestingClientId}/#`;
      const requestTopic = 'rust/request';
      const requestPayload = {
        client_id: requestingClientId,
        request: 'cheap_energy',
        data: {}
      };

      client.subscribe(subscriptionTopic, { qos: 1 }, (err) => {
        if (err) {
          setCheapEnergyError('Fehler beim Abonnieren des MQTT-Topics.');
          setIsCheapEnergyLoading(false);
        } else {
          client.publish(requestTopic, JSON.stringify(requestPayload), { qos: 1 }, (pubErr) => {
            if (pubErr) {
              setCheapEnergyError('Fehler beim Senden der MQTT-Anfrage.');
              setIsCheapEnergyLoading(false);
            }
          });
        }
      });
      
    }
  }, [client, client?.connected]);

  useEffect(() => {
    
    if (!videoState.isVisible) {
      return;
    }

    let ws;
    
    setVideoConnectionStatus('connecting');
    try {
      ws = new WebSocket('ws://localhost:1337');
      wsRef.current = ws;

      ws.onopen = () => setVideoConnectionStatus('connected');
      
      ws.onclose = () => {
        
        if (wsRef.current === ws) {
          setVideoConnectionStatus('disconnected');
          wsRef.current = null;
        }
      };
      
      ws.onerror = () => {
        if (wsRef.current === ws) {
          setVideoConnectionStatus('error');
        }
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.type === 'video_frame_chunk') {
            const frameData = frameBufferRef.current.get(data.frame_index);
            if (frameData) {
              frameData.chunks[data.chunk_index] = data.chunk_data;
              frameData.received++;
              if (frameData.received === frameData.total_chunks) {
                const completeFrame = frameData.chunks.join('');
                const now = Date.now();
                const newFrame = { frame: completeFrame, timestamp: now };
                setVideoFramesCache(prevCache => {
                    const tenSecondsAgo = Date.now() - 10000;
                    const filteredCache = prevCache.filter(f => f.timestamp > tenSecondsAgo);
                    return [...filteredCache, newFrame];
                });
                frameBufferRef.current.delete(data.frame_index);
              }
            }
          } else if (data.type === 'video_frame_start') {
            frameBufferRef.current.set(data.frame_index, {
              chunks: new Array(data.total_chunks),
              received: 0,
              total_chunks: data.total_chunks
            });
          }
        } catch (e) { console.error('Error parsing video message:', e); }
      };
    } catch (error) {
      setVideoConnectionStatus('error');
      console.error('Video connection error:', error);
    }

    return () => {
      if (ws) {
        
        ws.onopen = null;
        ws.onclose = null;
        ws.onerror = null;
        ws.onmessage = null;
        ws.close();
        if (wsRef.current === ws) {
            wsRef.current = null;
        }
      }
    };
  }, [videoState.isVisible]); 

  const handleLiveDataMessage = (messageString) => {
    try {
      const parsedMessage = JSON.parse(messageString);
      if (parsedMessage.type === "robotdata" && Array.isArray(parsedMessage.data)) {
        const newTempPoints = [], newHumidityPoints = [], newEnergyConsumePoints = [], newEnergyCostPoints = [];
        parsedMessage.data.forEach(item => {
          const ts = new Date(item.timestamp).toLocaleTimeString();
          if (item.sensor_data) {
            if (typeof item.sensor_data.temperature === 'number') newTempPoints.push({ time: ts, value: item.sensor_data.temperature });
            if (typeof item.sensor_data.humidity === 'number') newHumidityPoints.push({ time: ts, value: item.sensor_data.humidity });
          }
          if (typeof item.energy_consume === 'number') newEnergyConsumePoints.push({ time: ts, value: item.energy_consume });
          if (typeof item.energy_cost === 'number') newEnergyCostPoints.push({ time: ts, value: item.energy_cost });
        });
        if (newTempPoints.length > 0) setTemperatureData(prev => [...prev, ...newTempPoints].slice(-50));
        if (newHumidityPoints.length > 0) setHumidityData(prev => [...prev, ...newHumidityPoints].slice(-50));
        if (newEnergyConsumePoints.length > 0) setEnergyConsumptionData(prev => [...prev, ...newEnergyConsumePoints].slice(-50));
        if (newEnergyCostPoints.length > 0) setEnergyCostData(prev => [...prev, ...newEnergyCostPoints].slice(-50));
      }
    } catch (e) {
      console.error(`[App] Failed to parse live data MQTT message JSON:`, e, messageString);
    }
  };

  const handleCheapEnergyResponse = (messageString) => {
    try {
      const parsedMessage = JSON.parse(messageString);
      if (Array.isArray(parsedMessage)) {
        const sortedData = parsedMessage.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
        setCheapEnergyData(sortedData);
      }
    } catch (e) {
      setCheapEnergyError('Fehler beim Verarbeiten der Energiedaten.');
      setCheapEnergyData([]);
    } finally {
      setIsCheapEnergyLoading(false);
    }
  };

  const handleViewChange = (view) => {
    setActiveView(view);
    if (view === 'video') {
      setVideoState({ isVisible: true, isMini: false });
    } else if (!videoState.isMini) {
      setVideoState({ isVisible: false, isMini: false });
    }
  };

  const handleToggleMiniPlayer = () => {
    setVideoState(prevState => {
      const newIsMini = !prevState.isMini;
      if (newIsMini) {
        
        if (activeView === 'video') {
          setActiveView('dashboard');
        }
      } else {
        
        setActiveView('video');
      }
      return { isVisible: true, isMini: newIsMini };
    });
  };

  const handleCloseVideo = () => {
    setVideoState({ isVisible: false, isMini: false });
    if (activeView === 'video') {
      setActiveView('dashboard');
    }
  };

  const isMqttConnected = client && connectStatus === 'Connected';
  const latestFrame = videoFramesCache.length > 0 ? videoFramesCache[videoFramesCache.length - 1].frame : null;

  const videoPlayer = (
    <VideoView
      isMini={videoState.isMini}
      onToggleMini={handleToggleMiniPlayer}
      onClose={handleCloseVideo}
      frameData={latestFrame}
      connectionStatus={videoConnectionStatus}
    />
  );

  return (
    <div className="App">
      <Sidebar activeView={activeView} setActiveView={handleViewChange} connectStatus={connectStatus} />
      
      <main className="main-content">
        {activeView === 'dashboard' && (
          isMqttConnected ? <DashboardView 
            temperatureData={temperatureData}
            humidityData={humidityData}
            energyConsumptionData={energyConsumptionData}
            energyCostData={energyCostData}
          /> : <p>Verbinde mit MQTT-Broker...</p>
        )}
        {activeView === 'test' && (
          isMqttConnected ? <TestView mqttClient={client} /> : <p>Verbinde mit MQTT-Broker...</p>
        )}
        {activeView === 'cheap_energy' && (
          isMqttConnected ? <CheapEnergyView 
            energyData={cheapEnergyData}
            isLoading={isCheapEnergyLoading}
            error={cheapEnergyError}
          /> : <p>Verbinde mit MQTT-Broker...</p>
        )}
        {activeView === 'video' && !videoState.isMini && videoPlayer}
      </main>

      {videoState.isMini && videoPlayer}
    </div>
  );
}

export default App;