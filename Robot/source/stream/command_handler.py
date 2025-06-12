import socket
import json
import threading
import time
import math
from typing import Dict, List, Any, Tuple
import stream.shared_state as shared_state
from stream.marker_detector import MarkerDetector
from stream.video_analyzer import VideoAnalyzer


class CommandHandler:
    """Handles TCP connections and processes commands."""

    def __init__(
        self,
        host: str,
        port: int,
        marker_detector: MarkerDetector,
        video_analyzer: VideoAnalyzer,
    ):
        """
        Initialize the command handler.

        Args:
            host: TCP host address
            port: TCP port number
            marker_detector: Instance of MarkerDetector
            video_analyzer: Instance of VideoAnalyzer
        """
        self.host = host
        self.port = port
        self.marker_detector = marker_detector
        self.video_analyzer = video_analyzer
        self.server_running = False
        self.server_thread = None

    def start_server(self) -> bool:
        """
        Start the TCP server in a separate thread.

        Returns:
            bool: True if server started, False otherwise
        """
        if self.server_running:
            return False

        self.server_running = True
        self.server_thread = threading.Thread(
            target=self._tcp_server_logic, daemon=True
        )
        self.server_thread.start()
        return True

    def _tcp_server_logic(self) -> None:
        """
        Listens for TCP connections and processes calibration commands.
        Runs in a separate thread.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((self.host, self.port))
            except socket.error as e:
                self.server_running = False
                return
            s.listen()
            while self.server_running:
                try:
                    conn, addr = s.accept()
                    with conn:
                        data = conn.recv(1024)
                        if not data:
                            continue
                        response_to_send = None
                        message_str = data.decode("utf-8")
                        try:
                            message = json.loads(message_str)
                            msg_type = message.get("type")
                            if msg_type == "calibrate":
                                response_to_send = self._handle_calibrate_command(
                                    message, addr
                                )
                            elif msg_type == "color":
                                color_data_payload = self._handle_color_request()
                                response_to_send = json.dumps(
                                    color_data_payload
                                ).encode("utf-8")
                            elif msg_type == "sensor":
                                response_payload = self._handle_sensor_request()
                                response_to_send = json.dumps(
                                    response_payload
                                ).encode("utf-8")
                            else:
                                response_message = "Invalid message type. Expected 'calibrate' or 'color'."
                                error_payload = {
                                    "status": "error",
                                    "message": response_message,
                                }
                                response_to_send = json.dumps(error_payload).encode(
                                    "utf-8"
                                )
                        except json.JSONDecodeError:
                            error_payload = {
                                "status": "error",
                                "message": "Invalid JSON format.",
                            }
                            response_to_send = json.dumps(error_payload).encode("utf-8")
                        except Exception as e:
                            error_payload = {
                                "status": "error",
                                "message": f"Server error: {e}",
                            }
                            response_to_send = json.dumps(error_payload).encode("utf-8")
                        if response_to_send:
                            conn.sendall(response_to_send)
                        else:
                            fallback_error = {
                                "status": "error",
                                "message": "Internal server error processing request.",
                            }
                            conn.sendall(json.dumps(fallback_error).encode("utf-8"))
                except socket.error as e:
                    if self.server_running:
                        time.sleep(1)
                except Exception as e:
                    break
            self.server_running = False

    def _handle_calibrate_command(
        self, message: Dict[str, Any], addr: Tuple[str, int]
    ) -> bytes:
        """
        Handles the 'calibrate' command type.

        Args:
            message: The parsed JSON message
            addr: Client address tuple

        Returns:
            bytes: Response to send to client
        """
        payload = message.get("payload")
        response_status = "error"
        response_message = "Invalid payload for calibrate."
        processed_id = None
        if isinstance(payload, dict):
            if payload.get("finish") is True:
                success, msg = self._handle_finish_calibration_command()
                response_status = "success" if success else "error"
                response_message = msg
            elif "number" in payload and "robot_pos" in payload:
                try:
                    calibration_profile_id_from_tcp = int(payload["number"])
                    robot_pos_payload = payload["robot_pos"]
                    if not (
                        isinstance(robot_pos_payload, dict)
                        and "x" in robot_pos_payload
                        and isinstance(robot_pos_payload["x"], (int, float))
                        and "y" in robot_pos_payload
                        and isinstance(robot_pos_payload["y"], (int, float))
                    ):
                        response_message = 'Invalid \'robot_pos\' format in payload. Expected {"x": number, "y": number}.'
                    elif (
                        0
                        <= calibration_profile_id_from_tcp
                        <= shared_state.MAX_CALIBRATION_PROFILE_ID
                    ):
                        success, msg = self._handle_tcp_command(
                            calibration_profile_id_from_tcp, robot_pos_payload
                        )
                        response_status = "success" if success else "error"
                        response_message = msg
                        processed_id = calibration_profile_id_from_tcp
                    else:
                        response_message = f"Invalid calibration profile ID {calibration_profile_id_from_tcp}. Must be 0-{shared_state.MAX_CALIBRATION_PROFILE_ID}."
                except ValueError:
                    response_message = (
                        "Invalid 'number' in payload, must be an integer."
                    )
                except TypeError:
                    response_message = (
                        "Invalid type for 'number' or 'robot_pos' in payload."
                    )
            else:
                response_message = "Payload for 'calibrate' must contain 'number' and 'robot_pos', or 'finish: true'."
        else:
            response_message = "Payload for 'calibrate' must be a dictionary."
        response_payload_dict = {"status": response_status, "message": response_message}
        if processed_id is not None:
            response_payload_dict["id"] = processed_id
        response_to_send = json.dumps(response_payload_dict).encode("utf-8")
        return response_to_send

    def _handle_tcp_command(
        self, calibration_profile_id: int, robot_pos_from_payload: Dict[str, float]
    ) -> Tuple[bool, str]:
        """
        Handles a calibration command. Updates the calibration data for the
        specified calibration_profile_id using the currently detected center of PHYSICAL_MARKER_ID_TO_TRACK
        and the provided robot_pos.

        Args:
            calibration_profile_id: The calibration profile ID to update
            robot_pos_from_payload: The robot position from the client

        Returns:
            tuple: (success, message)
        """
        with shared_state.data_lock:
            if (
                shared_state.PHYSICAL_MARKER_ID_TO_TRACK
                in shared_state.current_detected_marker_centers
            ):
                center_x, center_y = shared_state.current_detected_marker_centers[
                    shared_state.PHYSICAL_MARKER_ID_TO_TRACK
                ]
                shared_state.calibrated_marker_origins = (
                    self.marker_detector.update_marker_origin(
                        calibration_profile_id,
                        center_x,
                        center_y,
                        robot_pos_from_payload,
                        shared_state.calibrated_marker_origins,
                    )
                )
                self.marker_detector.save_calibration_data(
                    shared_state.CALIBRATION_FILE_PATH,
                    shared_state.calibrated_marker_origins,
                )
                msg = f"Calibration profile ID {calibration_profile_id} updated using Marker {shared_state.PHYSICAL_MARKER_ID_TO_TRACK}'s position ({center_x}, {center_y}) and robot_pos {robot_pos_from_payload}."
                return True, msg
            else:
                msg = f"Calibration command for profile ID {calibration_profile_id} received, but Marker {shared_state.PHYSICAL_MARKER_ID_TO_TRACK} is not currently visible."
                return False, msg

    def _handle_finish_calibration_command(self) -> Tuple[bool, str]:
        """
        Handles the 'finish calibration' command: calculates and stores the transformation.

        Returns:
            tuple: (success, message)
        """
        current_calibration_data_copy = []
        with shared_state.data_lock:
            if not shared_state.calibrated_marker_origins or not isinstance(
                shared_state.calibrated_marker_origins, list
            ):
                msg = "No valid calibration data available to calculate transformation."
                return False, msg
            current_calibration_data_copy = [
                dict(item) for item in shared_state.calibrated_marker_origins
            ]
        if not current_calibration_data_copy:
            msg = "No calibration data available (after copy) to calculate transformation."
            return False, msg
        success, msg, _ = self.video_analyzer.calculate_and_store_transformation(
            current_calibration_data_copy
        )
        return success, msg

    def _handle_color_request(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Prepares data for detected color objects for TCP response.

        Returns:
            dict: Color objects data for TCP response
        """
        response_objects = []
        with shared_state.data_lock:
            objects_to_process = list(shared_state.current_detected_color_objects_info)
        for obj_info in objects_to_process:
            bgr_tuple = obj_info.get("bgr_tuple")
            robot_pos = obj_info.get("robot_pos")
            if (
                bgr_tuple
                and isinstance(bgr_tuple, tuple)
                and len(bgr_tuple) == 3
                and robot_pos
                and isinstance(robot_pos, dict)
                and "x" in robot_pos
                and "y" in robot_pos
                and robot_pos["x"] is not None
                and math.isfinite(robot_pos["x"])
                and robot_pos["y"] is not None
                and math.isfinite(robot_pos["y"])
            ):
                bgr_string = f"{bgr_tuple[0]},{bgr_tuple[1]},{bgr_tuple[2]}"
                response_objects.append(
                    {
                        "bgr": bgr_string,
                        "robot_pos": {
                            "x": float(robot_pos["x"]),
                            "y": float(robot_pos["y"]),
                        },
                    }
                )
        return {"objects": response_objects}

    def _handle_sensor_request(self) -> Dict[str, Any]:
        return {
            "temperature": shared_state.temperature,
            "humidity": shared_state.humidity,
            "fan_speed": shared_state.fan_speed,
        }

    def stop_server(self) -> None:
        """Stop the TCP server."""
        self.server_running = False
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.0)
