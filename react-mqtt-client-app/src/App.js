import React, { useState, useEffect, useCallback, useRef } from 'react';
import mqtt from 'mqtt';
import './App.css';
import Sidebar from './components/Sidebar';
import DashboardView from './views/DashboardView';
import TestView from './views/TestView';
import CheapEnergyView from './views/CheapEnergyView';
import VideoView from './views/VideoView';
import { useTranslation } from 'react-i18next';

const MAX_FRAMES = 120; 
const generateId = () => `react-client-${Math.random().toString(16).substr(2, 8)}`;

function App() {
  const { t } = useTranslation();
  const [client, setClient] = useState(null);
  const [connectStatus, setConnectStatus] = useState('Disconnected');
  const [activeView, setActiveView] = useState('dashboard');
  const [videoState, setVideoState] = useState({ isVisible: false, isMini: false });
  const [isPaused, setIsPaused] = useState(false);
  const [currentFrame, setCurrentFrame] = useState(null);
  const [pauseTimestamp, setPauseTimestamp] = useState(null);

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
  const isPausedRef = useRef(isPaused);
  isPausedRef.current = isPaused;

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
        if (client && client.connected) {
            client.unsubscribe(liveDataTopic, (err) => {
                if (err) console.error(`[App] Error unsubscribing from ${liveDataTopic}:`, err);
            });
        }
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
          setCheapEnergyError(t('app.cheapEnergyError'));
          setIsCheapEnergyLoading(false);
        } else {
          client.publish(requestTopic, JSON.stringify(requestPayload), { qos: 1 }, (pubErr) => {
            if (pubErr) {
              setCheapEnergyError(t('app.cheapEnergyError'));
              setIsCheapEnergyLoading(false);
            }
          });
        }
      });
      
      return () => {
        if (client && client.connected) {
          client.unsubscribe(subscriptionTopic);
        }
      };
    }
  }, [client, client?.connected, t]);

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
                    const fortySecondsAgo = Date.now() - 40000; // 40s Puffer
                    const filteredCache = prevCache.filter(f => f.timestamp > fortySecondsAgo);
                    return [...filteredCache, newFrame];
                });
                if (!isPausedRef.current) {
                    setCurrentFrame(newFrame);
                }
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
      setCheapEnergyError(t('app.cheapEnergyError'));
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

  const handleTogglePause = () => {
    const newIsPaused = !isPaused;
    setIsPaused(newIsPaused);

    if (newIsPaused) {
      setPauseTimestamp(currentFrame?.timestamp || Date.now());
    } else {
      setPauseTimestamp(null);
      if (videoFramesCache.length > 0) {
        setCurrentFrame(videoFramesCache[videoFramesCache.length - 1]);
      }
    }
  };

  const handleRewind = () => {
    if (!isPaused || !currentFrame) return;
    const targetTimestamp = currentFrame.timestamp - 5000; 
    let newFrame = null;
    for (let i = videoFramesCache.length - 1; i >= 0; i--) {
      if (videoFramesCache[i].timestamp <= targetTimestamp) {
        newFrame = videoFramesCache[i];
        break;
      }
    }
    if (!newFrame && videoFramesCache.length > 0) {
      newFrame = videoFramesCache[0];
    }
    if (newFrame) {
      setCurrentFrame(newFrame);
    }
  };

  const handleSeek = (timestamp) => {
    if (!isPaused || videoFramesCache.length === 0) return;
    const closestFrame = videoFramesCache.reduce((prev, curr) => 
      (Math.abs(curr.timestamp - timestamp) < Math.abs(prev.timestamp - timestamp) ? curr : prev)
    );
    if (closestFrame) {
      setCurrentFrame(closestFrame);
    }
  };

  const isMqttConnected = client && connectStatus === 'Connected';

  const videoPlayer = (
    <VideoView
      isMini={videoState.isMini}
      onToggleMini={handleToggleMiniPlayer}
      onClose={handleCloseVideo}
      frameData={currentFrame?.frame || null}
      connectionStatus={videoConnectionStatus}
      isPaused={isPaused}
      onTogglePause={handleTogglePause}
      onRewind={handleRewind}
      onSeek={handleSeek}
      cacheInfo={{
        oldest: videoFramesCache[0]?.timestamp,
        newest: isPaused ? pauseTimestamp : videoFramesCache[videoFramesCache.length - 1]?.timestamp,
      }}
      currentTimestamp={currentFrame?.timestamp}
      showPlaybackControls={isPaused}
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
          /> : <p>{t('app.connecting')}</p>
        )}
        {activeView === 'test' && (
          isMqttConnected ? <TestView mqttClient={client} /> : <p>{t('app.connecting')}</p>
        )}
        {activeView === 'cheap_energy' && (
          isMqttConnected ? <CheapEnergyView 
            energyData={cheapEnergyData}
            isLoading={isCheapEnergyLoading}
            error={cheapEnergyError}
          /> : <p>{t('app.connecting')}</p>
        )}
        {activeView === 'video' && !videoState.isMini && videoPlayer}
      </main>

      {videoState.isMini && videoPlayer}
    </div>
  );
}

export default App;