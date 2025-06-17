import asyncio
from sys import argv, platform

from PySide6.QtCore import QRect, QEvent
from PySide6.QtGui import QIcon, QFontMetrics, Qt, QPixmap
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QVBoxLayout, QGroupBox, QHBoxLayout, QStackedWidget, QSizePolicy
from qasync import QEventLoop

from automated_sorter import AutomatedSorter
from gui import reset_slogan, post_calibrate_camera, post_start_sorting, post_storage_display, post_camera_display, post_color_analysis, post_color_settings, post_manual_controls, post_settings
from stream.stream import Stream
from utils.communication import start_fetching
from utils.config import read_config
from utils.custom_elements import CustomSidebar, GlobalEventListener
from utils.database_imp import DatabaseImp
from utils.energy_price_fetch import EnergyPriceFetcher
from utils.gui import delete_layout_items, set_style_sheet, resize_window, remove_warning, set_title_bar_color, get_focusable_widgets


class MainWindow(QMainWindow):
    def __init__(self, app: QApplication) -> None:
        """
        Initializes the main window of the WNR Robot Controller.

        Args:
            app (QApplication): The application instance.
        """
        super().__init__()
        self.app = app
        self.global_event_listener = GlobalEventListener(self)
        self.app.installEventFilter(self.global_event_listener)
        self.robot_busy = False
        self.warned = False
        self.submenu_mode = False
        self.storage_counts = [0, 0, 0, 0]
        self.config_path = "config.json"
        config = read_config(self)
        self.tcp_host = config["tcp"]["host"]
        self.tcp_port = config["tcp"]["port"]
        self.camera_display = QLabel("Sorry, the camera is not available yet.")
        self.color_analysis = QLabel("Sorry, the camera is not available yet.")
        self.sorter = AutomatedSorter(self)
        self.db = DatabaseImp(self)
        self.fetcher = EnergyPriceFetcher(self)
        self.stream = Stream(self)
        set_style_sheet(self)
        self.setWindowTitle("WNR Robot Controller")
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint | Qt.WindowType.WindowMinimizeButtonHint | Qt.WindowType.CustomizeWindowHint)
        self.min_width: int = QFontMetrics(self.font()).horizontalAdvance(self.windowTitle()) + 160
        self.setMinimumWidth(self.min_width)

        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)

        self.main_wrapper = QHBoxLayout()
        self.main_widget.setLayout(self.main_wrapper)

        self.sidebar_wrapper = QVBoxLayout()
        self.main_wrapper.addLayout(self.sidebar_wrapper)

        self.all_wrapper = QVBoxLayout()
        self.main_wrapper.addLayout(self.all_wrapper)

    async def post_connection_menu(self) -> None:
        """Posts the connection menu to the main window."""
        reset_slogan(self)

        self.connection_group = QGroupBox("Connect to DoBot")
        self.connection_layout = QVBoxLayout()
        self.connection_group.setLayout(self.connection_layout)

        self.connection_button = QPushButton("Connect")
        self.connection_button.clicked.connect(lambda: start_fetching(self))
        self.connection_layout.addWidget(self.connection_button)
        self.all_wrapper.addWidget(self.connection_group)
        resize_window(self)

    def post_main_widget(self) -> None:
        """Shows the main widget with the sidebar and buttons."""
        delete_layout_items(self, self.all_wrapper)
        reset_slogan(self)
        delete_layout_items(self, self.sidebar_wrapper)

        self.logo_label = QLabel()
        self.logo_label.setPixmap(QPixmap(r".\icons\wnr_logo.png").scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.sidebar_wrapper.addWidget(self.logo_label)

        self.sidebar = CustomSidebar(["Calibrate Camera", "Start sorting", "Storage status", "Camera", "Color analysis", "Color settings", "Manual controls", "Settings", "Exit"])
        self.sidebar.setFixedWidth(250)
        self.sidebar.tabChanged.connect(self.on_tab_changed)

        self.content_stack = QStackedWidget()
        self.content_stack.addWidget(post_calibrate_camera(self))
        self.content_stack.addWidget(post_start_sorting(self))
        self.content_stack.addWidget(post_storage_display(self))
        self.content_stack.addWidget(post_camera_display(self))
        self.content_stack.addWidget(post_color_analysis(self))
        self.content_stack.addWidget(post_color_settings(self))
        self.content_stack.addWidget(post_manual_controls(self))
        self.content_stack.addWidget(post_settings(self))

        self.sidebar.buttons[-1].clicked.connect(self.close)

        self.sidebar_wrapper.addWidget(self.sidebar)
        self.sidebar.buttons[0].setFocus()
        self.all_wrapper.addWidget(self.content_stack)

        resize_window(self)

    def on_tab_changed(self, index: int) -> None:
        """
        Handles the tab change event in the sidebar.

        Args:
            index (int): The index of the selected tab.
        """
        remove_warning(self)
        self.content_stack.setCurrentIndex(index)
        self.focusable_widgets = get_focusable_widgets(self.content_stack.currentWidget())
        try: self.focusable_widgets[0].setFocus()
        except: pass
        self.submenu_mode = True


    def show_warning(self, message: str, interactable: bool = False, insert_place: int = 2) -> None:
        """
        Shows a warning message in the GUI.

        Args:
            message (str): The message to be shown.
            interactable (bool, optional): If True, the message is selectable. Default is False.
            insert_place (int, optional): The index to insert the message at. Default is 2.
        """
        if not self.warned:
            self.warned = True
            self.warning_text = QLabel(message)
            self.warning_text.setWordWrap(False)
            self.warning_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.warning_text.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
            self.content_stack.currentWidget().layout().insertWidget(insert_place, self.warning_text)
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
        resize_window(self)

    def focusInEvent(self, event: QEvent) -> None:
        """
        Overrides the focusInEvent method to set the style sheet for the main window.

        Args:
            event (QEvent): The focus in event.
        """
        super().focusInEvent(event)
        set_style_sheet(self)

    def close(self) -> None:
        """Overrides the close method to handle the closing of the main window."""
        # FIXME: Hier muss ich noch die Connections killen
        super().close()


async def main() -> None:
    """Main function of the script. Starts and styles the GUI."""
    if platform == "win32":
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID("WNR.App.1.0")
    app = QApplication(argv)
    app.setWindowIcon(QIcon(r".\icons\wnr_logo.png"))
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    main_window = MainWindow(app)
    await main_window.post_connection_menu()
    main_window.show()
    set_title_bar_color(main_window)
    # exit(app.exec())
    with loop:
        return loop.run_forever()


if __name__ == "__main__":
    asyncio.run(main())