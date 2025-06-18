from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit, QPushButton

from utils import delete_layout_items, set_robot_speed, resize_window


def post_calibrate_camera(self) -> None:
    self.calibrate_camera()


def post_start_sorting(self) -> None:
    self.start_sorting()


def post_change_speed(self, button_text: str) -> None:
    """
    Post the change speed widget to the main window.

    Args:
        self: The main window object.
        button_text (str): The text of the button that was clicked.
    """
    delete_layout_items(self, self.all_wrapper)
    self.main_shown = False
    self.last_clicked_button = button_text

    self.speed_group = QGroupBox("Change Speed")
    self.speed_layout = QVBoxLayout()
    self.speed_group.setLayout(self.speed_layout)

    self.speed_label = QLabel("Enter new speed:")
    self.speed_input = QLineEdit()
    self.speed_layout.addWidget(self.speed_label)
    self.speed_layout.addWidget(self.speed_input)

    self.button_layout = QHBoxLayout()
    self.cancel_button = QPushButton("Cancel")
    self.cancel_button.clicked.connect(self.post_main_widget)
    self.change_speed_button = QPushButton("Change Speed")
    self.change_speed_button.clicked.connect(lambda: set_robot_speed(self.speed_input.text()))
    self.button_layout.addWidget(self.cancel_button)
    self.button_layout.addWidget(self.change_speed_button)
    
    self.all_wrapper.addWidget(self.speed_group)
    self.all_wrapper.addLayout(self.button_layout)
    self.speed_input.setFocus()
    resize_window(self)


def post_storage_display(self) -> None:
    pass