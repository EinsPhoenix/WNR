import paho.mqtt.client as mqtt
import json
import time

class MQTTWebSocketClient:
    def __init__(self, host="192.168.1.100", port=9001, keepalive=60):
        """
        MQTT WebSocket Client
        
        Args:
            host (str): MQTT Broker IP-Adresse
            port (int): WebSocket Port (Standard: 9001)
            keepalive (int): Keepalive Intervall in Sekunden
        """
        self.host = host
        self.port = port
        self.keepalive = keepalive
        self.client = mqtt.Client(transport="websockets")
        
        # Event Callbacks setzen
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_publish = self.on_publish
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback für erfolgreiche Verbindung"""
        if rc == 0:
            print(f"✅ Erfolgreich mit MQTT Broker verbunden: {self.host}:{self.port}")
            print(f"Connection flags: {flags}")
        else:
            print(f"❌ Verbindung fehlgeschlagen mit Code: {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback für Verbindungstrennung"""
        if rc != 0:
            print(f"⚠️ Unerwartete Verbindungstrennung: {rc}")
        else:
            print("🔌 Verbindung getrennt")
    
    def on_message(self, client, userdata, msg):
        """Callback für eingehende Nachrichten"""
        try:
            payload = msg.payload.decode('utf-8')
            print(f"📨 Nachricht empfangen:")
            print(f"   Topic: {msg.topic}")
            print(f"   Payload: {payload}")
            print(f"   QoS: {msg.qos}")
            print("-" * 50)
        except Exception as e:
            print(f"❌ Fehler beim Verarbeiten der Nachricht: {e}")
    
    def on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback für erfolgreiche Subscription"""
        print(f"📋 Topic abonniert mit Message ID: {mid}, QoS: {granted_qos}")
    
    def on_publish(self, client, userdata, mid):
        """Callback für erfolgreiche Veröffentlichung"""
        print(f"📤 Nachricht veröffentlicht mit Message ID: {mid}")
    
    def connect(self):
        """Verbindung zum MQTT Broker herstellen"""
        try:
            print(f"🔗 Verbinde mit MQTT Broker {self.host}:{self.port} über WebSocket...")
            self.client.connect(self.host, self.port, self.keepalive)
            return True
        except Exception as e:
            print(f"❌ Verbindungsfehler: {e}")
            return False
    
    def disconnect(self):
        """Verbindung trennen"""
        self.client.disconnect()
    
    def subscribe(self, topic, qos=0):
        """Topic abonnieren"""
        result = self.client.subscribe(topic, qos)
        if result[0] == mqtt.MQTT_ERR_SUCCESS:
            print(f"📋 Abonniere Topic: {topic} (QoS: {qos})")
        else:
            print(f"❌ Fehler beim Abonnieren von {topic}: {result}")
        return result
    
    def publish(self, topic, payload, qos=0, retain=False):
        """Nachricht veröffentlichen"""
        try:
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            
            result = self.client.publish(topic, payload, qos, retain)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"📤 Nachricht gesendet an {topic}: {payload}")
            else:
                print(f"❌ Fehler beim Senden: {result.rc}")
            return result
        except Exception as e:
            print(f"❌ Publish-Fehler: {e}")
            return None
    
    def start_loop(self):
        """Starte den MQTT Loop (non-blocking)"""
        self.client.loop_start()
    
    def stop_loop(self):
        """Stoppe den MQTT Loop"""
        self.client.loop_stop()
    
    def loop_forever(self):
        """Blockierender Loop"""
        self.client.loop_forever()


def main():
    """Beispiel für die Verwendung des MQTT WebSocket Clients"""
    
    # Client erstellen
    mqtt_client = MQTTWebSocketClient(host="192.168.1.100", port=9001)
    
    # Verbindung herstellen
    if mqtt_client.connect():
        # Non-blocking Loop starten
        mqtt_client.start_loop()
        
        # Warten bis Verbindung steht
        time.sleep(2)
        
        # Topics abonnieren
        mqtt_client.subscribe("test/topic", qos=1)
        mqtt_client.subscribe("benchmark/+", qos=0)  # Wildcard für alle benchmark topics
        
        # Beispiel-Nachrichten senden
        mqtt_client.publish("test/topic", "Hello from Python WebSocket Client!")
        mqtt_client.publish("benchmark/data", {"speed": 123.45, "timestamp": time.time()})
        
        try:
            print("\n🔄 Client läuft... (Strg+C zum Beenden)")
            print("Warte auf Nachrichten...")
            
            # Hauptloop
            while True:
                time.sleep(1)
                
                # Beispiel: Regelmäßig Daten senden
                if int(time.time()) % 10 == 0:  # Alle 10 Sekunden
                    mqtt_client.publish("heartbeat", {
                        "timestamp": time.time(),
                        "status": "alive"
                    })
                
        except KeyboardInterrupt:
            print("\n🛑 Beende Client...")
        finally:
            mqtt_client.stop_loop()
            mqtt_client.disconnect()
            print("👋 Client beendet")
    else:
        print("❌ Konnte keine Verbindung herstellen")


if __name__ == "__main__":
    main()