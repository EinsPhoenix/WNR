import asyncio
from asyncua import Client as AsyncuaClient, Node
import json
import stream.shared_state as shared_state
import os


class AsyncOPCUAClient:
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client = AsyncuaClient(url=self.server_url)
        self.node_ids = {}
        self.temperature_node: Node = None
        self.humidity_node: Node = None
        self.fan_speed_node: Node = None
        self.set_fan_speed_node: Node = None
        self.running = True
        self._fetch_task: asyncio.Task = None
        self.client_cert_path = os.path.join(os.path.dirname(__file__), "certs", "server_cert.pem")
        self.client_key_path = os.path.join(os.path.dirname(__file__), "certs", "server_key.pem")
        self.server_cert_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "RaspCamStream", "certs", "server_cert.pem"))

    async def connect(self):
        """Verbindet sich mit dem Server und initialisiert die Nodes."""
        if not os.path.exists(self.client_cert_path):
            raise RuntimeError(f"Client certificate not found: {self.client_cert_path}")
        if not os.path.exists(self.client_key_path):
            raise RuntimeError(f"Client key not found: {self.client_key_path}")
        if not os.path.exists(self.server_cert_path):
            raise RuntimeError(f"Server certificate not found: {self.server_cert_path}")
        try:
            await self.client.set_security_string(
                f"Basic256Sha256,SignAndEncrypt,{self.client_cert_path},{self.client_key_path},{self.server_cert_path}"
            )
        except Exception as e:
            raise RuntimeError(f"Error setting OPC UA Security Policy: {e}")
        await self.client.connect()
        node_ids_ua_node = await self._find_node_by_displayname("NodeIDs", path=["Objects", "Device"])
        if node_ids_ua_node:
            node_ids_json = await node_ids_ua_node.read_value()
            self.node_ids = json.loads(node_ids_json)
            self.temperature_node = self.client.get_node(self.node_ids["Temperature"])
            self.humidity_node = self.client.get_node(self.node_ids["Humidity"])
            self.fan_speed_node = self.client.get_node(self.node_ids["FanSpeed"])
            self.set_fan_speed_node = self.client.get_node(self.node_ids["SetFanSpeed"])
        else:
            await self.client.disconnect()
            raise RuntimeError("Node initialization failed, 'NodeIDs' not found.")

    async def _find_node_by_displayname(self, display_name_to_find: str, parent_node_ua: Node = None, path: list[str] = None) -> Node:
        """
        Sucht einen Node anhand seines Anzeigenamens, optional innerhalb eines Pfades.
        """
        if parent_node_ua is None:
            parent_node_ua = self.client.get_root_node()
        current_node_ua = parent_node_ua
        if path:
            for node_name_in_path_str in path:
                found_in_path = False
                children_ua = await current_node_ua.get_children()
                for child_ua in children_ua:
                    child_display_name = await child_ua.read_display_name()
                    if child_display_name.Text == node_name_in_path_str:
                        current_node_ua = child_ua
                        found_in_path = True
                        break
                if not found_in_path:
                    return None
            children_of_final_path_node = await current_node_ua.get_children()
            for child_ua in children_of_final_path_node:
                child_display_name = await child_ua.read_display_name()
                if child_display_name.Text == display_name_to_find:
                    return child_ua
            return None
        else:

            async def recursive_search(node_ua_param: Node) -> Node:
                display_name_obj = await node_ua_param.read_display_name()
                if display_name_obj.Text == display_name_to_find:
                    return node_ua_param
                children_ua_list = await node_ua_param.get_children()
                for child_ua_rec in children_ua_list:
                    result = await recursive_search(child_ua_rec)
                    if result:
                        return result
                return None
            return await recursive_search(parent_node_ua)

    async def reconnect(self):
        """Versucht, die Verbindung zum OPC UA Server wiederherzustellen."""
        try:
            if self.client and self.client.uaclient and self.client.uaclient.protocol:
                try:
                    await self.client.disconnect()
                except Exception:
                    pass
            self.client = AsyncuaClient(url=self.server_url)
            await self.client.set_security_string(
                f"Basic256Sha256,SignAndEncrypt,{self.client_cert_path},{self.client_key_path},{self.server_cert_path}"
            )
            await self.client.connect()
            node_ids_ua_node = await self._find_node_by_displayname("NodeIDs", path=["Objects", "Device"])
            if node_ids_ua_node:
                node_ids_json = await node_ids_ua_node.read_value()
                self.node_ids = json.loads(node_ids_json)
                self.temperature_node = self.client.get_node(self.node_ids["Temperature"])
                self.humidity_node = self.client.get_node(self.node_ids["Humidity"])
                self.fan_speed_node = self.client.get_node(self.node_ids["FanSpeed"])
                self.set_fan_speed_node = self.client.get_node(self.node_ids["SetFanSpeed"])
                return True
            else:
                return False
        except Exception as e:
            return False

    async def fetch_data_periodically(self):
        """Ruft periodisch Daten vom Server ab und speichert sie in shared_state."""
        reconnect_delay = shared_state.OPC_FETCH_INTERVAL
        max_reconnect_delay = shared_state.OPC_RECONNECT_TIMEOUT
        while self.running:
            try:
                if not (self.temperature_node and self.humidity_node and self.fan_speed_node):
                    await asyncio.sleep(shared_state.OPC_FETCH_INTERVAL)
                    continue
                temp_val = await self.temperature_node.read_value()
                hum_val = await self.humidity_node.read_value()
                fan_val = await self.fan_speed_node.read_value()
                shared_state.temperature = float(temp_val)
                shared_state.humidity = float(hum_val)
                shared_state.fan_speed = float(fan_val)
                reconnect_delay = shared_state.OPC_FETCH_INTERVAL
            except Exception as e:
                if "Connection is closed" in str(e):
                    await asyncio.sleep(reconnect_delay)
                    if await self.reconnect():
                        reconnect_delay = shared_state.OPC_FETCH_INTERVAL
                    else:
                        reconnect_delay = min(reconnect_delay * 1.5, max_reconnect_delay)
            if not self.running:
                break
            await asyncio.sleep(shared_state.OPC_FETCH_INTERVAL)

    async def set_fan_speed(self, value: float):
        """Setzt die Lüftergeschwindigkeit auf dem Server."""
        if not self.set_fan_speed_node:
            return
        try:
            await self.set_fan_speed_node.write_value(float(value))
        except Exception as e:
            pass

    def start_fetching_data(self):
        """Startet den Task für den periodischen Datenabruf."""
        if self._fetch_task and not self._fetch_task.done():
            return
        try:
            loop = asyncio.get_event_loop()
            self._fetch_task = loop.create_task(self.fetch_data_periodically())
        except RuntimeError as e:
            pass

    async def stop(self):
        """Stoppt den Datenabruf und trennt die Verbindung zum Server."""
        self.running = False
        if self._fetch_task:
            self._fetch_task.cancel()
            try:
                await self._fetch_task
            except asyncio.CancelledError:
                pass
        if self.client and self.client.uaclient and self.client.uaclient.protocol:
            try:
                await self.client.disconnect()
            except Exception as e:
                pass