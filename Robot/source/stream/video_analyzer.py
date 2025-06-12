import cv2
import numpy as np
import math
from typing import Dict, List, Tuple, Any, Optional
import stream.shared_state as shared_state


class VideoAnalyzer:
    """Analyzes video frames for color detection and coordinate transformations."""
    def __init__(self):
        """Initialize the video analyzer."""
        pass

    def find_color(
        self, frame: np.ndarray, display_frame: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, List[Dict[str, Any]]]:
        """
        Finds objects of predefined colors in the frame, calculates their centers,
        converts to robot coordinates, and draws them on the frame.
        Filters for rectangular shapes.

        Args:
            frame: The frame to process.
            display_frame: Optional frame to draw detections on. If None, a copy of the input frame is used.

        Returns:
            tuple: (frame with detections, detected objects list)
                  - The frame with color detections drawn on it.
                  - A list of dictionaries, each containing info about a detected object.
        """
        original_frame_for_color_sampling = frame.copy()
        hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        detected_color_objects_list = []
        frame_to_process_and_draw_on = (
            display_frame if display_frame is not None else frame.copy()
        )
        for color_name, color_data in shared_state.COLOR_RANGES_HSV.items():
            lower_bound = color_data["lower"]
            upper_bound = color_data["upper"]
            draw_bgr_color_tuple = color_data["draw_color"]
            mask = cv2.inRange(hsv_frame, lower_bound, upper_bound)
            mask = cv2.erode(mask, None, iterations=2)
            mask = cv2.dilate(mask, None, iterations=2)
            contours, _ = cv2.findContours(
                mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            for contour in contours:
                if cv2.contourArea(contour) < 400:
                    continue
                perimeter = cv2.arcLength(contour, True)
                approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
                if len(approx) == 4:
                    M = cv2.moments(contour)
                    if M["m00"] == 0:
                        continue
                    center_x_cam = int(M["m10"] / M["m00"])
                    center_y_cam = int(M["m01"] / M["m00"])
                    mask_for_mean_color = np.zeros(hsv_frame.shape[:2], dtype="uint8")
                    cv2.drawContours(mask_for_mean_color, [approx], -1, 255, -1)
                    mean_val = cv2.mean(
                        original_frame_for_color_sampling, mask=mask_for_mean_color
                    )
                    actual_detected_bgr = (
                        int(mean_val[0]),
                        int(mean_val[1]),
                        int(mean_val[2]),
                    )
                    actual_detected_rgb = (
                        actual_detected_bgr[2],
                        actual_detected_bgr[1],
                        actual_detected_bgr[0],
                    )
                    robot_x, robot_y = self.convert_camera_to_robot(
                        center_x_cam, center_y_cam
                    )
                    if (
                        robot_x is not None
                        and robot_y is not None
                        and math.isfinite(robot_x)
                        and math.isfinite(robot_y)
                    ):
                        detected_color_objects_list.append(
                            {
                                "bgr_tuple": draw_bgr_color_tuple,
                                "robot_pos": {"x": robot_x, "y": robot_y},
                            }
                        )
                    cv2.drawContours(
                        frame_to_process_and_draw_on,
                        [approx],
                        -1,
                        draw_bgr_color_tuple,
                        2,
                    )
                    cv2.circle(
                        frame_to_process_and_draw_on,
                        (center_x_cam, center_y_cam),
                        7,
                        (255, 255, 255),
                        -1,
                    )
                    cv2.circle(
                        frame_to_process_and_draw_on,
                        (center_x_cam, center_y_cam),
                        5,
                        draw_bgr_color_tuple,
                        -1,
                    )
                    text_to_display = f"RGB: {actual_detected_rgb}"
                    if (
                        robot_x is not None
                        and robot_y is not None
                        and math.isfinite(robot_x)
                        and math.isfinite(robot_y)
                    ):
                        text_to_display += f" Rob:({robot_x:.1f}, {robot_y:.1f})"
                    else:
                        text_to_display += f" Cam:({center_x_cam}, {center_y_cam})"
                    text_x = center_x_cam - 60
                    text_y = center_y_cam - 20
                    if text_y < 10:
                        text_y = center_y_cam + 30
                    if text_x < 0:
                        text_x = 10
                    cv2.putText(
                        frame_to_process_and_draw_on,
                        text_to_display,
                        (text_x, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.4,
                        draw_bgr_color_tuple,
                        1,
                    )
        return frame_to_process_and_draw_on, detected_color_objects_list

    def calculate_and_store_transformation(
        self, calibration_data: List[Dict[str, Any]]
    ) -> Tuple[bool, str, Optional[np.ndarray]]:
        """
        Calculates the affine transformation from camera coordinates to robot coordinates
        using the provided calibration data and stores it globally.

        Args:
            calibration_data: A list of dictionaries containing calibration data.

        Returns:
            tuple: (success, message, matrix)
                   - success: True if transformation was calculated, False otherwise.
                   - message: A message describing the outcome.
                   - matrix: The 2x3 transformation matrix, or None on failure.
        """
        camera_points = []
        robot_points = []
        for entry in calibration_data:
            if "origin_point" in entry and "robot_pos" in entry:
                try:
                    cam_x = float(entry["origin_point"]["x"])
                    cam_y = float(entry["origin_point"]["y"])
                    rob_x = float(entry["robot_pos"]["x"])
                    rob_y = float(entry["robot_pos"]["y"])
                    camera_points.append([cam_x, cam_y])
                    robot_points.append([rob_x, rob_y])
                except (TypeError, ValueError) as e:
                    continue
        if len(camera_points) < 3:
            msg = f"Insufficient valid calibration points to calculate transformation. Need at least 3, found {len(camera_points)}."
            with shared_state.data_lock:
                shared_state.global_transformation_matrix = None
            return False, msg, None
        src_pts = np.float32(camera_points)
        dst_pts = np.float32(robot_points)
        transform_matrix, inliers = cv2.estimateAffine2D(
            src_pts, dst_pts, method=cv2.RANSAC, ransacReprojThreshold=20.0
        )
        if transform_matrix is not None:
            num_inliers = np.sum(inliers) if inliers is not None else 0
            with shared_state.data_lock:
                shared_state.global_transformation_matrix = transform_matrix
            msg = f"Successfully calculated and stored transformation matrix using {num_inliers}/{len(src_pts)} points."
            return True, msg, transform_matrix
        else:
            msg = "Failed to calculate transformation matrix (cv2.estimateAffine2D returned None). Check if points are collinear or insufficient."
            with shared_state.data_lock:
                shared_state.global_transformation_matrix = None
            return False, msg, None

    def convert_camera_to_robot(
        self, camera_x: float, camera_y: float
    ) -> Tuple[Optional[float], Optional[float]]:
        """
        Converts camera coordinates to robot coordinates using the globally stored
        affine transformation matrix.

        Args:
            camera_x: The x-coordinate in the camera's frame.
            camera_y: The y-coordinate in the camera's frame.

        Returns:
            tuple: (robot_x, robot_y) or (None, None) if transformation matrix is not available.
        """
        with shared_state.data_lock:
            current_matrix = shared_state.global_transformation_matrix
        if current_matrix is None:
            return None, None
        cam_point = np.array([[[float(camera_x), float(camera_y)]]], dtype=np.float32)
        if isinstance(current_matrix, np.ndarray):
            try:
                transformed_point = cv2.transform(cam_point, current_matrix)
                return transformed_point[0][0][0], transformed_point[0][0][1]
            except cv2.error as e:
                return None, None
        else:
            return None, None
