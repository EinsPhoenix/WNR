from ctypes import windll, c_int, byref, sizeof
from ctypes.wintypes import HWND, DWORD
from json import dumps, loads, load
from socket import socket, AF_INET, SOCK_STREAM
from time import sleep

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLayout, QLayoutItem, QWidget, QVBoxLayout, QHBoxLayout, QApplication, QMainWindow
from qt_material import apply_stylesheet


def send_message(self, message_to_send: dict) -> str | None:
    """
    Send a command to the rasberry pi, which controls the camera.

    Args:
        self: The main window object.
        message_to_send (dict): The message to send.

    Returns:
        str | None: The response from the server, or None if an error occurred.
    """
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect((self.host, self.port))
            s.sendall(dumps(message_to_send).encode("utf-8"))
            response_data = s.recv(1024)
            response = loads(response_data.decode("utf-8"))
            print(f"Received response: {response}")
            return response
    except ConnectionRefusedError:
        print("Connection refused. Please check if the server is running.")
    except Exception as e:
        print(f"An error occurred: {e}")


def set_title_bar_color(window: QMainWindow) -> None:
    """
    Sets the title bar color of the window to black.

    Args:
        window (QMainWindow): The window to change the title bar color of.
    """
    hwnd: int = window.winId().__int__()
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    windll.dwmapi.DwmSetWindowAttribute(HWND(hwnd), DWORD(DWMWA_USE_IMMERSIVE_DARK_MODE), byref(c_int(read_config(window)["ui"]["dark_mode"])), sizeof(c_int))
    window.hide()
    window.show()


def delete_layout_items(self, layout: QLayout | QVBoxLayout | QHBoxLayout) -> None:
    """
    Deletes all items in the given layout.

    Args:
        self: The main window object.
        layout (QLayout | QVBoxLayout | QHBoxLayout): The layout to delete the items from.
    """
    if layout is not None:
        while layout.count():
            item: QLayoutItem | None = layout.takeAt(0)
            if item is not None:
                widget: QWidget | None = item.widget()
                if widget is not None:
                    widget.setParent(None)
                else:
                    currentLayout: QLayout | None = item.layout()
                    if currentLayout is not None:
                        delete_layout_items(self, currentLayout)


def resize_window(self, add_width: int = 0, add_height: int = 0) -> None:
    """
    Resizes the window to fit the content.

    Args:
        self: The main window object.
        add_width (int, optional): The width to add to the window size.
        add_height (int, optional): The height to add to the window size.
    """
    self.setMinimumSize(0, 0)
    self.setMaximumSize(16777215, 16777215)
    QTimer.singleShot(0, lambda: check_min_size(self, add_width, add_height))
    QApplication.processEvents()
    frame_geometry = self.frameGeometry()
    frame_geometry.moveCenter(self.screen().geometry().center())
    self.move(frame_geometry.topLeft())


def check_min_size(self, add_width: int, add_height: int) -> None:
    """
    Checks if the window is smaller than the minimum width and sets it to the minimum width if it is.

    Args:
        self: The main window object.
        add_width (int): The width to add to the window size.
        add_height (int): The height to add to the window size.
    """
    self.adjustSize()
    if self.size().width() < self.min_width:
        self.setFixedSize(self.min_width + add_width, self.size().height() + add_height)
    else:
        self.setFixedSize(self.size().width() + add_width, self.size().height() + add_height)


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
        self.show_warning("Robot is busy. Please wait until the current operation is finished or cancel it.")
        return
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
        while send_message(self, {"type": "calibrate", "payload": {"number": self.current_calibration_step, "robot_pos": {"x": pos[0], "y": pos[1]}}}["status"]) == "error":
            sleep(0.5)
        self.current_calibration_step += 1
        if self.current_calibration_step == len(self.calibrate_positions):
            send_message(self, {"type": "calibrate", "payload": {"finish": True}})
            self.calibrate_label.setText("Calibration finished. You can now start sorting.")
            self.calibrate_button.setText("Calibration")
        else:
            pos = self.calibrate_positions[self.current_calibration_step]
            # self.sorter.move_to_position(*pos, z)
            self.calibrate_label.setText(f"Calibrating position {self.current_calibration_step + 1} at ({pos[0]}, {pos[1]}, {z}).\nConfirm to continue if QR-Cube is in position.")
    self.robot_busy = False


def remove_warning(self) -> None:
    """
    Remove the warning text if it exists.

    Args:
        self: The main window object.
    """
    if self.warned:
        self.warned = False
        if hasattr(self, "warning_text"):
            self.warning_text.setParent(None)
            del self.warning_text


def read_config(self) -> dict:
    """
    Reads the configuration file and returns the configuration as a dictionary.

    Args:
        self: The main window object.

    Returns:
        dict: The configuration dictionary.
    """
    with open(self.config_path, "r") as config_file:
        config = load(config_file)
    return config


def save_config(self, dark_mode: bool = None, com_port: str = None, speed: int = None) -> None:
    """
    Toggle the dark mode style sheet for the main window.

    Args:
        self: The main window object.
        dark_mode (bool, optional): If True, enable dark mode. If False, disable dark mode. Defaults to None.
        com_port (str, optional): The COM port to set for the robot. Defaults to None.
        speed (int, optional): The speed to set for the robot. Defaults to None.
    """
    with open(self.config_path, "r") as config_file:
        config = load(config_file)
    if dark_mode is not None:
        config["ui"]["dark_mode"] = dark_mode
    if com_port is not None:
        config["robot"]["com_port"] = com_port
    if speed is not None:
        if speed > 2000:
            speed = 2000
        elif speed < 100:
            speed = 100
        config["robot"]["speed"] = speed
    with open(self.config_path, "w") as config_file:
        config_file.write(dumps(config, indent=4))
    set_style_sheet(self)


def set_settings(self) -> None:
    """
    Sets the settings for the main window.

    Args:
        self: The main window object.
    """
    self.com_port_input.setText(read_config(self)["robot"]["com_port"])
    self.speed_input.setText(str(read_config(self)["robot"]["speed"]))


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


def set_style_sheet(self) -> None:
    """
    Sets the style sheet for the main window.

    Args:
        self: The main window object.
    """
    self.setStyleSheet("")
    if read_config(self)["ui"]["dark_mode"]:
        apply_stylesheet(self.app, theme="WNR_dark.xml", invert_secondary=False, extra={"pyside6": True})
        self.setStyleSheet("""
            QGroupBox::title {
                border-radius: 5px;
                color: #ffffff;
            }
            QPushButton {
                border: 2px solid #949CA3;
                border-radius: 5px;
                color: #ffffff;
            }
            QPushButton:hover {
                border-color: #A2445E;
            }
            QPushButton:focus {
                background-color: #31363b;
                border-color: #A2445E;
            }
            QLineEdit {
                border: 2px solid #949CA3;
                border-radius: 5px;
                color: #ffffff;
                min-width: 200px;
                min-height: 30px;
                max-height: 30px;
            }
            QLineEdit:hover {
                border-color: #A2445E;
            }
            QLineEdit:focus {
                border-color: #A2445E;
            }
            QCheckBox {
                border: 2px solid #949CA3;
                border-radius: 5px;
                padding: 0px 8px;
            }
            QCheckBox::focus {
                border: 2px solid #A2445E;
                border-radius: 5px;
                padding: 0px 8px;
            }
            QCheckBox::indicator {
                background-color: none;
            }
            QCheckBox::indicator:focus {
                background-color: none;
            }
            QMenu {
                background-color: #31363b;
            }
            QMenu::item:selected {
                background-color: none;
                border: 2px solid #A2445E;
                border-radius: 5px;
                color: #ffffff;
            }
        """)
        set_title_bar_color(self)
    else:
        apply_stylesheet(self.app, theme="WNR_light.xml", invert_secondary=True, extra={"pyside6": True})
        # self.setStyleSheet("""
        #     QGroupBox::title {
        #         border-radius: 5px;
        #         color: #000000;
        #     }
        #     QPushButton {
        #         border: 2px solid #949CA3;
        #         border-radius: 5px;
        #         color: #000000;
        #     }
        #     QPushButton:hover {
        #         border-color: #A2445E;
        #     }
        #     QPushButton:focus {
        #         background-color: #31363b;
        #         border-color: #A2445E;
        #     }
        #     QLineEdit {
        #         border: 2px solid #949CA3;
        #         border-radius: 5px;
        #         color: #000000;
        #         min-width: 200px;
        #         min-height: 30px;
        #         max-height: 30px;
        #     }
        #     QLineEdit:hover {
        #         border-color: #A2445E;
        #     }
        #     QLineEdit:focus {
        #         border-color: #A2445E;
        #     }
        #     QCheckBox {
        #         border: 2px solid #949CA3;
        #         border-radius: 5px;
        #         padding: 0px 8px;
        #     }
        #     QCheckBox::focus {
        #         border: 2px solid #A2445E;
        #         border-radius: 5px;
        #         padding: 0px 8px;
        #     }
        #     QCheckBox::indicator {
        #         background-color: none;
        #     }
        #     QCheckBox::indicator:focus {
        #         background-color: none;
        #     }
        #     QMenu {
        #         background-color: #31363b;
        #     }
        #     QMenu::item:selected {
        #         background-color: none;
        #         border: 2px solid #A2445E;
        #         border-radius: 5px;
        #         color: #000000;
        #     }
        # """)
        set_title_bar_color(self)