from asyncio import create_task
from math import sqrt

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSizePolicy, QWidget, QGridLayout, QApplication, QGroupBox

from sorting import start_sorting_worker, cancel_sorting
from utils.config import read_config, save_config
from utils.custom_elements import CustomToggle
from utils.function import cancel_calibration, confirm_calibration_step, update_storage_display, increase_storage, decrease_storage, toggle_dark_mode, set_settings, confirm_fast_calibration_step, send_to_db_test


def reset_slogan(self) -> None:
    slogan_wrapper = QHBoxLayout()
    slogan_wrapper.setAlignment(Qt.AlignmentFlag.AlignCenter)
    slogan_label = QLabel()
    slogan_label.setPixmap(QPixmap(r".\icons\wnr_slogan.png").scaled(400, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    slogan_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    slogan_label.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
    slogan_wrapper.addWidget(slogan_label)
    self.all_wrapper.addLayout(slogan_wrapper)


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

    self.sorting_label = QLabel("Start sorting process by pressing the \"Start\" button.")
    layout.addWidget(self.sorting_label)

    button_layout = QHBoxLayout()
    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(lambda: cancel_sorting(self))
    self.start_sorting_button = QPushButton("Start")
    self.start_sorting_button.clicked.connect(lambda: start_sorting_worker(self))
    button_layout.addWidget(cancel_button)
    button_layout.addWidget(self.start_sorting_button)

    layout.addLayout(button_layout)
    self.start_sorting_button.setFocus()
    return page


def post_storage_display(self) -> QWidget:
    """
    Post the storage display widget to the main window.

    Args:
        self: The main window object.

    Returns:
        QWidget: The widget containing the storage display interface.
    """
    page = QWidget()
    layout = QVBoxLayout(page)

    bars_container = QHBoxLayout()
    bars_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
    bars_container.setSpacing(30)

    self.colors = [
        ("Yellow", "#FFFF44"),
        ("Red", "#FF4444"),
        ("Blue", "#4444FF"),
        ("Green", "#44FF44")
    ]

    self.storage_labels = []
    self.storage_blocks = []

    for idx, (color_name, color_hex) in enumerate(self.colors):
        bar_container = QVBoxLayout()
        bar_container.setAlignment(Qt.AlignmentFlag.AlignCenter)

        color_label = QLabel(f"{color_name}\n{self.storage_counts[idx]}/5")
        color_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        color_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        bar_container.addWidget(color_label)
        self.storage_labels.append(color_label)

        blocks_layout = QVBoxLayout()
        blocks_layout.setSpacing(2)
        blocks_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        blocks_for_color = []
        for i in range(5):
            block = QLabel()
            block.setFixedSize(40, 40)
            blocks_layout.addWidget(block)
            blocks_for_color.append(block)

        self.storage_blocks.append(blocks_for_color)
        bar_container.addLayout(blocks_layout)

        button_layout = QVBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        button_layout.setSpacing(5)

        plus_button = QPushButton("+")
        plus_button.setFixedSize(40, 40)
        plus_button.clicked.connect(lambda checked, i=idx: increase_storage(self, i))

        minus_button = QPushButton("-")
        minus_button.setFixedSize(40, 40)
        minus_button.clicked.connect(lambda checked, i=idx: decrease_storage(self, i))

        button_layout.addWidget(plus_button)
        button_layout.addWidget(minus_button)
        bar_container.addLayout(button_layout)

        bar_widget = QWidget()
        bar_widget.setLayout(bar_container)
        bars_container.addWidget(bar_widget)

    layout.addLayout(bars_container)
    layout.addStretch()
    update_storage_display(self)
    return page


def post_camera_display(self) -> QWidget:
    """
    Post the camera widget to the main window.

    Args:
        self: The main window object.

    Returns:
        QWidget: The widget containing the camera interface.
    """
    page = QWidget()
    layout = QVBoxLayout(page)
    # FIXME:
    screen = QApplication.primaryScreen().geometry()
    max_width = int(screen.width() * 0.7)
    max_height = int(screen.height() * 0.7)
    self.camera_display.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.camera_display.setMinimumSize(max_width, max_height)
    layout.addWidget(self.camera_display)
    return page


def post_color_analysis(self) -> QWidget:
    """
    Post the color analysis widget to the main window.

    Args:
        self: The main window object.

    Returns:
        QWidget: The widget containing the color analysis interface.
    """
    page = QWidget()
    layout = QVBoxLayout(page)
    # FIXME:
    screen = QApplication.primaryScreen().geometry()
    max_width = int(screen.width() * 0.7)
    max_height = int(screen.height() * 0.7)
    self.color_analysis.setAlignment(Qt.AlignmentFlag.AlignCenter)
    self.color_analysis.setMinimumSize(max_width, max_height)
    layout.addWidget(self.color_analysis)
    return page


def post_color_settings(self) -> QWidget:
    """
    Post the color settings widget to the main window.

    Args:
        self: The main window object.

    Returns:
        QWidget: The widget containing the color settings interface.
    """
    page = QWidget()
    layout = QVBoxLayout(page)

    return page


def post_manual_controls(self) -> QWidget:
    """
    Post the manual controls widget to the main window.

    Args:
        self: The main window object.

    Returns:
        QWidget: The widget containing the manual controls interface.
    """
    page = QWidget()
    layout = QVBoxLayout(page)
    return page


def post_settings(self) -> QWidget:
    """
    Post the settings widget to the main window.

    Args:
        self: The main window object.

    Returns:
        QWidget: The widget containing the settings interface.
    """
    page = QWidget()
    layout = QVBoxLayout(page)

    toggle_wrapper = QHBoxLayout()
    left_toggle_layout = QGridLayout()
    right_toggle_layout = QGridLayout()
    left_toggle_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    right_toggle_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    dark_mode_label = QLabel("Dark Mode")
    dark_mode_toggle = CustomToggle()
    dark_mode_toggle.set_checked(read_config(self)["ui"]["dark_mode"])
    dark_mode_toggle.toggled.connect(lambda: toggle_dark_mode(self, dark_mode=dark_mode_toggle.is_checked()))
    left_toggle_layout.addWidget(dark_mode_label, 0, 0)
    left_toggle_layout.addWidget(dark_mode_toggle, 0, 1)

    dobot_connection_label = QLabel("DoBot Connection")
    self.dobot_connection_toggle = CustomToggle(True, self.sorter.dobot_connect, self.sorter.dobot_disconnect)
    self.dobot_connection_toggle._checked = False
    self.dobot_connection_toggle.toggle()
    right_toggle_layout.addWidget(dobot_connection_label, 0, 0)
    right_toggle_layout.addWidget(self.dobot_connection_toggle, 0, 1)

    db_connection_label = QLabel("Database Connection")
    self.db_connection_toggle = CustomToggle(True, self.db.connect, self.db.disconnect)
    self.db_connection_toggle._checked = False
    self.db_connection_toggle.toggle()
    left_toggle_layout.addWidget(db_connection_label, 1, 0)
    left_toggle_layout.addWidget(self.db_connection_toggle, 1, 1)

    raspi_connection_label = QLabel("Raspi Connection")
    self.raspi_connection_toggle = CustomToggle(True, self.stream.start_stream, self.stream.stop_stream)
    self.raspi_connection_toggle._checked = False
    self.raspi_connection_toggle.toggle()
    right_toggle_layout.addWidget(raspi_connection_label, 1, 0)
    right_toggle_layout.addWidget(self.raspi_connection_toggle, 1, 1)

    toggle_wrapper.addLayout(left_toggle_layout)
    toggle_wrapper.addLayout(right_toggle_layout)
    layout.addLayout(toggle_wrapper)

    input_wrapper = QHBoxLayout()
    left_input_layout = QGridLayout()
    right_input_layout = QGridLayout()
    left_input_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    right_input_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

    x_offset_label = QLabel("X Offset")
    self.x_offset_input = QLineEdit()
    left_input_layout.addWidget(x_offset_label, 0, 0)
    left_input_layout.addWidget(self.x_offset_input, 0, 1)

    x_offset_factor_label = QLabel("X Offset Factor")
    self.x_offset_factor_input = QLineEdit()
    left_input_layout.addWidget(x_offset_factor_label, 1, 0)
    left_input_layout.addWidget(self.x_offset_factor_input, 1, 1)

    com_port_label = QLabel("COM Port")
    self.com_port_input = QLineEdit()
    left_input_layout.addWidget(com_port_label, 2, 0)
    left_input_layout.addWidget(self.com_port_input, 2, 1)

    speed_label = QLabel("Speed")
    self.speed_input = QLineEdit()
    left_input_layout.addWidget(speed_label, 3, 0)
    left_input_layout.addWidget(self.speed_input, 3, 1)

    stream_host_label = QLabel("Stream Host")
    self.stream_host_input = QLineEdit()
    left_input_layout.addWidget(stream_host_label, 4, 0)
    left_input_layout.addWidget(self.stream_host_input, 4, 1)

    stream_port_label = QLabel("Stream Port")
    self.stream_port_input = QLineEdit()
    left_input_layout.addWidget(stream_port_label, 5, 0)
    left_input_layout.addWidget(self.stream_port_input, 5, 1)

    y_offset_label = QLabel("Y Offset")
    self.y_offset_input = QLineEdit()
    right_input_layout.addWidget(y_offset_label, 0, 0)
    right_input_layout.addWidget(self.y_offset_input, 0, 1)

    y_offset_factor_label = QLabel("Y Offset Factor")
    self.y_offset_factor_input = QLineEdit()
    right_input_layout.addWidget(y_offset_factor_label, 1, 0)
    right_input_layout.addWidget(self.y_offset_factor_input, 1, 1)

    tcp_host_label = QLabel("TCP Host")
    self.tcp_host_input = QLineEdit()
    right_input_layout.addWidget(tcp_host_label, 2, 0)
    right_input_layout.addWidget(self.tcp_host_input, 2, 1)

    tcp_port_label = QLabel("TCP Port")
    self.tcp_port_input = QLineEdit()
    right_input_layout.addWidget(tcp_port_label, 3, 0)
    right_input_layout.addWidget(self.tcp_port_input, 3, 1)

    db_host_label = QLabel("Database Host")
    self.db_host_input = QLineEdit()
    right_input_layout.addWidget(db_host_label, 4, 0)
    right_input_layout.addWidget(self.db_host_input, 4, 1)

    db_port_label = QLabel("Database Port")
    self.db_port_input = QLineEdit()
    right_input_layout.addWidget(db_port_label, 5, 0)
    right_input_layout.addWidget(self.db_port_input, 5, 1)

    left_input_layout.setColumnMinimumWidth(1, 150)
    left_input_layout.setColumnStretch(1, 1)
    right_input_layout.setColumnMinimumWidth(1, 150)
    right_input_layout.setColumnStretch(1, 1)

    input_wrapper.addLayout(left_input_layout)
    input_wrapper.addLayout(right_input_layout)
    layout.addLayout(input_wrapper)

    set_settings(self)

    button_wrapper = QHBoxLayout()
    button_wrapper.setAlignment(Qt.AlignmentFlag.AlignBottom)
    cancel_button = QPushButton("Cancel")
    cancel_button.clicked.connect(lambda: set_settings(self))
    save_button = QPushButton("Save")
    save_button.clicked.connect(lambda: save_config(
        self,
        x_offset = float(self.x_offset_input.text()),
        x_offset_factor = float(self.x_offset_factor_input.text()),
        com_port = self.com_port_input.text(),
        speed = int(self.speed_input.text()),
        stream_host = self.stream_host_input.text(),
        stream_port = int(self.stream_port_input.text()),
        y_offset = float(self.y_offset_input.text()),
        y_offset_factor = float(self.y_offset_factor_input.text()),
        tcp_host = self.tcp_host_input.text(),
        tcp_port = int(self.tcp_port_input.text()),
        db_host = self.db_host_input.text(),
        db_port = int(self.db_port_input.text())
    ))
    button_wrapper.addWidget(cancel_button)
    button_wrapper.addWidget(save_button)
    layout.addLayout(button_wrapper)

    return page


def post_tests(self) -> QWidget:
    """
    Post the fast calibration widget to the main window.

    Args:
        self: The main window object.

    Returns:
        QWidget: The widget containing the fast calibration interface.
    """
    page = QWidget()
    layout = QVBoxLayout(page)

    calibrate_group = QGroupBox("Fast Calibration")
    calibrate_wrapper = QVBoxLayout(calibrate_group)

    x_layout = QHBoxLayout()
    x_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    x_label = QLabel("X Position:")
    x_input = QLineEdit()
    x_layout.addWidget(x_label)
    x_layout.addWidget(x_input)
    calibrate_wrapper.addLayout(x_layout)

    y_layout = QHBoxLayout()
    y_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    y_label = QLabel("Y Position:")
    y_input = QLineEdit()
    y_layout.addWidget(y_label)
    y_layout.addWidget(y_input)
    calibrate_wrapper.addLayout(y_layout)

    button_wrapper = QHBoxLayout()
    button_wrapper.setAlignment(Qt.AlignmentFlag.AlignBottom)
    calibrate_button = QPushButton("Calibrate")
    calibrate_button.clicked.connect(lambda: confirm_fast_calibration_step(self, float(x_input.text()), float(y_input.text())))
    button_wrapper.addWidget(calibrate_button)
    calibrate_wrapper.addLayout(button_wrapper)

    layout.addWidget(calibrate_group)

    send_group = QGroupBox("Send Test to DB")
    send_wrapper = QVBoxLayout(send_group)
    send_label = QLabel("Send test to DB")
    send_button = QPushButton("Send")
    send_button.clicked.connect(lambda: create_task(send_to_db_test(self)))
    send_wrapper.addWidget(send_label)
    send_wrapper.addWidget(send_button)

    layout.addWidget(send_group)

    return page