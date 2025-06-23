from asyncio import create_task
from typing import Callable

from PySide6.QtCore import Qt, Signal, Property, QPropertyAnimation, QEasingCurve, QEvent, QObject, QTimer
from PySide6.QtGui import QPainter, QColor, QBrush, QMouseEvent
from PySide6.QtWidgets import QPushButton, QWidget, QVBoxLayout, QLineEdit
from PySide6.QtCore import QRect


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
            QPushButton:checked {
                border-left: 4px solid #99354F;
            }
            QPushButton:hover {
                background-color: rgba(254, 176, 189, 0.5);
            }
            QPushButton:focus {
                background-color: rgba(254, 176, 189, 0.5);
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


class CustomToggle(QWidget):
    toggled = Signal(bool)

    def __init__(self, async_bool: bool = False, toggle_on_function: Callable | None = None, toggle_off_function: Callable | None = None, parent: QWidget | None = None) -> None:
        """
        Initialize the CustomToggle widget.

        Args:
            async_bool (bool, optional): Whether the toggle should operate asynchronously. Defaults to False.
            toggle_on_function (Callable, optional): The function to call when the toggle is turned on. Defaults to None.
            toggle_off_function (Callabele, optional): The function to call when the toggle is turned off. Defaults to None.
            parent (QWidget, optional): The parent widget. Defaults to None.
        """
        super().__init__(parent)

        self._checked = False
        self._async_running = False
        self._async = async_bool
        if async_bool and (toggle_on_function is None or toggle_off_function is None):
            raise ValueError("toggle_on_function and toggle_off_function must be provided for asynchronous toggling.")
        else:
            self._toggle_on_function = toggle_on_function
            self._toggle_off_function = toggle_off_function
        self.setFixedSize(70, 35)

        self.bg_color_off = QColor(60, 60, 60)
        self.bg_color_loading = QColor(255, 152, 0)
        self.bg_color_on = QColor(76, 175, 80)
        self.circle_color = QColor(255, 255, 255)

        self._circle_position = 4

        self.animation = QPropertyAnimation(self, b"circlePosition")
        self.animation.setDuration(250)
        self.animation.setEasingCurve(QEasingCurve.Type.OutBack)
        self.async_animation = QPropertyAnimation(self, b"circlePosition")
        self.async_animation.setDuration(250)
        self.async_animation.setEasingCurve(QEasingCurve.Type.OutBack)

        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def get_circle_position(self) -> float:
        """
        Get the current position of the toggle circle.

        Returns:
            float: The current position of the circle.
        """
        return self._circle_position

    def set_circle_position(self, pos: float) -> None:
        """
        Set the position of the toggle circle.

        Args:
            pos (float): The new position of the circle.
        """
        self._circle_position = pos
        self.update()

    circlePosition = Property(float, get_circle_position, set_circle_position)

    def is_checked(self) -> bool:
        """
        Check if the toggle is currently checked.

        Returns:
            bool: True if the toggle is checked, False otherwise.
        """
        return self._checked

    def set_checked(self, checked: bool) -> None:
        """
        Set the checked state of the toggle.

        Args:
            checked (bool): The new checked state.
        """
        if self._checked != checked:
            self._checked = checked
            if self._async:
                self._animate_async_toggle()
            else:
                self._animate_toggle()
            self.toggled.emit(self._checked)

    def toggle(self) -> None:
        """Toggle the checked state of the toggle."""
        self.set_checked(not self._checked)

    def _animate_toggle(self) -> None:
        """Animate the toggle switch to its new position based on the checked state."""
        if self.animation.state() == QPropertyAnimation.State.Running:
            self.animation.stop()
        if self._checked:
            end_pos = self.width() - 31
        else:
            end_pos = 4
        self.animation.setStartValue(self._circle_position)
        self.animation.setEndValue(end_pos)
        self.animation.start()

    def _animate_async_toggle(self) -> None:
        """
        Animate the toggle switch asynchronously to its new position based on the checked state.
        """
        if self.animation.state() == QPropertyAnimation.State.Running:
            self.animation.stop()
        if self._async_running:
            return
        else:
            self._async_running = True
        mid_pos = (self.width() - 27) / 2
        self.animation.setStartValue(self._circle_position)
        self.animation.setEndValue(mid_pos)
        self.animation.start()

        async def handle_async() -> None:
            """
            Handle the asynchronous operation and update the toggle state.
            """
            self.animation.finished.disconnect()
            if self._checked:
                try:
                    result = await self._toggle_on_function()
                    self._checked = result
                except Exception as e:
                    self._checked = False
            else:
                try:
                    result = await self._toggle_off_function()
                    self._checked = result
                except Exception as e:
                    self._checked = True
            if self._checked:
                end_pos = self.width() - 31
            else:
                end_pos = 4
            self._async_running = False
            self.animation.setStartValue(self._circle_position)
            self.animation.setEndValue(end_pos)
            self.animation.start()

        self.animation.finished.connect(lambda: create_task(handle_async()))

    def paintEvent(self, event: QEvent) -> None:
        """
        Paint the toggle switch with a rounded rectangle and a circle.

        Args:
            event (QEvent): The paint event.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        radius = rect.height() // 2

        bg_color = self.bg_color_on if self._checked else self.bg_color_off
        if self._async_running:
            bg_color = self.bg_color_loading
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(rect, radius, radius)

        shadow_rect = QRect(int(self._circle_position + 2), 6, 27, 25)
        painter.setBrush(QBrush(QColor(0, 0, 0, 20)))
        painter.drawEllipse(shadow_rect)

        circle_rect = QRect(int(self._circle_position), 4, 27, 27)
        painter.setBrush(QBrush(self.circle_color))
        painter.drawEllipse(circle_rect)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """
        Handle mouse press events to toggle the switch.

        Args:
            event (QMouseEvent): The mouse press event.
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggle()
        super().mousePressEvent(event)


class GlobalEventListener(QObject):
    def __init__(self, main_window: object) -> None:
        """
        Initialize the global event listener.

        Args:
            main_window (object): The main window object to which the listener is attached.
        """
        super().__init__()
        self.main_window = main_window

    def eventFilter(self, obj: object, event: QEvent) -> bool:
        """
        Overrides the event method to handle custom events.

        Args:
            obj (object): The object that received the event.
            event (QEvent): The event to handle.

        Returns:
            bool: True if the event was handled, False otherwise.
        """
        main_window = self.main_window
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                if type(main_window.focusWidget()) == QLineEdit:
                    main_window.focusNextChild()
                else:
                    try:
                        main_window.focusWidget().click()
                    except:
                        pass
                return True
            elif event.key() == 16777218 or event.key() == Qt.Key.Key_Left or event.key() == Qt.Key.Key_Up:
                if not main_window.submenu_mode and hasattr(main_window, "sidebar"):
                    try:
                        for i, button in enumerate(main_window.sidebar.buttons):
                            if button == main_window.focusWidget():
                                main_window.sidebar.buttons[(i + len(main_window.sidebar.buttons) - 1) % len(main_window.sidebar.buttons)].setFocus()
                                break
                    except:
                        pass
                else:
                    if not type(main_window.focusWidget()) == QLineEdit or event.key() == 16777218:
                        try:
                            for i, child in enumerate(main_window.focusable_widgets):
                                if child == main_window.focusWidget():
                                    main_window.focusable_widgets[(i + len(main_window.focusable_widgets) - 1) % len(main_window.focusable_widgets)].setFocus()
                                    break
                        except:
                            pass
                    else:
                        return super().eventFilter(obj, event)
                return True
            elif event.key() == Qt.Key.Key_Tab or event.key() == Qt.Key.Key_Right or event.key() == Qt.Key.Key_Down:
                if not main_window.submenu_mode and hasattr(main_window, "sidebar"):
                    try:
                        for i, button in enumerate(main_window.sidebar.buttons):
                            if button == main_window.focusWidget():
                                main_window.sidebar.buttons[(i + 1) % len(main_window.sidebar.buttons)].setFocus()
                                break
                    except:
                        pass
                else:
                    if not type(main_window.focusWidget()) == QLineEdit or event.key() == Qt.Key.Key_Tab:
                        try:
                            for i, child in enumerate(main_window.focusable_widgets):
                                if child == main_window.focusWidget():
                                    main_window.focusable_widgets[(i + 1) % len(main_window.focusable_widgets)].setFocus()
                                    break
                        except:
                            pass
                    else:
                        return super().eventFilter(obj, event)
                return True
            elif event.key() == Qt.Key.Key_Escape:
                if not main_window.submenu_mode:
                    if hasattr(main_window, "worker") and main_window.worker.isRunning():
                        main_window.worker.stop()
                        main_window.worker.wait()
                    self.main_window.close()
                else:
                    main_window.submenu_mode = False
                    for button in main_window.sidebar.buttons:
                        if button.isChecked():
                            button.setFocus()
                            break
                return True
        if event.type() == QEvent.Type.Close:
            if hasattr(main_window, "sorting_worker") and main_window.sorting_worker.isRunning():
                main_window.sorting_worker.stop()
                main_window.sorting_worker.wait()
            return super().eventFilter(obj, event)
        return super().eventFilter(obj, event)