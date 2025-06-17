from ctypes import windll, c_int, byref, sizeof
from ctypes.wintypes import HWND, DWORD

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QLayout, QLayoutItem, QWidget, QVBoxLayout, QHBoxLayout, QApplication, QMainWindow, QLineEdit, QPushButton
from qt_material import apply_stylesheet

from utils.config import read_config


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


def get_focusable_widgets(layout: QWidget | QLayout | QVBoxLayout | QHBoxLayout) -> list[QWidget]:
    """
    Returns a list of focusable widgets in the given widget.

    Args:
        widget (QWidget): The widget to search for focusable widgets.

    Returns:
        list[QWidget]: A list of focusable widgets.
    """
    focusable_widgets = []
    if layout is not None:
        for item in layout.children():
            if isinstance(item, (QLineEdit, QPushButton)) and item.isVisible():
                focusable_widgets.append(item)
            elif isinstance(item, (QWidget, QLayout, QVBoxLayout, QHBoxLayout)):
                focusable_widgets.extend(get_focusable_widgets(item))
            else:
                print(f"Skipping item of type {type(item)} in layout.")
    return focusable_widgets


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