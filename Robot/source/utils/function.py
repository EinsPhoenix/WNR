import asyncio
from time import sleep

from utils.communication import send_message
from utils.config import read_config, save_config
from utils.gui import remove_warning, set_style_sheet


def cancel_calibration(self) -> None:
    """
    Cancel the calibration process and reset the state.

    Args:
        self: The main window object.
    """
    if self.calibrate_button.text() == "Confirm":
        send_message(self, {"type": "calibrate", "payload": {"finish": True}})
        self.calibrate_label.setText("Calibration cancelled. You can start again.")
        self.calibrate_button.setText("Calibration")
        self.current_calibration_step = 0
        self.robot_busy = False
    else:
        remove_warning(self)


def confirm_calibration_step(self) -> None:
    """
    Confirm the calibration step by moving the robot to specific positions.

    Args:
        self: The main window object.
    """
    if self.robot_busy:
        #FIXME:
        # self.show_warning("Robot is busy. Please wait until the current operation is finished or cancel it.")
        # return
        pass
    else:
        self.robot_busy = True
        self.sorter.set_speed(read_config(self)["robot"]["speed"])
    pos = self.calibrate_positions[self.current_calibration_step]
    z: int = 15
    if self.calibrate_button.text() == "Calibration":
        self.sorter.move_to_position(*pos, z)
        self.calibrate_label.setText(f"Calibrating position {self.current_calibration_step + 1} at ({pos[0]}, {pos[1]}, {z}).\nConfirm to continue if QR-Cube is in position.")
        self.calibrate_button.setText("Confirm")
    else:
        if pos != (300, 0):
            self.sorter.move_to_position(300, 0, z)
        else:
            self.sorter.move_to_position(0, 300, z)
        sleep(0.5)
        while send_message(self, {"type": "calibrate", "payload": {"number": self.current_calibration_step, "robot_pos": {"x": pos[0], "y": pos[1]}}})["status"] == "error":
            sleep(0.5)
        self.current_calibration_step += 1
        if self.current_calibration_step == len(self.calibrate_positions):
            send_message(self, {"type": "calibrate", "payload": {"finish": True}})
            self.calibrate_label.setText("Calibration finished. You can now start sorting.")
            self.calibrate_button.setText("Calibration")
        else:
            pos = self.calibrate_positions[self.current_calibration_step]
            self.sorter.move_to_position(*pos, z)
            self.calibrate_label.setText(f"Calibrating position {self.current_calibration_step + 1} at ({pos[0]}, {pos[1]}, {z}).\nConfirm to continue if QR-Cube is in position.")
    self.robot_busy = False


def confirm_fast_calibration_step(self, x, y) -> None:
    """
    Confirm the fast calibration step by moving the robot to specific positions.

    Args:
        self: The main window object.
    """
    if not hasattr(self, "calibrating") or self.calibrating is False:
        self.calibrating = True
        self.calibration_step = 0
    while send_message(self, {"type": "calibrate", "payload": {"number": self.calibration_step, "robot_pos": {"x": x, "y": y}}})["status"] == "error":
        sleep(0.5)
    self.calibration_step += 1
    if self.calibration_step == 5:
        send_message(self, {"type": "calibrate", "payload": {"finish": True}})
        self.calibrate_label.setText("Fast calibration finished. You can now start sorting.")
        self.calibrating = False
        


def set_settings(self) -> None:
    """
    Sets the settings for the main window.

    Args:
        self: The main window object.
    """
    config = read_config(self)
    self.com_port_input.setText(config["robot"]["com_port"])
    self.speed_input.setText(str(config["robot"]["speed"]))
    self.tcp_host_input.setText(config["tcp"]["host"])
    self.tcp_port_input.setText(str(config["tcp"]["port"]))
    self.stream_host_input.setText(config["stream"]["host"])
    self.stream_port_input.setText(str(config["stream"]["port"]))
    self.db_host_input.setText(config["db"]["host"])
    self.db_port_input.setText(str(config["db"]["port"]))


def update_storage_display(self) -> None:
    """
    Updates the storage display with the current counts and colors.

    Args:
        self: The main window object.
    """
    for idx, (color_name, color_hex) in enumerate(self.colors):
        self.storage_labels[idx].setText(f"{color_name}\n{self.storage_counts[idx]}/5")
        for i in range(5):
            if (4 - i) < self.storage_counts[idx]:
                self.storage_blocks[idx][i].setStyleSheet(f"""
                    background-color: {color_hex};
                    border: 1px solid #333;
                    border-radius: 3px;
                """)
            else:
                self.storage_blocks[idx][i].setStyleSheet(f"""
                    background-color: transparent;
                    border: 1px solid #666;
                    border-radius: 3px;
                """)


def increase_storage(self, color_idx: int) -> None:
    """
    Increases the storage count for a specific color.

    Args:
        self: The main window object.
        color_idx (int): The index of the color to increase the storage count for.
    """
    if self.storage_counts[color_idx] < 5:
        self.storage_counts[color_idx] += 1
        update_storage_display(self)


def decrease_storage(self, color_idx: int) -> None:
    """
    Decreases the storage count for a specific color.

    Args:
        self: The main window object.
        color_idx (int): The index of the color to decrease the storage count for.
    """
    if self.storage_counts[color_idx] > 0:
        self.storage_counts[color_idx] -= 1
        update_storage_display(self)


def toggle_dark_mode(self, dark_mode: bool) -> None:
    """
    Toggles the dark mode style sheet for the main window.

    Args:
        self: The main window object.
        dark_mode (bool): If True, enable dark mode. If False, disable dark mode.
    """
    save_config(self, dark_mode = dark_mode)
    set_style_sheet(self)