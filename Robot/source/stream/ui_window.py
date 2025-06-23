from typing import Dict, Any
import threading
import time

import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QImage, QPixmap

import stream.shared_state as shared_state
from stream.stream_handler import StreamHandler
from stream.marker_detector import MarkerDetector
from stream.video_analyzer import VideoAnalyzer
import stream.color_filter_module as color_filter_module
from stream.color_settings_window import ColorSettingsWindow



class UIWindow(QObject):
    """Manages the application window and user interactions."""
    frame_ready = Signal(np.ndarray, object)

    def __init__(
        self,
        stream_handler: StreamHandler,
        marker_detector: MarkerDetector,
        video_analyzer: VideoAnalyzer,
    ):
        """
        Initialize the UI window.

        Args:
            stream_handler: Instance of StreamHandler
            marker_detector: Instance of MarkerDetector
            video_analyzer: Instance of VideoAnalyzer
        """
        super().__init__()
        self.frame_ready.connect(self._update_qlabel_slot)
        self.stream_handler = stream_handler
        self.marker_detector = marker_detector
        self.video_analyzer = video_analyzer
        self.color_settings_window = None
        self.running = False
        self.initial_frame_width, self.initial_frame_height = (
            stream_handler.get_frame_dimensions()
        )
        self.latest_display_frame = None
        self.latest_color_analysis_frame = None
        self.processing_lock = threading.Lock()
        self.processing_thread = None
        self.processing_running = False
        self.frame_ready_event = threading.Event()


    def setup_window(self) -> None:
        """Setup the OpenCV window."""
        self.color_settings_window = ColorSettingsWindow()

    def _mouse_callback(
        self, event: int, x: int, y: int, flags: int, param: Dict[str, Any]
    ) -> None:
        """
        Handles mouse events for zooming, panning, and ROI selection.

        Args:
            event: Mouse event type
            x: Mouse x coordinate
            y: Mouse y coordinate
            flags: Event flags
            param: Additional parameters
        """
        with shared_state.data_lock:
            if shared_state.g_zoom_scale == 1.0:
                if event == cv2.EVENT_LBUTTONDOWN and not shared_state.g_roi_confirmed:
                    shared_state.g_roi_selection_active = True
                    shared_state.g_roi_selection_start = (x, y)
                    shared_state.g_roi_selection_end = (x, y)
                elif event == cv2.EVENT_MOUSEMOVE and shared_state.g_roi_selection_active:
                    shared_state.g_roi_selection_end = (x, y)
                elif event == cv2.EVENT_LBUTTONUP and shared_state.g_roi_selection_active:
                    shared_state.g_roi_selection_active = False
                    shared_state.g_roi_selection_end = (x, y)
            if event == cv2.EVENT_MOUSEWHEEL:
                mouse_x_in_original = shared_state.g_current_roi_top_left_x + (
                    x / shared_state.g_zoom_scale
                )
                mouse_y_in_original = shared_state.g_current_roi_top_left_y + (
                    y / shared_state.g_zoom_scale
                )
                shared_state.g_zoom_center_original_x = mouse_x_in_original
                shared_state.g_zoom_center_original_y = mouse_y_in_original
                if flags > 0:
                    shared_state.g_zoom_scale *= 1.1
                else:
                    shared_state.g_zoom_scale /= 1.1
                shared_state.g_zoom_scale = max(1.0, min(shared_state.g_zoom_scale, 10.0))
                if shared_state.g_zoom_scale == 1.0:
                    shared_state.g_zoom_center_original_x = None
                    shared_state.g_zoom_center_original_y = None
            elif event == cv2.EVENT_LBUTTONDOWN and shared_state.g_zoom_scale > 1.0:
                shared_state.g_zoom_center_original_x = (
                    shared_state.g_current_roi_top_left_x + (x / shared_state.g_zoom_scale)
                )
                shared_state.g_zoom_center_original_y = (
                    shared_state.g_current_roi_top_left_y + (y / shared_state.g_zoom_scale)
                )

    def _apply_zoom(self, display_frame: np.ndarray) -> np.ndarray:
        """
        Apply zoom to the display frame.

        Args:
            display_frame: Original frame

        Returns:
            np.ndarray: Zoomed frame
        """
        original_display_h, original_display_w = display_frame.shape[:2]
        zoomed_display_frame = display_frame.copy()
        if (
            shared_state.g_zoom_scale > 1.0
            and shared_state.g_zoom_center_original_x is not None
            and shared_state.g_zoom_center_original_y is not None
        ):
            roi_w_orig = int(original_display_w / shared_state.g_zoom_scale)
            roi_h_orig = int(original_display_h / shared_state.g_zoom_scale)
            clamped_center_x = max(
                roi_w_orig / 2,
                min(
                    shared_state.g_zoom_center_original_x,
                    original_display_w - roi_w_orig / 2,
                ),
            )
            clamped_center_y = max(
                roi_h_orig / 2,
                min(
                    shared_state.g_zoom_center_original_y,
                    original_display_h - roi_h_orig / 2,
                ),
            )
            shared_state.g_current_roi_top_left_x = int(
                clamped_center_x - roi_w_orig / 2
            )
            shared_state.g_current_roi_top_left_y = int(
                clamped_center_y - roi_h_orig / 2
            )
            shared_state.g_current_roi_top_left_x = max(
                0,
                min(
                    shared_state.g_current_roi_top_left_x,
                    original_display_w - roi_w_orig,
                ),
            )
            shared_state.g_current_roi_top_left_y = max(
                0,
                min(
                    shared_state.g_current_roi_top_left_y,
                    original_display_h - roi_h_orig,
                ),
            )
            roi_x1 = shared_state.g_current_roi_top_left_x
            roi_y1 = shared_state.g_current_roi_top_left_y
            roi_x2 = shared_state.g_current_roi_top_left_x + roi_w_orig
            roi_y2 = shared_state.g_current_roi_top_left_y + roi_h_orig
            if roi_x2 > roi_x1 and roi_y2 > roi_y1:
                roi = display_frame[roi_y1:roi_y2, roi_x1:roi_x2]
                if roi.size > 0:
                    zoomed_display_frame = cv2.resize(
                        roi,
                        (self.initial_frame_width, self.initial_frame_height),
                        interpolation=cv2.INTER_LINEAR,
                    )
                else:
                    self._reset_zoom()
            else:
                self._reset_zoom()
        else:
            shared_state.g_current_roi_top_left_x = 0
            shared_state.g_current_roi_top_left_y = 0
            if shared_state.g_zoom_scale != 1.0 and (
                shared_state.g_zoom_center_original_x is None
                or shared_state.g_zoom_center_original_y is None
            ):
                shared_state.g_zoom_scale = 1.0
        return zoomed_display_frame

    def _reset_zoom(self) -> None:
        """Reset zoom settings to default."""
        with shared_state.data_lock:
            shared_state.g_zoom_scale = 1.0
            shared_state.g_zoom_center_original_x = None
            shared_state.g_zoom_center_original_y = None
            shared_state.g_current_roi_top_left_x = 0
            shared_state.g_current_roi_top_left_y = 0

    def toggle_fullscreen(self) -> None:
        """Toggle fullscreen mode."""
        shared_state.g_is_fullscreen = not shared_state.g_is_fullscreen
        if shared_state.g_is_fullscreen:
            cv2.setWindowProperty(
                shared_state.g_window_name,
                cv2.WND_PROP_FULLSCREEN,
                cv2.WINDOW_FULLSCREEN,
            )
        else:
            cv2.setWindowProperty(
                shared_state.g_window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_NORMAL
            )
            cv2.resizeWindow(
                shared_state.g_window_name,
                self.initial_frame_width,
                self.initial_frame_height,
            )

    def process_key(self, key: int) -> bool:
        """
        Process keyboard input.

        Args:
            key: Key code

        Returns:
            bool: True to continue running, False to exit
        """
        if key == 27:
            return False
        elif key == ord("l"):
            with shared_state.data_lock:
                shared_state.calibrated_marker_origins = (
                    self.marker_detector.load_calibration_data(
                        shared_state.CALIBRATION_FILE_PATH
                    )
                )
                if shared_state.calibrated_marker_origins:
                    self.video_analyzer.calculate_and_store_transformation(
                        shared_state.calibrated_marker_origins
                    )
        elif key == ord("f"):
            self.toggle_fullscreen()
        elif key == ord("r"):
            self._reset_zoom()
        elif key == ord("q"):
            new_saturation = self.stream_handler.increase_saturation()
        elif key == ord("e"):
            new_saturation = self.stream_handler.decrease_saturation()
        elif key == ord("a"):
            new_brightness = self.stream_handler.increase_brightness()
        elif key == ord("d"):
            new_brightness = self.stream_handler.decrease_brightness()
        elif key == ord("y"):
            new_sharpness = self.stream_handler.increase_sharpness()
        elif key == ord("x"):
            new_sharpness = self.stream_handler.decrease_sharpness()
        elif key == 13:
            with shared_state.data_lock:
                if shared_state.g_roi_selection_start and shared_state.g_roi_selection_end:
                    shared_state.g_roi_confirmed = True
        elif key == ord("c"):
            with shared_state.data_lock:
                shared_state.g_roi_selection_start = None
                shared_state.g_roi_selection_end = None
                shared_state.g_roi_confirmed = False
                shared_state.g_roi_rotation_angle = 0
        elif key == ord("v"):
            with shared_state.data_lock:
                if shared_state.g_roi_confirmed:
                    shared_state.g_roi_rotation_angle = (
                        shared_state.g_roi_rotation_angle - 5
                    ) % 360
        elif key == ord("b"):
            with shared_state.data_lock:
                if shared_state.g_roi_confirmed:
                    shared_state.g_roi_rotation_angle = (
                        shared_state.g_roi_rotation_angle + 5
                    ) % 360
        elif key == ord("k"):
            if self.color_settings_window:
                if cv2.getWindowProperty(shared_state.COLOR_SETTINGS_WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                    self.color_settings_window.show()
                else:
                    self.color_settings_window.hide()
        return True

    def _processing_loop(self):
        """Handles frame acquisition and processing in a separate thread."""
        while self.processing_running:
            ret, frame = self.stream_handler.get_frame()
            if not ret:
                time.sleep(0.05)
                continue
            original_frame_copy = frame.copy()
            pre_color_filtered_base = color_filter_module.apply_color_filter(frame.copy(), shared_state.MIN_AREA_COLOR_FILTER)
            processed_frame_for_color_analysis = pre_color_filtered_base.copy()
            processed_current_display_frame = original_frame_copy.copy()
            with shared_state.data_lock:
                roi_confirmed_local = shared_state.g_roi_confirmed
                roi_selection_start_local = shared_state.g_roi_selection_start
                if roi_selection_start_local: roi_selection_start_local = tuple(roi_selection_start_local)
                roi_selection_end_local = shared_state.g_roi_selection_end
                if roi_selection_end_local: roi_selection_end_local = tuple(roi_selection_end_local)
                roi_rotation_angle_local = shared_state.g_roi_rotation_angle
            detected_centers_this_frame = {}
            box_points_for_drawing_roi = None
            if roi_confirmed_local and roi_selection_start_local and roi_selection_end_local:
                x1 = min(roi_selection_start_local[0], roi_selection_end_local[0])
                y1 = min(roi_selection_start_local[1], roi_selection_end_local[1])
                x2 = max(roi_selection_start_local[0], roi_selection_end_local[0])
                y2 = max(roi_selection_start_local[1], roi_selection_end_local[1])
                roi_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
                if roi_rotation_angle_local == 0:
                    cv2.rectangle(roi_mask, (x1, y1), (x2, y2), 255, -1)
                else:
                    center_x = (x1 + x2) // 2
                    center_y = (y1 + y2) // 2
                    width = x2 - x1
                    height = y2 - y1
                    rect = ((center_x, center_y), (width, height), roi_rotation_angle_local)
                    box_points_for_drawing_roi = cv2.boxPoints(rect)
                    box_points_for_drawing_roi = np.int64(box_points_for_drawing_roi)
                    cv2.drawContours(roi_mask, [box_points_for_drawing_roi], 0, 255, -1)
                frame_for_marker_detection_roi = cv2.bitwise_and(original_frame_copy.copy(), original_frame_copy.copy(), mask=roi_mask)
                processed_frame_for_color_analysis = cv2.bitwise_and(pre_color_filtered_base.copy(), pre_color_filtered_base.copy(), mask=roi_mask)
                marker_output_frame, detected_centers_this_frame = self.marker_detector.process_frame(frame_for_marker_detection_roi)
                alpha = 0.7
                base_for_blend = cv2.bitwise_and(original_frame_copy.copy(), original_frame_copy.copy(), mask=roi_mask)
                processed_current_display_frame = cv2.addWeighted(base_for_blend, alpha, marker_output_frame, 1 - alpha, 0)
                inverse_roi_mask = cv2.bitwise_not(roi_mask)
                background = cv2.bitwise_and(original_frame_copy.copy(), original_frame_copy.copy(), mask=inverse_roi_mask)
                processed_current_display_frame = cv2.add(processed_current_display_frame, background)
                if roi_rotation_angle_local == 0:
                    cv2.rectangle(processed_current_display_frame, (x1, y1), (x2, y2), (0, 0, 0), 2)
                else:
                    if box_points_for_drawing_roi is not None:
                        cv2.drawContours(processed_current_display_frame, [box_points_for_drawing_roi], 0, (0, 0, 0), 2)
            else:
                marker_output_frame, detected_centers_this_frame = self.marker_detector.process_frame(original_frame_copy.copy())
                processed_current_display_frame = marker_output_frame
            with shared_state.data_lock:
                shared_state.current_detected_marker_centers = detected_centers_this_frame.copy()
            _, color_data_for_this_frame = self.video_analyzer.find_color(
                processed_frame_for_color_analysis.copy()
            )
            processed_current_display_frame, _ = self.video_analyzer.find_color(
                processed_frame_for_color_analysis.copy(),
                display_frame=processed_current_display_frame
            )
            with shared_state.data_lock:
                shared_state.current_detected_color_objects_info = color_data_for_this_frame.copy()
            self.marker_detector.draw_calibrated_origins(
                processed_current_display_frame, shared_state.calibrated_marker_origins
            )
            with self.processing_lock:
                self.latest_display_frame = processed_current_display_frame
                self.latest_color_analysis_frame = processed_frame_for_color_analysis
            self.frame_ready_event.set()

    def run(self, main_window) -> None:
        """Run the main UI loop."""
        self.running = True
        self.processing_running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        while self.running:
            new_frame_available = self.frame_ready_event.wait(timeout=0.01)
            display_frame_to_show = None
            color_analysis_frame_to_show = None
            if new_frame_available:
                with self.processing_lock:
                    if self.latest_display_frame is not None:
                        display_frame_to_show = self.latest_display_frame.copy()
                    if self.latest_color_analysis_frame is not None:
                        color_analysis_frame_to_show = self.latest_color_analysis_frame.copy()
                self.frame_ready_event.clear()
            else:
                with self.processing_lock:
                    if self.latest_display_frame is not None:
                        display_frame_to_show = self.latest_display_frame.copy()
                    if self.latest_color_analysis_frame is not None:
                        color_analysis_frame_to_show = self.latest_color_analysis_frame.copy()
            if display_frame_to_show is not None:
                with shared_state.data_lock:
                    roi_selection_active_local = shared_state.g_roi_selection_active
                    roi_selection_start_local = shared_state.g_roi_selection_start
                    roi_selection_end_local = shared_state.g_roi_selection_end
                    roi_confirmed_local = shared_state.g_roi_confirmed
                if roi_selection_active_local and not roi_confirmed_local and roi_selection_start_local and roi_selection_end_local:
                    sx1 = min(roi_selection_start_local[0], roi_selection_end_local[0])
                    sy1 = min(roi_selection_start_local[1], roi_selection_end_local[1])
                    sx2 = max(roi_selection_start_local[0], roi_selection_end_local[0])
                    sy2 = max(roi_selection_start_local[1], roi_selection_end_local[1])
                    cv2.rectangle(display_frame_to_show, (sx1, sy1), (sx2, sy2), (255, 0, 0), 2)
                zoomed_display_frame = self._apply_zoom(display_frame_to_show)
                self._update_qlabel_slot(zoomed_display_frame, main_window.camera_display)
            if color_analysis_frame_to_show is not None and color_analysis_frame_to_show.size > 0 :
                self._update_qlabel_slot(color_analysis_frame_to_show, main_window.color_analysis)
            if self.color_settings_window:
                try:
                    if cv2.getWindowProperty(shared_state.COLOR_SETTINGS_WINDOW_NAME, cv2.WND_PROP_VISIBLE) >= 1:
                        self.color_settings_window.update_display()
                except cv2.error:
                    pass
            key = cv2.waitKey(1) & 0xFF
            if not self.process_key(key) or not main_window.stream_running:
                main_window.camera_display.setText("Sorry, the camera is not available.")
                main_window.color_analysis.setText("Sorry, the camera is not available.")
                self.running = False
                break
        self.processing_running = False
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=1.0)
        if self.color_settings_window:
            self.color_settings_window.hide()
        cv2.destroyAllWindows()

    def _update_qlabel_slot(self, frame, qlabel):
        """Slot to update QLabel with new frame (runs in main thread)."""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_frame.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format_RGB888)
            label_size = qlabel.size()
            pixmap = QPixmap.fromImage(qt_image)
            scaled_pixmap = pixmap.scaled(
                label_size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            qlabel.setPixmap(scaled_pixmap)
        except:
            pass

    def _display_frame(self, frame, qlabel):
        """Display OpenCV frame in QLabel widget."""
        if hasattr(self, 'frame_ready'):
            self.frame_ready.emit(frame.copy(), qlabel)

    def stop(self) -> None:
        """Stop the UI loop and processing thread."""
        self.running = False
        self.processing_running = False
        if self.color_settings_window:
            try:
                self.color_settings_window.hide()
            except Exception:
                pass
