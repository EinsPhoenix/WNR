import json
import uuid
import random
from datetime import datetime, timedelta
import socket
import sys 
import os  



class TcpClient:
    """
    Manages the TCP connection and communication with the Rust server.
    """

    def __init__(self, host="localhost", port=12345):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False

    
    def connect(self):
        """Establishes a connection to the server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"INFO: Connected to server at {self.host}:{self.port}")
            return True
        except socket.error as e:
            print(f"ERROR: Connection failed: {e}")
            self.socket = None
            return False
        except Exception as e:
            print(f"ERROR: Unexpected connection error: {e}")
            self.socket = None
            return False

    
    def authenticate(self, password):
        """Handles password authentication with the server."""
        if not self.connected or not self.socket:
            print("ERROR: Not connected to server.")
            return False

        try:
            
            prompt = self.socket.recv(1024).decode("utf-8")
            print(f"Server: {prompt}", end="")
            self.socket.sendall(password.encode("utf-8"))
            response = self.socket.recv(1024).decode("utf-8")
            print(f"Server: {response}")

            if "Access granted" in response:
                print("INFO: Authentication successful.")
                return True
            else:
                print("ERROR: Authentication failed.")
                self.close()
                return False
        except socket.error as e:
            print(f"ERROR: Socket error during authentication: {e}")
            self.close()
            return False
        except Exception as e:
            print(f"ERROR: Unexpected authentication error: {e}")
            self.close()
            return False

    
    def receive_response(self, buffer_size=4096):
        """Receives a complete JSON response terminated by a newline."""
        if not self.connected or not self.socket:
            print("ERROR: Not connected to server.")
            return None

        try:
            response_data = ""
            
            while not response_data.endswith("\n"):
                chunk = self.socket.recv(buffer_size).decode("utf-8")
                if not chunk:  
                    print("INFO: Server closed the connection.")
                    self.connected = False
                    self.socket = None
                    return None
                response_data += chunk

            
            try:
                return json.loads(response_data.strip())
            except json.JSONDecodeError as e:
                print(f"ERROR: Invalid JSON received: {e}")
                print(f"Raw response data: {response_data}")
                return None
        except socket.error as e:
            print(f"ERROR: Socket error receiving response: {e}")
            self.close()
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error receiving response: {e}")
            self.close()
            return None

    
    def send_json(self, data):
        """Sends a Python dictionary as a JSON string to the server."""
        if not self.connected or not self.socket:
            print("ERROR: Not connected to server.")
            return None

        try:
            json_data = json.dumps(data) + "\n" 
            self.socket.sendall(json_data.encode("utf-8"))
            
            response = self.receive_response()

            if response:
                status = response.get("status", "unknown")
                message = response.get("message", "No message provided")
                if status == "success":
                    print(f"\033[92mServer Response (Success):\033[0m {message}")
                elif status == "error":
                    print(f"\033[91mServer Response (Error):\033[0m {message}")
                else:
                    print(f"Server Response ({status}): {message}")
            else:
                print("WARNING: No valid response received from server for sent data.")

            return response
        except socket.error as e:
            print(f"ERROR: Socket error sending data: {e}")
            self.close()
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error sending data: {e}")
            self.close()
            return None

    
    def close(self):
        """Closes the socket connection if open."""
        if self.socket:
            try:
                self.socket.close()
                print("INFO: Connection closed.")
            except Exception as e:
                print(f"ERROR: Error closing socket: {e}")
            finally:
                self.socket = None
                self.connected = False



colors = ["blue", "green", "red", "yellow", "purple", "orange", "black", "white"]
start_time = datetime(2025, 4, 22, 10, 0)
TOTAL_ENTRIES = 100000000
BATCH_SIZE = 5000


def generate_and_send_data():
    """
    Generates data and sends it in batches via TCP.
    """
    
    server_password = "1234"  
    client = TcpClient()

    
    if not client.connect():
        print("ERROR: Failed to connect to server. Exiting.")
        return
    if not client.authenticate(server_password):
        print("ERROR: Authentication failed. Exiting.")
        return

    print("\nINFO: Authentication successful! Ready to send data batches.")

    data_batch = []
    entries_sent_count = 0

    for i in range(TOTAL_ENTRIES):
        entry = {
            "uuid": str(uuid.uuid4()),
            "color": random.choice(colors),
            "sensor_data": {
                "temperature": round(random.uniform(15.0, 30.0), 1),
                "humidity": random.randint(30, 80),
            },
            "timestamp": (start_time + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S"),
            "energy_consume": round(random.uniform(0.1, 1.0), 3),
            "energy_cost": round(random.uniform(0.005, 0.02), 5),
        }
        data_batch.append(entry)

        if len(data_batch) == BATCH_SIZE:
            payload = {"type": "robotdata", "data": data_batch} 
            print(f"\nINFO: Sending batch of {len(data_batch)} entries...")
            if client.send_json(payload):
                entries_sent_count += len(data_batch)
            else:
                print(f"ERROR: Failed to send batch. Stopping further transmissions.")
                break 
            data_batch = [] 

    
    if data_batch: 
        payload = {"type": "robotdata", "data": data_batch} 
        print(f"\nINFO: Sending final batch of {len(data_batch)} remaining entries...")
        if client.send_json(payload):
            entries_sent_count += len(data_batch)
        else:
            print(f"ERROR: Failed to send final batch.")
    
    print(f"\nINFO: Finished sending data. Total entries attempted: {TOTAL_ENTRIES}, Total entries successfully indicated by send_json: {entries_sent_count}.")

    
    print("INFO: Cleaning up and closing connection...")
    client.close()


if __name__ == "__main__":
    generate_and_send_data()
    print("Datenversand abgeschlossen.")
