import json
import asyncio
import uuid

from utils.config import read_config

class DatabaseImp:
    def __init__(self, main_window, password="1234"):
        self.main_window = main_window
        self.password = password
        self.reader = None
        self.writer = None
        self.connected = False
        self.authenticated = False

    async def connect(self):
        """Establishes an async TCP connection to the database server."""
        config = read_config(self.main_window)
        db_ip = config["db"]["host"]
        db_port = config["db"]["port"]
        try:
            self.reader, self.writer = await asyncio.open_connection(db_ip, db_port)
            self.connected = True
            if await self._authenticate():
                return True
            else:
                await self.disconnect()
                return False
        except Exception as e:
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
            self.writer.write(self.password.encode("utf-8"))
            await self.writer.drain()
            response_data = await self.reader.read(1024)
            response = response_data.decode("utf-8")
            if "Access granted" in response:
                self.authenticated = True
                return True
            else:
                self.authenticated = False
                return False
        except Exception as e:
            return False

    async def disconnect(self):
        """Closes the database connection."""
        if self.writer:
            try:
                self.writer.close()
                await self.writer.wait_closed()
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
            return None
        except Exception as e:
            return None

    async def send_json(self, data):
        """Sends a Python dictionary as a JSON string to the server."""
        if not self.connected or not self.writer:
            return None
        try:
            json_data = json.dumps(data)
            self.writer.write(json_data.encode("utf-8"))
            await self.writer.drain()
            response = await self.receive_response()
            return response
        except Exception as e:
            return None

    async def generate_robot_struct(self, color, temperature, humidity, timestamp, energy_consume, energy_cost):
        """Generates a structure for the database and sends it."""
        if not self._is_connected():
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
            return None
        if not isinstance(energy_data_list, list):
            return None
        struct = {
            "type": "energydata",
            "data": energy_data_list
        }
        return await self.send_json(struct)