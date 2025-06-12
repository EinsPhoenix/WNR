import socket
import struct
import numpy as np
import cv2
import threading
import time
import json
import base64
from typing import Tuple, Optional
from collections import deque


class StreamHandler:
    """Handles receiving video frames from a network stream by acting as a server."""

    def __init__(self,
        host: str,
        port: int,
        # forward_host: str = "192.168.1.103",
        forward_host: str = "localhost",
        forward_port: int = 12345):
        """
        Initialize the stream handler server.

        Args:
            host: Host address to bind the server to
            port: Port number to listen on
            forward_host: Host to forward video data to
            forward_port: Port to forward video data to
        """
        self.host = host
        self.port = port
        self.forward_host = forward_host
        self.forward_port = forward_port
        self.server_socket = None
        self.client_socket = None
        self.client_address = None
        self.is_running = False
        self.is_connected = False
        self.is_receiving = False
        self.current_frame = None
        self.frame_available = False
        self.frame_width = 0
        self.frame_height = 0
        self.accept_thread = None
        self.receive_thread = None

        self.forward_socket = None
        self.forward_thread = None
        self.is_forwarding = False
        self.frame_buffer = deque(maxlen=5)
        self.frame_lock = threading.Lock()

        self.brightness_factor = 0
        self.saturation_factor = 0
        self.sharpness_factor = 0
        self._next_send_allowed_time = 0.0

    def open(self) -> bool:
        """
        Start the stream server and listen for connections.

        Returns:
            bool: True if server was started successfully, False otherwise
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)

            self.is_running = True
            self.accept_thread = threading.Thread(target=self._accept_connections)
            self.accept_thread.daemon = True
            self.accept_thread.start()

            self._start_forwarding()

            time.sleep(0.5)
            return True

        except Exception as e:
            if self.server_socket:
                self.server_socket.close()
                self.server_socket = None
            return False

    def _start_forwarding(self):
        """Start the forwarding thread."""
        self.is_forwarding = True
        self.forward_thread = threading.Thread(target=self._forward_frames)
        self.forward_thread.daemon = True
        self.forward_thread.start()

    def _connect_to_forward_server(self):
        """Connect to the forwarding server."""
        try:
            if self.forward_socket:
                try:
                    self.forward_socket.close()
                except:
                    pass
            self.forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.forward_socket.connect((self.forward_host, self.forward_port))
            try:
                password = "1234"
                self.forward_socket.sendall(password.encode("utf-8"))
                response = self.forward_socket.recv(1024).decode("utf-8")
                if "Access granted" in response:
                    return True
                else:
                    self.forward_socket.close()
                    self.forward_socket = None
                    return False
            except socket.error as e:
                if self.forward_socket:
                    self.forward_socket.close()
                self.forward_socket = None
                return False
            except Exception as e:
                if self.forward_socket:
                    self.forward_socket.close()
                self.forward_socket = None
                return False
        except Exception as e:
            self.forward_socket = None
            return False

    def _forward_frames(self):
        """Forward frames to the specified server."""
        while self.is_forwarding:
            try:
                current_time = time.time()
                if current_time < self._next_send_allowed_time:
                    sleep_duration = self._next_send_allowed_time - current_time
                    time.sleep(min(max(0, sleep_duration), 1.0))
                    continue
                if len(self.frame_buffer) > 0:
                    if not self.forward_socket:
                        if not self._connect_to_forward_server():
                            self._next_send_allowed_time = time.time() + 1.0
                            continue
                    frame = None
                    with self.frame_lock:
                        if len(self.frame_buffer) > 0:
                            frame = self.frame_buffer.popleft()
                    if frame is not None:
                        try:
                            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                            frame_base64 = base64.b64encode(buffer).decode('utf-8')

                            message = {
                                "type": "videostream",
                                "data": [frame_base64]
                            }

                            json_str = json.dumps(message)
                            message_payload_bytes = json_str.encode('utf-8') + b'\n'
                            if len(message_payload_bytes) > 500000:
                                continue
                            self.forward_socket.sendall(message_payload_bytes)
                            self._next_send_allowed_time = time.time() + 0.02
                            try:
                                self.forward_socket.settimeout(0.5)
                                response_buffer = b''
                                while not response_buffer.endswith(b'\n'):
                                    chunk = self.forward_socket.recv(1024)
                                    if not chunk:
                                        if self.forward_socket:
                                            self.forward_socket.close()
                                        self.forward_socket = None
                                        break
                                    response_buffer += chunk
                                if self.forward_socket:
                                    response_str = response_buffer.decode('utf-8').strip()
                                    if response_str:
                                        try:
                                            response_data = json.loads(response_str)
                                            if isinstance(response_data, dict) and \
                                               response_data.get("message") == "Video stream ignored, no WebRTC clients connected" and \
                                               response_data.get("status") == "success":
                                                self._next_send_allowed_time = time.time() + 5.0
                                        except json.JSONDecodeError:
                                            pass
                            except socket.timeout:
                                pass
                            except socket.error as e_recv:
                                if self.forward_socket:
                                    self.forward_socket.close()
                                self.forward_socket = None
                            finally:
                                if self.forward_socket:
                                    self.forward_socket.settimeout(None)
                        except socket.error as e_send:
                            if self.forward_socket:
                                self.forward_socket.close()
                            self.forward_socket = None
                            self._next_send_allowed_time = time.time() + 1.0
                        except Exception as e_send_generic:
                            if self.forward_socket:
                                try:
                                    self.forward_socket.close()
                                except:
                                    pass
                            self.forward_socket = None
                            self._next_send_allowed_time = time.time() + 1.0
                else:
                    time.sleep(0.1)
            except Exception as e_outer:
                if self.forward_socket:
                    try:
                        self.forward_socket.close()
                    except:
                        pass
                    self.forward_socket = None
                self._next_send_allowed_time = time.time() + 1.0

    def _accept_connections(self):
        """
        Accept client connections in a separate thread.
        """
        while self.is_running:
            try:
                self.server_socket.settimeout(1.0)
                try:
                    client_socket, client_address = self.server_socket.accept()
                    if self.client_socket:
                        try:
                            self.client_socket.close()
                        except:
                            pass
                    self.client_socket = client_socket
                    self.client_address = client_address
                    self.is_connected = True
                    if self.receive_thread and self.receive_thread.is_alive():
                        self.is_receiving = False
                        self.receive_thread.join(timeout=1.0)
                    self.is_receiving = True
                    self.receive_thread = threading.Thread(target=self._receive_frames)
                    self.receive_thread.daemon = True
                    self.receive_thread.start()
                except socket.timeout:
                    continue
            except Exception as e:
                time.sleep(1.0)

    def _receive_frames(self):
        """
        Continuously receive frames from the connected client in a separate thread.
        """
        data = b""
        payload_size = struct.calcsize("L")
        try:
            while self.is_receiving and self.is_connected:
                try:
                    while len(data) < payload_size:
                        packet = self.client_socket.recv(4096)
                        if not packet:
                            self.is_connected = False
                            break
                        data += packet
                    if not self.is_connected:
                        break
                    packed_msg_size = data[:payload_size]
                    data = data[payload_size:]
                    msg_size = struct.unpack("L", packed_msg_size)[0]
                    while len(data) < msg_size:
                        data += self.client_socket.recv(4096)
                    frame_data = data[:msg_size]
                    data = data[msg_size:]
                    img_array = np.frombuffer(frame_data, dtype=np.uint8)
                    frame = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    if frame is not None:
                        self.current_frame = frame
                        self.frame_available = True
                        with self.frame_lock:
                            self.frame_buffer.append(frame.copy())
                        if self.frame_height == 0 or self.frame_width == 0:
                            self.frame_height, self.frame_width = frame.shape[:2]
                except ConnectionError:
                    self.is_connected = False
                    break
        except Exception as e:
            pass
        finally:
            self.is_receiving = False
            self.frame_available = False
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
                self.client_address = None
                self.is_connected = False

    def _adjust_frame(self, frame):
        """
        Apply brightness, saturation, and sharpness adjustments to the frame.

        Args:
            frame: The frame to adjust

        Returns:
            The adjusted frame
        """
        if frame is None:
            return None
        frame_float = frame.astype(np.float32) / 255.0
        if self.brightness_factor != 0:
            brightness_value = self.brightness_factor / 100.0
            frame_float = frame_float + brightness_value
            frame_float = np.clip(frame_float, 0, 1)
        if self.saturation_factor != 0:
            frame_hsv = cv2.cvtColor(frame_float, cv2.COLOR_BGR2HSV)
            saturation_value = 1.0 + (self.saturation_factor / 100.0)
            frame_hsv[:, :, 1] = frame_hsv[:, :, 1] * saturation_value
            frame_hsv[:, :, 1] = np.clip(frame_hsv[:, :, 1], 0, 1)
            frame_float = cv2.cvtColor(frame_hsv, cv2.COLOR_HSV2BGR)
        adjusted_frame = (frame_float * 255).astype(np.uint8)
        if self.sharpness_factor != 0:
            blur = cv2.GaussianBlur(adjusted_frame, (0, 0), 3)
            sharpness_strength = self.sharpness_factor / 100.0
            adjusted_frame = cv2.addWeighted(
                adjusted_frame, 1.0 + sharpness_strength, blur, -sharpness_strength, 0
            )
        return adjusted_frame

    def get_frame(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Get the latest frame from the stream with adjustments applied.

        If no frame is available yet, returns (False, None).

        Returns:
            tuple: (success, frame) where success is a boolean indicating if a frame is available,
                  and frame is the adjusted video frame (if success is True)
        """
        if not self.frame_available or self.current_frame is None:
            return False, None
        adjusted_frame = self._adjust_frame(self.current_frame.copy())
        return True, adjusted_frame

    def get_frame_dimensions(self) -> Tuple[int, int]:
        """
        Get the stream frame dimensions.

        Returns:
            tuple: (width, height) of the video frame
        """
        return self.frame_width, self.frame_height

    def get_brightness(self) -> float:
        """Get the brightness adjustment value."""
        return self.brightness_factor

    def get_saturation(self) -> float:
        """Get the saturation adjustment value."""
        return self.saturation_factor

    def get_sharpness(self) -> float:
        """Get the sharpness adjustment value."""
        return self.sharpness_factor

    def set_brightness(self, value: float) -> None:
        """Set the brightness adjustment value"""
        self.brightness_factor = max(-100, min(100, value))

    def set_saturation(self, value: float) -> None:
        """Set the saturation adjustment value"""
        self.saturation_factor = max(-100, min(100, value))

    def set_sharpness(self, value: float) -> None:
        """Set the sharpness adjustment value"""
        self.sharpness_factor = max(-100, min(100, value))

    def increase_brightness(self) -> float:
        """Increase brightness adjustment and return new value."""
        self.brightness_factor = min(self.brightness_factor + 5, 100)
        return self.brightness_factor

    def decrease_brightness(self) -> float:
        """Decrease brightness adjustment and return new value."""
        self.brightness_factor = max(self.brightness_factor - 5, -100)
        return self.brightness_factor

    def increase_saturation(self) -> float:
        """Increase saturation adjustment and return new value."""
        self.saturation_factor = min(self.saturation_factor + 5, 500)
        return self.saturation_factor

    def decrease_saturation(self) -> float:
        """Decrease saturation adjustment and return new value."""
        self.saturation_factor = max(self.saturation_factor - 5, -500)
        return self.saturation_factor

    def increase_sharpness(self) -> float:
        """Increase sharpness adjustment and return new value."""
        self.sharpness_factor = min(self.sharpness_factor + 5, 500)
        return self.sharpness_factor

    def decrease_sharpness(self) -> float:
        """Decrease sharpness adjustment and return new value."""
        self.sharpness_factor = max(self.sharpness_factor - 5, -500)
        return self.sharpness_factor

    def close(self) -> None:
        """Stop the server and clean up resources."""
        self.is_running = False
        self.is_receiving = False
        self.is_forwarding = False
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            self.client_socket = None
        if self.forward_socket:
            try:
                self.forward_socket.close()
            except:
                pass
            self.forward_socket = None
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            self.server_socket = None
        if self.accept_thread and self.accept_thread.is_alive():
            self.accept_thread.join(timeout=1.0)
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=1.0)
        if self.forward_thread and self.forward_thread.is_alive():
            self.forward_thread.join(timeout=1.0)
        self.is_connected = False

    def wait_for_first_frame(self, timeout=None):
        """
        Wait until the first frame is received from a client.

        Args:
            timeout (float, optional): Maximum time to wait in seconds. None for indefinite wait.

        Returns:
            bool: True if frame was received, False if timeout occurred
        """
        start_time = time.time()
        while True:
            if self.current_frame is not None:
                return True
            if timeout is not None and time.time() - start_time > timeout:
                return False
            time.sleep(0.1)
