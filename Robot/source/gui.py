from math import sqrt

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QSizePolicy, QWidget

from sorting import start_sorting_worker, cancel_sorting
from utils import cancel_calibration, confirm_calibration_step, set_robot_speed


def reset_slogan(self) -> None:
    self.slogan_label = QLabel()
    self.slogan_label.setPixmap(QPixmap(r".\icons\wnr_slogan.png").scaled(400, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    self.slogan_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.slogan_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
    self.all_wrapper.addWidget(self.slogan_label)


class SidebarButton(QPushButton):
    def __init__(self, text: str) -> None:
        """
        Initialize a sidebar button with the given text.

        Args:
            text (str): The text to display on the button.
        """
        super().__init__(text)
        self.setCheckable(True)
        self.setMinimumHeight(50)
        
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 15px 20px;
                border: none;
                background-color: transparent;
                color: #ffffff;
                font-size: 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: rgba(254, 176, 189, 0.5);
            }
            QPushButton:focus {
                background-color: rgba(254, 176, 189, 0.5);
            }
            QPushButton:checked {
                background-color: rgba(254, 176, 189, 0.5);
                border-left: 4px solid #99354F;
            }
        """)


class CustomSidebar(QWidget):
    tabChanged = Signal(int)
    
    def __init__(self, tabs: list = []) -> None:
        """
        Initialize the sidebar with a list of tabs.

        Args:
            tabs (list, optional): A list of tab names to display in the sidebar. Defaults to an empty list.
        """
        super().__init__()
        self.tabs = tabs
        self.buttons = []
        self.setup_ui()
        
    def setup_ui(self) -> None:
        """Set up the user interface for the sidebar."""
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)
        
        for i, tab in enumerate(self.tabs):
            button = SidebarButton(tab)
            button.clicked.connect(lambda checked, idx=i: self.select_tab(idx))
            self.buttons.append(button)
            layout.addWidget(button)
        
        layout.addStretch()

        self.buttons[0].setChecked(True)
    
    def select_tab(self, index: int) -> None:
        """
        Select a tab by index and emit the tabChanged signal.

        Args:
            index (int): The index of the tab to select.
        """
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)
        self.tabChanged.emit(index)


def post_calibrate_camera(self) -> QWidget:
    """
    Calibrate the camera by moving the robot to specific position.

    Args:
        self: The main window object.

    Returns:
        QWidget: The widget containing the calibration interface.
    """
    page = QWidget()
    layout = QVBoxLayout(page)

    mid_value: float = sqrt(45000)
    self.calibrate_positions = [(0, -300), (mid_value, -mid_value), (300, 0), (mid_value, mid_value), (0, 300)]
    self.current_calibration_step = 0

    self.calibrate_label = QLabel("Start calibration process by pressing the \"Calibration\" button.")
    layout.addWidget(self.calibrate_label)

    button_layout = QHBoxLayout()
    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(lambda: cancel_calibration(self))
    self.calibrate_button = QPushButton("Calibration")
    self.calibrate_button.clicked.connect(lambda: confirm_calibration_step(self))
    button_layout.addWidget(cancel_button)
    button_layout.addWidget(self.calibrate_button)

    layout.addLayout(button_layout)
    self.calibrate_button.setFocus()
    return page


def post_start_sorting(self) -> QWidget:
    """
    Post the start sorting widget to the main window.

    Args:
        self: The main window object.

    Returns:
        QWidget: The widget containing the start sorting interface.
    """
    page = QWidget()
    layout = QVBoxLayout(page)

    sorting_label = QLabel("Start sorting process by pressing the \"Start\" button.")
    layout.addWidget(sorting_label)

    button_layout = QHBoxLayout()
    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(lambda: cancel_sorting(self))
    start_sorting_button = QPushButton("Start")
    # start_sorting_button.clicked.connect(lambda: self.sorter.start_sorting())
    start_sorting_button.clicked.connect(lambda: start_sorting_worker(self))
    button_layout.addWidget(cancel_button)
    button_layout.addWidget(start_sorting_button)

    layout.addLayout(button_layout)
    start_sorting_button.setFocus()
    return page


def post_change_speed(self) -> QWidget:
    """
    Post the change speed widget to the main window.

    Args:
        self: The main window object.

    Returns:
        QWidget: The widget containing the change speed interface.
    """
    page = QWidget()
    layout = QVBoxLayout(page)

    speed_label = QLabel("Enter new speed:")
    speed_input = QLineEdit()
    layout.addWidget(speed_label)
    layout.addWidget(speed_input)

    button_layout = QHBoxLayout()
    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(self.post_main_widget)
    change_speed_button = QPushButton("Change speed")
    change_speed_button.clicked.connect(lambda: set_robot_speed(self, speed_input.text()))
    button_layout.addWidget(cancel_button)
    button_layout.addWidget(change_speed_button)

    layout.addLayout(button_layout)
    speed_input.setFocus()
    return page


def post_manual_controls(self) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    return page


def post_storage_display(self) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)
    return page