import cv2
import numpy as np
import stream.shared_state as shared_state
import os
from typing import Dict, List, Optional
import json
import tkinter as tk
from tkinter import filedialog


def _numpy_to_list_converter(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.integer):
        return int(obj)
    if isinstance(obj, np.floating):
        return float(obj)
    try:
        return obj.item()
    except AttributeError:
        pass
    return obj

class ColorSettingsWindow:
    """A simplified class to manage color filter settings with a clean UI."""
    def __init__(self):
        """Initialize the color settings window with a clean, simple UI."""
        self.window_name = shared_state.COLOR_SETTINGS_WINDOW_NAME
        self.window_width = 1000
        self.window_height = 700
        self.background_color = (255, 255, 255)
        self.panel_bg_color = (240, 240, 240)
        self.text_color = (0, 0, 0)
        self.slider_color = (100, 100, 100)
        self.slider_fill_color = (70, 130, 180)
        self.divider_color = (200, 200, 200)
        self.header_height = 40
        self.control_height = 30
        self.panel_padding = 10
        self.slider_height = 20
        self.slider_width = 300
        self.label_width = 120
        self.value_width = 50
        self.split_ratio = 0.5
        self.scroll_position = 0
        self.max_scroll_position = 0
        self.scroll_drag_active = False
        self.scroll_start_y = 0
        self.active_slider_info = None
        self.slider_drag_start_x = 0
        self.slider_drag_value_on_start = 0
        self.hover_element = None
        self.all_sliders: List[Dict] = []
        self._populate_slider_definitions()
        self.current_sample_index = 0
        self.sample_images = []
        self.sample_image_paths = []
        self.sample_filtered_images = {}
        self.load_sample_images()
        self.slider_values: Dict[str, int] = {}
        self.initialize_slider_values()
        self._initialize_tk()
        self.setup_window()

    def show(self) -> None:
        """Show the color settings window."""
        self.setup_window()

    def _initialize_tk(self):
        """Initializes a hidden Tkinter root window for file dialogs."""
        try:
            self.tk_root = tk.Tk()
            self.tk_root.withdraw()
        except tk.TclError as e:
            self.tk_root = None

    def _populate_slider_definitions(self):
        """Populate the self.all_sliders list with definitions for all UI sliders and buttons."""
        self.all_sliders = []
        color_configs = [
            {"name": "RED (Lower)", "key": "red", "range_idx": 0, "color": (0, 0, 255)},
            {"name": "RED (Upper)", "key": "red", "range_idx": 1, "color": (0, 0, 255)},
            {"name": "GREEN", "key": "green", "range_idx": 0, "color": (0, 255, 0)},
            {"name": "BLUE", "key": "blue", "range_idx": 0, "color": (255, 0, 0)},
            {"name": "YELLOW", "key": "yellow", "range_idx": 0, "color": (0, 255, 255)}
        ]
        for config in color_configs:
            color_key = config["key"]
            range_idx = config["range_idx"]
            group_name = config["name"]
            group_color = config["color"]
            for bound_idx, bound_name in enumerate(["Low", "High"]):
                for comp_idx, comp_name in enumerate(["H", "S", "V"]):
                    slider_id = f"{color_key}_{range_idx}_{bound_idx}_{comp_idx}"
                    label = f"{comp_name} {bound_name}"
                    max_val = 179 if comp_name == "H" else 255
                    self.all_sliders.append({
                        "id": slider_id,
                        "label": label,
                        "max_value": max_val,
                        "type": "color",
                        "group_name": group_name,
                        "group_color": group_color,
                        "color_key": color_key,
                        "range_idx": range_idx,
                        "bound_idx": bound_idx,
                        "comp_idx": comp_idx
                    })
        global_setting_configs = [
            {"name": "D-THRESHOLD", "key": "s_desaturated_threshold", "max_value": 255},
            {"name": "WHITE-MAX", "key": "s_white_max", "max_value": 255},
            {"name": "WHITE-MIN", "key": "v_white_min", "max_value": 255}
        ]
        global_group_name = "Global Settings"
        global_group_color = (0, 165, 255)
        for config in global_setting_configs:
            self.all_sliders.append({
                "id": config["key"],
                "label": config["name"],
                "max_value": config["max_value"],
                "type": "global",
                "group_name": global_group_name,
                "group_color": global_group_color,
                "global_key": config["key"]
            })
        action_button_configs = [
            {"name": "Einstellungen Speichern", "action": "save_settings"},
            {"name": "Einstellungen Laden", "action": "load_settings"},
        ]
        action_button_group_name = "Dateioperationen"
        action_button_group_color = (100, 100, 100)
        for config in action_button_configs:
            self.all_sliders.append({
                "id": config["action"],
                "label": config["name"],
                "type": "action_button",
                "group_name": action_button_group_name,
                "group_color": action_button_group_color,
                "action": config["action"]
            })

    def initialize_slider_values(self):
        """Initialize slider values from shared state using the unified slider definitions."""
        with shared_state.data_lock:
            for slider_def in self.all_sliders:
                if slider_def["type"] not in ["color", "global"]:
                    continue
                slider_id = slider_def["id"]
                value = 0
                if slider_def["type"] == "color":
                    color_key = slider_def["color_key"]
                    range_idx = slider_def["range_idx"]
                    bound_idx = slider_def["bound_idx"]
                    comp_idx = slider_def["comp_idx"]
                    if color_key in shared_state.COLOR_FILTER and \
                       range_idx < len(shared_state.COLOR_FILTER[color_key]) and \
                       shared_state.COLOR_FILTER[color_key][range_idx] and \
                       bound_idx < len(shared_state.COLOR_FILTER[color_key][range_idx]) and \
                       comp_idx < len(shared_state.COLOR_FILTER[color_key][range_idx][bound_idx]):
                        value = shared_state.COLOR_FILTER[color_key][range_idx][bound_idx][comp_idx]
                    else:
                        if color_key not in shared_state.COLOR_FILTER:
                             shared_state.COLOR_FILTER[color_key] = []
                        while range_idx >= len(shared_state.COLOR_FILTER[color_key]):
                            shared_state.COLOR_FILTER[color_key].append( (np.array([0,0,0]), np.array([179,255,255])) )
                        if bound_idx < len(shared_state.COLOR_FILTER[color_key][range_idx]) and \
                           comp_idx < len(shared_state.COLOR_FILTER[color_key][range_idx][bound_idx]):
                             value = shared_state.COLOR_FILTER[color_key][range_idx][bound_idx][comp_idx]
                        else:
                             value = 0
                elif slider_def["type"] == "global":
                    global_key_in_def = slider_def["global_key"]
                    shared_state_attr_name = global_key_in_def.upper()
                    if hasattr(shared_state, shared_state_attr_name):
                        value = getattr(shared_state, shared_state_attr_name)
                self.slider_values[slider_id] = value

    def load_sample_images(self):
        """Load sample images for testing color filters."""
        h, w = 300, 300
        color_wheel = np.zeros((h, w, 3), dtype=np.uint8)
        center = (w//2, h//2)
        radius = min(w, h) // 2 - 10
        for y in range(h):
            for x in range(w):
                dx, dy = x - center[0], y - center[1]
                distance = np.sqrt(dx**2 + dy**2)
                if distance < radius:
                    angle = np.arctan2(dy, dx) * 180 / np.pi
                    if angle < 0:
                        angle += 360
                    hue = int(angle / 2)
                    sat = min(255, int((distance / radius) * 255))
                    val = 255
                    color_wheel[y, x] = [hue, sat, val]
        color_wheel = cv2.cvtColor(color_wheel, cv2.COLOR_HSV2BGR)
        self.sample_images = [color_wheel]
        self.sample_image_paths = ["Default Color Wheel"]
        sample_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples")
        if os.path.exists(sample_dir):
            for filename in os.listdir(sample_dir):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                    filepath = os.path.join(sample_dir, filename)
                    try:
                        img = cv2.imread(filepath)
                        if img is not None:
                            self.sample_images.append(img)
                            self.sample_image_paths.append(filename)
                    except Exception as e:
                        pass

    def setup_window(self) -> None:
        """Create the window and set initial properties."""
        cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.window_name, self.window_width, self.window_height)
        cv2.setMouseCallback(self.window_name, self._mouse_callback)
        self.update_display()

    def _mouse_callback(self, event: int, x: int, y: int, flags: int, param: None) -> None:
        """Handle mouse interactions."""
        self.hover_element = self._get_element_at_position(x, y)
        if event == cv2.EVENT_LBUTTONDOWN:
            if self._handle_sample_click(x, y):
                return
            clicked_control_info = self._get_control_at_position(x, y)
            if clicked_control_info:
                control_def = clicked_control_info["definition"]
                control_type = control_def["type"]
                if control_type == "action_button":
                    action = control_def["action"]
                    if action == "save_settings":
                        self.save_settings()
                    elif action == "load_settings":
                        self.load_settings()
                    return
                elif control_type == "color" or control_type == "global":
                    self.active_slider_info = clicked_control_info
                    self.slider_drag_start_x = x
                    self.slider_drag_value_on_start = self.get_slider_value(clicked_control_info["id"])
                    self.update_display()
                    return
            scrollbar_info = self._is_on_scrollbar(x, y)
            if scrollbar_info:
                self.scroll_drag_active = True
                self.scroll_start_y = y
                return
        elif event == cv2.EVENT_LBUTTONUP:
            self.active_slider_info = None
            self.scroll_drag_active = False
        elif event == cv2.EVENT_MOUSEMOVE:
            if self.active_slider_info:
                slider_max_value = self.active_slider_info["max_value"]
                start_val_py_int = int(self.slider_drag_value_on_start)
                max_val_py_int = int(slider_max_value)
                drag_distance = x - self.slider_drag_start_x
                if self.slider_width == 0:
                    value_change_ratio = 0.0
                else:
                    value_change_ratio = drag_distance / self.slider_width
                value_change = int(value_change_ratio * max_val_py_int)
                calculated_py_int_value = start_val_py_int + value_change
                clamped_value = max(0, min(max_val_py_int, calculated_py_int_value))
                self.set_slider_value(self.active_slider_info["id"], clamped_value)
                self.update_display()
                return
            if self.scroll_drag_active:
                content_height = self._get_content_height()
                visible_height = self.window_height - self.header_height
                if content_height > visible_height:
                    mouse_delta_y_since_last_event = y - self.scroll_start_y
                    if visible_height > 0:
                        scroll_scaling_factor = content_height / visible_height
                        scroll_amount_delta_for_content = int(mouse_delta_y_since_last_event * scroll_scaling_factor)
                    else:
                        scroll_amount_delta_for_content = mouse_delta_y_since_last_event
                    new_scroll_pos = self.scroll_position + scroll_amount_delta_for_content
                    self.scroll_position = max(0, min(self.max_scroll_position, new_scroll_pos))
                    self.scroll_start_y = y
                    self.update_display()
                    return
            self.update_display()
        elif event == cv2.EVENT_MOUSEWHEEL:
            wheel_direction = -1 if flags > 0 else 1
            scroll_amount = 40 * wheel_direction
            new_scroll = self.scroll_position + scroll_amount
            self.scroll_position = max(0, min(self.max_scroll_position, new_scroll))
            self.update_display()

    def _get_content_height(self) -> int:
        """Calculate the total content height based on unified slider definitions and consistent spacing."""
        content_h = self.panel_padding
        active_group_for_height_calc = None
        for slider_def in self.all_sliders:
            if slider_def["group_name"] != active_group_for_height_calc:
                content_h += self.control_height
                content_h += self.panel_padding
                active_group_for_height_calc = slider_def["group_name"]
            content_h += self.control_height
            content_h += self.panel_padding
        return content_h

    def _get_element_at_position(self, x: int, y: int) -> Optional[Dict]:
        """Determine what UI element is at the given position."""
        left_panel_width = int(self.window_width * self.split_ratio) - 5
        if x > left_panel_width:
            return {"type": "right_panel", "x": x, "y": y}
        adjusted_y = y - self.header_height + self.scroll_position
        control_info = self._get_control_at_position(x, y)
        if control_info:
            if control_info["definition"]["type"] == "action_button":
                 return {"type": "button", "info": control_info}
            else:
                 return {"type": "slider", "info": control_info}
        scrollbar_info = self._is_on_scrollbar(x, y)
        if scrollbar_info:
            return {"type": "scrollbar"}
        return None

    def _handle_sample_click(self, x: int, y: int) -> bool:
        """Handle clicks on sample images."""
        left_panel_width = int(self.window_width * self.split_ratio) - 5
        if x <= left_panel_width:
            return False
        right_panel_y = self.header_height + 20
        right_panel_height = self.window_height - right_panel_y
        if y < right_panel_y + right_panel_height / 2:
            samples_per_row = 3
            thumb_width = (self.window_width - left_panel_width - 30) / samples_per_row
            thumb_height = thumb_width * 0.75
            rel_x = x - left_panel_width - 10
            rel_y = y - right_panel_y - 40
            if rel_y > 0:
                row = int(rel_y / (thumb_height + 10))
                col = int(rel_x / (thumb_width + 10))
                index = row * samples_per_row + col
                if 0 <= index < len(self.sample_images):
                    self.current_sample_index = index
                    self._update_filtered_sample()
                    self.update_display()
                    return True
        return False

    def _is_on_scrollbar(self, x: int, y: int) -> bool:
        """Check if the position is on the scrollbar."""
        left_panel_width = int(self.window_width * self.split_ratio) - 5
        scrollbar_width = 12
        scrollbar_x = left_panel_width - scrollbar_width - 10
        if not (scrollbar_x <= x <= scrollbar_x + scrollbar_width):
            return None
        content_height = self._get_content_height()
        visible_height = self.window_height - self.header_height
        if content_height > visible_height:
            if self.max_scroll_position == 0:
                 if content_height > visible_height:
                      self.max_scroll_position = content_height - visible_height
                 else:
                      return None
            scrollbar_handle_height = max(40, visible_height * (visible_height / content_height))
            scroll_ratio = 0
            if self.max_scroll_position > 0 :
                scroll_ratio = self.scroll_position / self.max_scroll_position
            scrollbar_handle_y = self.header_height + (scroll_ratio * (visible_height - scrollbar_handle_height))
            if scrollbar_handle_y <= y <= scrollbar_handle_y + scrollbar_handle_height:
                return {"on_handle": True}
            elif self.header_height <= y <= self.window_height:
                return {"on_handle": False}
        return None

    def _get_control_at_position(self, x: int, y: int) -> Optional[Dict]:
        """Determine if the position is on a slider or button and return its info."""
        left_panel_width = int(self.window_width * self.split_ratio) - 5
        if x > left_panel_width:
            return None
        adjusted_y_click = y - self.header_height + self.scroll_position
        current_y_content_top = self.panel_padding
        current_group_for_pos_check = None
        for control_def in self.all_sliders:
            if control_def["group_name"] != current_group_for_pos_check:
                current_y_content_top += self.control_height
                current_y_content_top += self.panel_padding
                current_group_for_pos_check = control_def["group_name"]
            control_row_top_y_in_content = current_y_content_top
            control_row_bottom_y_in_content = current_y_content_top + self.control_height
            if control_row_top_y_in_content <= adjusted_y_click < control_row_bottom_y_in_content:
                if control_def["type"] == "color" or control_def["type"] == "global":
                    slider_bar_start_x = self.panel_padding + self.label_width
                    slider_bar_end_x = slider_bar_start_x + self.slider_width
                    if slider_bar_start_x <= x <= slider_bar_end_x:
                        return {
                            "id": control_def["id"],
                            "x": slider_bar_start_x,
                            "y": current_y_content_top,
                            "width": self.slider_width,
                            "height": self.slider_height,
                            "max_value": control_def["max_value"],
                            "definition": control_def
                        }
                elif control_def["type"] == "action_button":
                    button_render_width = self.label_width + self.slider_width
                    button_start_x = self.panel_padding
                    button_end_x = button_start_x + button_render_width
                    if button_start_x <= x <= button_end_x:
                        return {
                            "id": control_def["id"],
                            "x": button_start_x,
                            "y": current_y_content_top,
                            "width": button_render_width,
                            "height": self.control_height,
                            "definition": control_def
                        }
            current_y_content_top += self.control_height
            current_y_content_top += self.panel_padding
        return None

    def get_slider_value(self, slider_id: str) -> int:
        """Get the current value of a slider."""
        if slider_id in self.slider_values:
            return self.slider_values[slider_id]
        if "_" in slider_id:
            parts = slider_id.split("_")
            if len(parts) == 4:
                color_key, range_idx, bound_idx, comp_idx = parts
                with shared_state.data_lock:
                    return shared_state.COLOR_FILTER[color_key][int(range_idx)][int(bound_idx)][int(comp_idx)]
        return 0

    def set_slider_value(self, slider_id: str, value: int) -> None:
        """Set the value of a slider and update shared state, using unified definitions."""
        self.slider_values[slider_id] = value
        slider_def = next((s for s in self.all_sliders if s["id"] == slider_id), None)
        if not slider_def:
            return
        with shared_state.data_lock:
            if slider_def["type"] == "color":
                color_key = slider_def["color_key"]
                range_idx = slider_def["range_idx"]
                bound_idx = slider_def["bound_idx"]
                comp_idx = slider_def["comp_idx"]
                if color_key in shared_state.COLOR_FILTER and \
                   range_idx < len(shared_state.COLOR_FILTER[color_key]) and \
                   bound_idx < len(shared_state.COLOR_FILTER[color_key][range_idx]) and \
                   comp_idx < len(shared_state.COLOR_FILTER[color_key][range_idx][bound_idx]):
                    shared_state.COLOR_FILTER[color_key][range_idx][bound_idx][comp_idx] = value
            elif slider_def["type"] == "global":
                global_key_in_def = slider_def["global_key"]
                shared_state_attr_name = global_key_in_def.upper()
                if hasattr(shared_state, shared_state_attr_name):
                    setattr(shared_state, shared_state_attr_name, value)
        self._update_filtered_sample()

    def _draw_slider(self, display: np.ndarray, x: int, y: int, width: int,
                    label: str, value: int, max_value: int, slider_id: str) -> None:
        """Draw a simple slider control with label and value."""
        cv2.putText(display, label, (x, y + self.control_height//2 + 5),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.text_color, 1)
        slider_x = x + self.label_width
        slider_y = y + (self.control_height - self.slider_height) // 2
        cv2.rectangle(display,
                     (slider_x, slider_y),
                     (slider_x + width, slider_y + self.slider_height),
                     (220, 220, 220), -1)
        fill_width = int((value / max_value) * width)
        if fill_width > 0:
            cv2.rectangle(display,
                         (slider_x, slider_y),
                         (slider_x + fill_width, slider_y + self.slider_height),
                         self.slider_fill_color, -1)
        cv2.rectangle(display,
                     (slider_x, slider_y),
                     (slider_x + width, slider_y + self.slider_height),
                     self.slider_color, 1)
        cv2.putText(display, str(value),
                  (slider_x + width + 10, y + self.control_height//2 + 5),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.text_color, 1)

    def _draw_button(self, display: np.ndarray, x_start_of_row: int, y_start_of_row: int,
                     width: int, height: int, label: str):
        """Draw an action button."""
        button_rect_x1 = x_start_of_row
        button_rect_y1 = y_start_of_row
        button_rect_x2 = x_start_of_row + width
        button_rect_y2 = y_start_of_row + height
        cv2.rectangle(display, (button_rect_x1, button_rect_y1), (button_rect_x2, button_rect_y2), (220, 220, 220), -1)
        cv2.rectangle(display, (button_rect_x1, button_rect_y1), (button_rect_x2, button_rect_y2), self.slider_color, 1)
        text_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        text_x = button_rect_x1 + (width - text_size[0]) // 2
        text_y = button_rect_y1 + (height + text_size[1]) // 2
        cv2.putText(display, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, self.text_color, 1)

    def _draw_scrollbar(self, display: np.ndarray) -> None:
        """Draw a simple scrollbar on the left panel."""
        left_panel_width = int(self.window_width * self.split_ratio) - 5
        content_height = self._get_content_height()
        visible_height = self.window_height - self.header_height
        if content_height > visible_height:
            self.max_scroll_position = content_height - visible_height
            scrollbar_width = 8
            scrollbar_x = left_panel_width - scrollbar_width - 10
            cv2.rectangle(display,
                        (scrollbar_x, self.header_height),
                        (scrollbar_x + scrollbar_width, self.window_height),
                        (220, 220, 220), -1)
            scrollbar_height = max(40, visible_height * (visible_height / content_height))
            scrollbar_y = self.header_height
            if self.max_scroll_position > 0:
                scrollbar_y += (self.scroll_position / self.max_scroll_position) * (visible_height - scrollbar_height)
            handle_color = (100, 100, 100)
            cv2.rectangle(display,
                        (scrollbar_x, int(scrollbar_y)),
                        (scrollbar_x + scrollbar_width, int(scrollbar_y + scrollbar_height)),
                        handle_color, -1)

    def _update_filtered_sample(self) -> None:
        """Apply current color filters to the selected sample image."""
        if not self.sample_images or self.current_sample_index >= len(self.sample_images):
            return
        img = self.sample_images[self.current_sample_index].copy()
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        final_mask = np.zeros((img.shape[0], img.shape[1]), dtype=np.uint8)
        with shared_state.data_lock:
            for color_key, ranges in shared_state.COLOR_FILTER.items():
                color_mask = np.zeros_like(final_mask)
                for lower, upper in ranges:
                    range_mask = cv2.inRange(hsv,
                                          np.array(lower, dtype=np.uint8),
                                          np.array(upper, dtype=np.uint8))
                    color_mask = cv2.bitwise_or(color_mask, range_mask)
                final_mask = cv2.bitwise_or(final_mask, color_mask)
            filtered = cv2.bitwise_and(img, img, mask=final_mask)
            self.sample_filtered_images[self.current_sample_index] = filtered

    def _draw_sample_preview(self, display: np.ndarray) -> None:
        """Draw the sample image preview on the right side of the screen."""
        left_panel_width = int(self.window_width * self.split_ratio)
        right_panel_x = left_panel_width + 5
        right_panel_width = self.window_width - right_panel_x - self.panel_padding
        cv2.putText(display, "Sample Image",
                  (right_panel_x + 10, self.header_height + 30),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.text_color, 1)
        cv2.putText(display, "Filtered Sample Image",
                  (right_panel_x + 10, self.window_height - 150),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.7, self.text_color, 1)
        if self.sample_images and self.current_sample_index < len(self.sample_images):
            orig_img = self.sample_images[self.current_sample_index].copy()
            if self.current_sample_index not in self.sample_filtered_images:
                self._update_filtered_sample()
            filtered_img = self.sample_filtered_images.get(self.current_sample_index, orig_img.copy())
            orig_y = self.header_height + 40
            filtered_y = self.window_height - 140
            available_width = right_panel_width - 20
            aspect_ratio = orig_img.shape[1] / orig_img.shape[0]
            display_height = min(120, int(available_width / aspect_ratio))
            display_width = int(display_height * aspect_ratio)
            orig_display = cv2.resize(orig_img, (display_width, display_height))
            filtered_display = cv2.resize(filtered_img, (display_width, display_height))
            orig_x = right_panel_x + (right_panel_width - display_width) // 2
            filtered_x = orig_x
            display[orig_y:orig_y+display_height, orig_x:orig_x+display_width] = orig_display
            display[filtered_y:filtered_y+display_height, filtered_x:filtered_x+display_width] = filtered_display
            cv2.rectangle(display, (orig_x-1, orig_y-1),
                        (orig_x+display_width+1, orig_y+display_height+1), (0, 0, 0), 1)
            cv2.rectangle(display, (filtered_x-1, filtered_y-1),
                        (filtered_x+display_width+1, filtered_y+display_height+1), (0, 0, 0), 1)

    def update_display(self) -> None:
        """Refresh the window display with current settings, using unified slider definitions."""
        display = np.zeros((self.window_height, self.window_width, 3), dtype=np.uint8)
        display[:] = self.background_color
        cv2.rectangle(display, (0, 0), (self.window_width, self.header_height), (240, 240, 240), -1)
        cv2.line(display, (0, self.header_height), (self.window_width, self.header_height), (200, 200, 200), 1)
        cv2.putText(display, "Color Filter Settings", (20, self.header_height - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 1)
        left_panel_width = int(self.window_width * self.split_ratio)
        cv2.line(display, (left_panel_width, self.header_height), (left_panel_width, self.window_height), self.divider_color, 1)
        current_y_content_top = self.panel_padding
        current_group_drawn = None
        for control_def in self.all_sliders:
            if control_def["group_name"] != current_group_drawn:
                current_group_drawn = control_def["group_name"]
                adjusted_header_top_y_on_screen = current_y_content_top - self.scroll_position + self.header_height
                if adjusted_header_top_y_on_screen < self.window_height and \
                   adjusted_header_top_y_on_screen + self.control_height > self.header_height:
                    cv2.putText(display, control_def["group_name"],
                             (self.panel_padding, adjusted_header_top_y_on_screen + 20),
                             cv2.FONT_HERSHEY_SIMPLEX, 0.7, control_def["group_color"], 2)
                current_y_content_top += self.control_height
                current_y_content_top += self.panel_padding
            adjusted_control_row_top_y_on_screen = current_y_content_top - self.scroll_position + self.header_height
            if adjusted_control_row_top_y_on_screen < self.window_height and \
               adjusted_control_row_top_y_on_screen + self.control_height > self.header_height:
                if control_def["type"] == "color" or control_def["type"] == "global":
                    self._draw_slider(
                        display,
                        self.panel_padding,
                        adjusted_control_row_top_y_on_screen,
                        self.slider_width,
                        control_def["label"],
                        self.slider_values.get(control_def["id"], 0),
                        control_def["max_value"],
                        control_def["id"]
                    )
                elif control_def["type"] == "action_button":
                    button_render_width = self.label_width + self.slider_width
                    self._draw_button(
                        display,
                        self.panel_padding,
                        adjusted_control_row_top_y_on_screen,
                        button_render_width,
                        self.control_height,
                        control_def["label"]
                    )
            current_y_content_top += self.control_height
            current_y_content_top += self.panel_padding
        self._draw_scrollbar(display)
        self._draw_sample_preview(display)
        cv2.imshow(self.window_name, display)

    def save_settings(self):
        """Save current color filter and global settings to a JSON file."""
        if not self.tk_root:
            self._initialize_tk()
            if not self.tk_root: return
        filepath = filedialog.asksaveasfilename(
            master=self.tk_root,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Farbeinstellungen Speichern"
        )
        if not filepath:
            return
        settings_to_save = {
            "color_filter": {},
            "global_settings": {}
        }
        with shared_state.data_lock:
            for color_key, ranges_data in shared_state.COLOR_FILTER.items():
                settings_to_save["color_filter"][color_key] = []
                for lower_np, upper_np in ranges_data:
                    settings_to_save["color_filter"][color_key].append(
                        (lower_np.tolist(), upper_np.tolist())
                    )
            settings_to_save["global_settings"]["s_desaturated_threshold"] = shared_state.S_DESATURATED_THRESHOLD
            settings_to_save["global_settings"]["s_white_max"] = shared_state.S_WHITE_MAX
            settings_to_save["global_settings"]["v_white_min"] = shared_state.V_WHITE_MIN
        try:
            with open(filepath, 'w') as f:
                json.dump(settings_to_save, f, indent=4, default=_numpy_to_list_converter)
        except Exception as e:
            pass

    def load_settings(self):
        """Load color filter and global settings from a JSON file."""
        if not self.tk_root:
            self._initialize_tk()
            if not self.tk_root: return
        filepath = filedialog.askopenfilename(
            master=self.tk_root,
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Farbeinstellungen Laden"
        )
        if not filepath:
            return
        try:
            with open(filepath, 'r') as f:
                loaded_settings = json.load(f)
        except Exception as e:
            return
        with shared_state.data_lock:
            loaded_color_filter = loaded_settings.get("color_filter", {})
            for color_key, ranges_data_list in loaded_color_filter.items():
                if color_key in shared_state.COLOR_FILTER:
                    new_ranges_for_color = []
                    for lower_list, upper_list in ranges_data_list:
                        try:
                            low_np = np.array(lower_list, dtype=np.uint8)
                            high_np = np.array(upper_list, dtype=np.uint8)
                            if low_np.shape == (3,) and high_np.shape == (3,):
                                new_ranges_for_color.append((low_np, high_np))
                        except ValueError as ve:
                            pass
                    shared_state.COLOR_FILTER[color_key] = new_ranges_for_color
            loaded_global_settings = loaded_settings.get("global_settings", {})
            if "s_desaturated_threshold" in loaded_global_settings:
                shared_state.S_DESATURATED_THRESHOLD = int(loaded_global_settings["s_desaturated_threshold"])
            if "s_white_max" in loaded_global_settings:
                shared_state.S_WHITE_MAX = int(loaded_global_settings["s_white_max"])
            if "v_white_min" in loaded_global_settings:
                shared_state.V_WHITE_MIN = int(loaded_global_settings["v_white_min"])
        self.initialize_slider_values()
        self._update_filtered_sample()
        self.update_display()

    def hide(self) -> None:
        """Hide the color settings window."""
        try:
            cv2.destroyWindow(self.window_name)
        except cv2.error:
            pass