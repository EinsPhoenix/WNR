from sys import argv, exit

from keyboard import press_and_release
from PySide6.QtGui import QIcon, QFontMetrics, Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel, QVBoxLayout
from PySide6.QtCore import QRect, QTimer, QEvent
from qt_material import apply_stylesheet

from automated_sorter import AutomatedSorter
from gui import post_calibrate_camera, post_start_sorting, post_change_speed, post_storage_display
from utils import set_title_bar_color, delete_layout_items, resize_window


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.esc_pressed = False
        self.main_menu_buttons: list = []
        self.last_clicked_button = ""
        self.set_style_sheet()
        self.setWindowTitle("WNR Robot Controller")
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.CustomizeWindowHint)
        self.min_width: int = QFontMetrics(self.font()).horizontalAdvance(self.windowTitle()) + 160
        self.setMinimumWidth(self.min_width)

        # main_widget
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.all_wrapper = QVBoxLayout()
        self.main_widget.setLayout(self.all_wrapper)
        self.post_connection_menu()        

    def post_connection_menu(self) -> None:
        # TODO: Hier noch einen Button zum Verbinden mit dem Roboter hinzufügen
            # Vielleicht auch einen Ladekreis
        # FIXME: Entkommentieren, wenn ich fertig getestet habe
        # self.sorter = AutomatedSorter()
        self.post_main_widget()

    def set_style_sheet(self) -> None:
        """Sets the style sheet for the main window."""
        self.setStyleSheet("")
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
                border-color: #D71946;
            }
            QPushButton:focus {
                background-color: #31363b;
                border-color: #D71946;
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
                border-color: #D71946;
            }
            QLineEdit:focus {
                border-color: #D71946;
            }
            QCheckBox {
                border: 2px solid #949CA3;
                border-radius: 5px;
                padding: 0px 8px;
            }
            QCheckBox::focus {
                border: 2px solid #D71946;
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
                border: 2px solid #D71946;
                border-radius: 5px;
                color: #ffffff;
            }
        """)

    def post_main_widget(self) -> None:
        """Shows the main widget."""
        delete_layout_items(self, self.all_wrapper)
        self.main_shown = True

        # calibrate_button
        self.calibrate_button = QPushButton("Calibrate camera")
        self.calibrate_button.clicked.connect(lambda: post_calibrate_camera(self))
        self.all_wrapper.addWidget(self.calibrate_button)

        # sorting_button
        self.sorting_button = QPushButton("Start sorting")
        self.sorting_button.clicked.connect(lambda: post_start_sorting(self))
        self.all_wrapper.addWidget(self.sorting_button)

        # home_button
        self.home_button = QPushButton("Move to home position")
        self.home_button.clicked.connect(lambda: self.sorter.move_home())
        self.all_wrapper.addWidget(self.home_button)

        # speed_button
        self.speed_button = QPushButton("Change speed")
        self.speed_button.clicked.connect(lambda: post_change_speed(self, self.speed_button.text()))
        self.all_wrapper.addWidget(self.speed_button)
        self.main_menu_buttons.append(self.speed_button)

        # storage_button
        self.storage_button = QPushButton("Show storage status")
        self.storage_button.clicked.connect(lambda: post_storage_display(self))
        self.all_wrapper.addWidget(self.storage_button)

        # exit_button
        self.exit_button = QPushButton("Exit")
        self.exit_button.clicked.connect(lambda: self.close())
        self.all_wrapper.addWidget(self.exit_button)

        for button in self.main_menu_buttons:
            if button.text() == self.last_clicked_button:
                button.setFocus()
                break
        else:
            self.calibrate_button.setFocus()

    def keyPressEvent(self, event: QEvent) -> None:
        """
        Overrides the keyPressEvent method to handle the Enter and Escape keys.
        Enter and Return keys will change the focus to the next widget if on a QLineEdit.

        Args:
            event (QEvent): The key press event.
        """
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if type(self.focusWidget()) == QLineEdit:
                self.focusNextChild()
            else:
                try:
                    self.focusWidget().click()
                except:
                    pass
        elif event.key() == Qt.Key.Key_Escape and not self.esc_pressed:
            self.esc_pressed = True
            if self.main_shown:
                self.close()
            else:
                if hasattr(self, "worker") and self.worker.isRunning():
                    self.worker.stop()
                    self.worker.wait()
                if not self.main_shown:
                    self.post_main_widget()
                self.esc_pressed = False
        else:
            super().keyPressEvent(event)

    def show_warning(self, message: str, interactable: bool = False, resize_width: bool = True, insert_place: int = 2) -> None:
        """
        Shows a warning message in the GUI.

        Args:
            message (str): The message to be shown.
            interactable (bool, optional): If True, the message is selectable. Default is False.
            resize_width (bool, optional): If True, the window width is resized. Default is True.
            insert_place (int, optional): The index to insert the message at. Default is 2.
        """
        if not self.main_shown:
            if not hasattr(self, "warned") or not self.warned:
                self.warned = True
                self.warning_wrapper = QVBoxLayout()
                self.warning_text = QLabel(message)
                self.warning_text.setWordWrap(False)
                self.warning_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.warning_wrapper.addWidget(self.warning_text)
                self.all_wrapper.insertLayout(insert_place, self.warning_wrapper)
                warning_min_height: int = QFontMetrics(self.font()).boundingRect(QRect(0, 0, self.warning_text.width(), 0), Qt.TextFlag.TextWordWrap, message).height() + 22
            else:
                self.warning_text.setText(message)
                warning_min_height: int = QFontMetrics(self.font()).boundingRect(QRect(0, 0, QFontMetrics(self.font()).horizontalAdvance(message) + 100, 0), Qt.TextFlag.TextWordWrap, message).height() + 22
            if interactable:
                self.warning_text.setStyleSheet("""
                    QLabel {
                        border: 2px solid #949CA3;
                        border-radius: 5px;
                        padding: 0px 8px;
                    }
                    QLabel:hover {
                        border-color: #D71946;
                    }
                    QLabel:focus {
                        border-color: #D71946;
                    }
                """)
                self.warning_text.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse | Qt.TextInteractionFlag.TextSelectableByKeyboard)
                self.warning_text.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            else:
                self.warning_text.setStyleSheet("""
                    QLabel {
                        border: 2px solid #949CA3;
                        border-radius: 5px;
                        padding: 0px 8px;
                    }
                """)
                self.warning_text.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
                self.warning_text.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            self.warning_text.setMinimumHeight(warning_min_height)
            resize_window(self, resize_width = resize_width)

    def focusInEvent(self, event: QEvent) -> None:
        """
        Overrides the focusInEvent method to set the style sheet for the main window.

        Args:
            event (QEvent): The focus in event.
        """
        super().focusInEvent(event)
        self.set_style_sheet()


def main() -> None:
    """Main function of the script. Starts and styles the GUI."""
    app = QApplication(argv)
    app.setWindowIcon(QIcon(r".\rob_icon.ico"))
    apply_stylesheet(app, theme="WNR_theme.xml", extra={"pyside6": True})
    main_window = MainWindow()
    main_window.show()
    set_title_bar_color(main_window)
    exit(app.exec())


if __name__ == "__main__":
    main()