import socket
import json
import asyncio
import uuid

class Database_Imp:
    def __init__(self, db_connector_ip="localhost", db_connector_port=12345, password="1234"):
        self.db_ip = db_connector_ip
        self.db_port = db_connector_port
        self.password = password
        self.reader = None
        self.writer = None
        self.connected = False
        self.authenticated = False

    async def connect(self):
        """Establishes an async TCP connection to the database server."""
        try:
            self.reader, self.writer = await asyncio.open_connection(self.db_ip, self.db_port)
            self.connected = True
            print(f"Connected to database server at {self.db_ip}:{self.db_port}")
            
            if await self._authenticate():
                return True
            else:
                await self.disconnect()
                return False
                
        except Exception as e:
            print(f"Connection failed: {e}")
            self.reader = None
            self.writer = None
            self.connected = False
            return False

    async def _authenticate(self):
        """Handles password authentication with the server."""
        if not self.connected or not self.writer:
            return False

        try:

            prompt_data = await self.reader.read(1024)
            prompt = prompt_data.decode("utf-8")
            print(f"Server: {prompt}", end="")
            
            self.writer.write(self.password.encode("utf-8"))
            await self.writer.drain()
            
            response_data = await self.reader.read(1024)
            response = response_data.decode("utf-8")
            print(f"Server: {response}")

            if "Access granted" in response:
                self.authenticated = True
                print("Authentication successful.")
                return True
            else:
                self.authenticated = False
                print("Authentication failed.")
                return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    async def disconnect(self):
        """Closes the database connection."""
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
                print("Database connection closed.")
            except Exception as e:
                print(f"Error closing connection: {e}")
            finally:
                self.reader = None
                self.writer = None
                self.connected = False
                self.authenticated = False

    def _is_connected(self):
        """Returns True if connected and authenticated to the database."""
        return self.connected and self.authenticated and self.writer is not None
    
    def generate_uuid(self):
        """Generates a UUID for the database."""
        return str(uuid.uuid4())
    
    async def receive_response(self):
        """Receives and parses JSON response from server."""
        if not self.reader:
            return None
        
        try:
            response_data = await self.reader.read(4096)
            response_str = response_data.decode("utf-8").strip()
            
            if response_str:
                return json.loads(response_str)
            return None
        except json.JSONDecodeError as e:
            print(f"ERROR: Failed to parse JSON response: {e}")
            return None
        except Exception as e:
            print(f"ERROR: Failed to receive response: {e}")
            return None
    
    async def send_json(self, data):
        """Sends a Python dictionary as a JSON string to the server."""
        if not self.connected or not self.writer:
            print("ERROR: Not connected to server.")
            return None

        try:
            json_data = json.dumps(data)
            self.writer.write(json_data.encode("utf-8"))
            await self.writer.drain()

            response = await self.receive_response()

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
                print("WARNING: No valid response received from server.")

            return response
        except Exception as e:
            print(f"ERROR: Unexpected error sending data: {e}")
            await self.disconnect()
            return None

    async def generate_robot_struct(self, color, temperature, humidity, timestamp, energy_consume, energy_cost):
        """Generates a structure for the database and sends it."""
        if not self._is_connected():
            print("ERROR: Not connected to database. Please connect first.")
            return None
        
        struct = {
            "type": "robotdata",
            "data": [
                {
                    "uuid": self.generate_uuid(),
                    "color": color,  # blue, red, green, yellow
                    "sensor_data": {
                        "temperature": temperature,  # float
                        "humidity": humidity
                    },
                    "timestamp": timestamp,  # 2025-03-10 15:30:00 format
                    "energy_consume": energy_consume,  # float
                    "energy_cost": energy_cost,  # float
                }
            ]
        }
        
        return await self.send_json(struct)
    
    async def generate_energydata_struct(self, energy_data_list):
        """Generates a structure for the database and sends it.
        
        Args:
            energy_data_list: List of dictionaries with 'timestamp' and 'energy_cost' keys
                             [{"timestamp": "2025-03-10 15:30:00", "energy_cost": 42.09}, ...]
        """
        if not self._is_connected():
            print("ERROR: Not connected to database. Please connect first.")
            return None
        
       
        if not isinstance(energy_data_list, list):
            print("ERROR: energy_data_list must be a list of dictionaries.")
            return None
        
        struct = {
            "type": "energydata",
            "data": energy_data_list
        }
        
        return await self.send_json(struct)

# Beispiel für die Verwendung:
async def main():
    db = Database_Imp()
    
    # Verbindung herstellen
    if await db.connect():
      
        response = await db.generate_robot_struct(
            color="blue",
            temperature=23.5,
            humidity=65.2,
            timestamp="2025-06-10 15:30:00",
            energy_consume=12.5,
            energy_cost=0.15
        )
        
        print(f"Response: {response}")
        
     
        # await db.disconnect()  # Nur aufrufen wenn fertig

if __name__ == "__main__":
    asyncio.run(main())