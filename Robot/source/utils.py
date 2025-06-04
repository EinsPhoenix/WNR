from ctypes import windll, c_int, byref, sizeof
from ctypes.wintypes import HWND, DWORD
from json import dumps, loads
from socket import socket, AF_INET, SOCK_STREAM

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLayout, QLayoutItem, QWidget, QVBoxLayout, QHBoxLayout, QApplication, QMainWindow


def send_message(self, message_to_send: str) -> None:
    """
    Send a command to the rasberry pi, which controls the camera.

    Args:
        self: The main window object.
        message_to_send (str): The message to send.
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
    windll.dwmapi.DwmSetWindowAttribute(HWND(hwnd), DWORD(DWMWA_USE_IMMERSIVE_DARK_MODE), byref(c_int(True)), sizeof(c_int))
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


def set_robot_speed(self, speed: str) -> None:
    """
    Sets the robot speed.

    Args:
        self: The main window object.
        speed (str): The speed to set.
    """
    try:
        speed_value: int = int(speed)
    except ValueError:
        self.show_warning("Invalid speed value. Please enter a valid integer.")
    else:
        self.sorter.set_speed(speed_value)
        self.post_main_widget()