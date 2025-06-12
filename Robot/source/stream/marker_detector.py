import cv2
import cv2.aruco as aruco
import numpy as np
import json
from typing import Dict, List, Tuple, Any
import stream.shared_state as shared_state


class MarkerDetector:
    """Handles ArUco marker detection and calibration."""
    def __init__(self):
        """Initialize the marker detector."""
        self.aruco_dict, self.aruco_params, self.detector = (
            self.initialize_aruco_detector()
        )

    def initialize_aruco_detector(self) -> Tuple[Any, Any, Any]:
        """
        Initializes the ArUco detector.

        Returns:
            tuple: (aruco_dict, aruco_params, detector_object) or (aruco_dict, aruco_params, None) for legacy.
        """
        try:
            aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_4X4_50)
            aruco_params = aruco.DetectorParameters()
            # Anpassungen für kleinere Marker:
            aruco_params.adaptiveThreshWinSizeMin = 3  # Experimentieren Sie mit Werten zwischen 3-7
            aruco_params.adaptiveThreshWinSizeMax = 23 # Experimentieren Sie mit Werten um 15-25
            aruco_params.minMarkerPerimeterRate = 0.01 # Verringern, wenn Marker sehr klein sind (Standard 0.03)
            detector = aruco.ArucoDetector(aruco_dict, aruco_params)
            return aruco_dict, aruco_params, detector
        except AttributeError:
            aruco_dict = aruco.Dictionary_get(aruco.DICT_4X4_50)
            aruco_params = aruco.DetectorParameters_create()
            aruco_params.adaptiveThreshWinSizeMin = 3
            aruco_params.adaptiveThreshWinSizeMax = 23
            aruco_params.minMarkerPerimeterRate = 0.01
            detector = None
            return aruco_dict, aruco_params, detector

    def process_frame(
        self, frame: np.ndarray
    ) -> Tuple[np.ndarray, Dict[int, Tuple[int, int]]]:
        """
        Detects ArUco markers in a frame, draws them, and calculates their centers.
        Only processes PHYSICAL_MARKER_ID_TO_TRACK.

        Args:
            frame: The input video frame.

        Returns:
            tuple: (display_frame, detected_centers_map)
                   display_frame: Frame with markers and centers drawn.
                   detected_centers_map: Maps detected marker IDs to their (x, y) center coordinates.
        """
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        display_frame = frame.copy()
        detected_centers_map = {}
        if self.detector:
            corners, ids, _ = self.detector.detectMarkers(gray_frame)
        else:
            corners, ids, _ = aruco.detectMarkers(
                gray_frame, self.aruco_dict, parameters=self.aruco_params
            )
        if ids is not None:
            aruco.drawDetectedMarkers(display_frame, corners, ids)
            for i, marker_id_array in enumerate(ids):
                marker_id = int(marker_id_array[0])
                if marker_id == shared_state.PHYSICAL_MARKER_ID_TO_TRACK:
                    marker_corners = corners[i].reshape((4, 2))
                    center_x = int(np.mean(marker_corners[:, 0]))
                    center_y = int(np.mean(marker_corners[:, 1]))
                    detected_centers_map[marker_id] = (center_x, center_y)
                    cv2.circle(display_frame, (center_x, center_y), 5, (0, 255, 0), -1)
                    cv2.putText(
                        display_frame,
                        f"ID {marker_id}",
                        (center_x + 10, center_y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        1,
                    )
        return display_frame, detected_centers_map

    def draw_calibrated_origins(
        self, display_frame: np.ndarray, calibration_data: List[Dict[str, Any]]
    ) -> np.ndarray:
        """
        Draws the calibrated origin points on the frame.

        Args:
            display_frame: The frame to draw on.
            calibration_data: List of calibrated marker data.

        Returns:
            np.ndarray: The frame with calibrated origins drawn
        """
        for marker_info in calibration_data:
            marker_id = marker_info.get("id")
            origin = marker_info.get("origin_point")
            if origin and isinstance(origin, dict) and "x" in origin and "y" in origin:
                ox, oy = int(origin["x"]), int(origin["y"])
                cv2.drawMarker(
                    display_frame, (ox, oy), (255, 0, 255), cv2.MARKER_CROSS, 15, 2
                )
                cv2.putText(
                    display_frame,
                    f"Calib ID {marker_id}",
                    (ox + 10, oy + 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 0, 255),
                    2,
                )
        return display_frame

    def load_calibration_data(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Loads marker origin calibration data from a JSON file.

        Args:
            filepath: The path to the JSON file.

        Returns:
            list: A list of dictionaries containing marker calibration data,
                  or an empty list if the file doesn't exist or is invalid.
        """
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    processed_data = []
                    for item in data:
                        if (
                            isinstance(item, dict)
                            and "id" in item
                            and "origin_point" in item
                        ):
                            if (
                                "robot_pos" not in item
                                or not isinstance(item["robot_pos"], dict)
                                or "x" not in item["robot_pos"]
                                or "y" not in item["robot_pos"]
                            ):
                                item["robot_pos"] = {"x": 0.0, "y": 0.0}
                            processed_data.append(item)
                    return processed_data
                else:
                    return []
        except FileNotFoundError:
            return []
        except json.JSONDecodeError:
            return []

    def save_calibration_data(self, filepath: str, data: List[Dict[str, Any]]) -> bool:
        """
        Saves marker origin calibration data to a JSON file.

        Args:
            filepath: The path to the JSON file.
            data: A list of dictionaries containing marker calibration data.

        Returns:
            bool: True if saving was successful, False otherwise.
        """
        try:
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)
            return True
        except IOError as e:
            return False

    def update_marker_origin(
        self,
        marker_id_to_update: int,
        center_x: int,
        center_y: int,
        robot_pos: Dict[str, float],
        calibration_list: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Updates or adds a marker's origin point and robot_pos in the calibration list.
        The list is modified in place.

        Args:
            marker_id_to_update: The ID of the marker to update.
            center_x: The x-coordinate of the marker's new origin.
            center_y: The y-coordinate of the marker's new origin.
            robot_pos: The robot position dictionary (e.g., {"x": 0.0, "y": 0.0}).
            calibration_list: The list of current calibration data.

        Returns:
            list: The updated calibration list.
        """
        found = False
        for marker_data in calibration_list:
            if marker_data.get("id") == marker_id_to_update:
                marker_data["origin_point"] = {"x": center_x, "y": center_y}
                marker_data["robot_pos"] = robot_pos
                found = True
                break
        if not found:
            calibration_list.append(
                {
                    "id": marker_id_to_update,
                    "origin_point": {"x": center_x, "y": center_y},
                    "robot_pos": robot_pos,
                }
            )
        return calibration_list
