import paho.mqtt.client as mqtt
import json
import time
import logging
import os
import signal
import sys
from datetime import datetime


BROKER = "localhost"
PORT = 1883
USERNAME = "admin"
PASSWORD = "admin"
TOPIC = "rust/response/livedata"

# Set up logging
if not os.path.exists("logs"):
    os.makedirs("logs")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = f"logs/livedata_{timestamp}.log"

# Configure logger
logger = logging.getLogger("livedata_subscriber")
logger.setLevel(logging.INFO)

# File handler
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter("%(asctime)s - %(message)s")
console_handler.setFormatter(console_formatter)
logger.addHandler(console_handler)


class LiveDataSubscriber:
    def __init__(self):
        self.client_id = f"livedata-subscriber-{timestamp}"
        self.client = mqtt.Client(client_id=self.client_id)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.username_pw_set(USERNAME, PASSWORD)
        self.running = False
        self.message_count = 0

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {BROKER}:{PORT}")
            logger.info(f"Subscribing to topic: {TOPIC}")
            self.client.subscribe(TOPIC)
            print(f"✅ Connected and subscribed to {TOPIC}")
        else:
            logger.error(f"Failed to connect, return code: {rc}")
            print(f"❌ Connection failed with code {rc}")

    def on_message(self, client, userdata, msg):
        self.message_count += 1
        try:
            payload = json.loads(msg.payload.decode())
            
            # Format for console output
            print(f"\n📥 Message #{self.message_count} received on {msg.topic}")
            
            # Log the message with detailed information
            logger.info(f"Message #{self.message_count} received on {msg.topic}")
            logger.info(f"Payload: {json.dumps(payload, indent=2)}")
            
            # Save to separate JSON file (optional)
            msg_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            json_file = f"logs/livedata_msg_{msg_timestamp}.json"
            with open(json_file, "w") as f:
                json.dump(payload, f, indent=2)
            
            print(f"📋 Message details logged to {log_file}")
            print(f"💾 Message saved to {json_file}")
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received: {msg.payload}")
            print(f"⚠️ Invalid JSON received")
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            print(f"❌ Error: {str(e)}")

    def on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"Unexpected disconnection, code: {rc}")
            print(f"⚠️ Unexpected disconnection, code: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
            print("👋 Disconnected from MQTT broker")

    def start(self):
        try:
            self.running = True
            logger.info(f"Connecting to MQTT broker at {BROKER}:{PORT}")
            self.client.connect(BROKER, PORT)
            self.client.loop_start()
            
            print(f"📡 LiveData subscriber started")
            print(f"🔄 Listening for messages on {TOPIC}...")
            print(f"💾 Logging to {log_file}")
            print(f"Press Ctrl+C to exit")
            
            # Keep the script running
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping subscriber...")
            self.stop()
        except Exception as e:
            logger.error(f"Error in MQTT client: {str(e)}")
            print(f"❌ Error in MQTT client: {str(e)}")
            self.stop()

    def stop(self):
        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        logger.info(f"LiveData subscriber stopped. Received {self.message_count} messages.")
        print(f"👋 LiveData subscriber stopped. Received {self.message_count} messages.")


if __name__ == "__main__":
    # Handle Ctrl+C gracefully
    def signal_handler(sig, frame):
        print("\n🛑 Ctrl+C pressed. Stopping subscriber...")
        subscriber.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    
    # Start the subscriber
    subscriber = LiveDataSubscriber()
    subscriber.start()