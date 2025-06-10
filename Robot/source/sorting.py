from time import sleep
from random import randint

from PySide6.QtCore import Signal, QThread

from utils import remove_warning

class SortingWorker(QThread):
    label = Signal(str)
    button = Signal(str)

    def __init__(self, main_self: object) -> None:
        """
        Initialize the sorting worker.

        Args:
            main_self (object): The main window object.
        """
        super().__init__()
        self.main_self = main_self
        self._running = True
        self._paused = False

    def run(self) -> None:
        """Start the sorting process."""
        self.label.emit("Sorting in progress...\nStop the process by pressing the \"Stop\" button.")
        self.button.emit("Pause")
        while True:
            while self._paused:
                if self._running is False:
                    self.label.emit("Sorting process was stopped.")
                    self.button.emit("Start")
                    self.main_self.robot_busy = False
                    return
                sleep(0.1)
            block_x, block_y, color = self.main_self.sorter.get_next_block()
            color = "red"
            if color == "none":
                self.label.emit("No more blocks to sort.")
                self.button.emit("Start")
                self.main_self.robot_busy = False
                break
            self.label.emit(f"Moving block at ({block_x}, {block_y}) with color {color} to storage.")
            self.main_self.sorter.move_block_to_storage(block_x, block_y, color)
            if self._running is False:
                self.label.emit("Sorting process was stopped.")
                self.button.emit("Start")
                self.main_self.robot_busy = False
                break

    def stop(self) -> None:
        """Stop the sorting process."""
        self._running = False
        self.label.emit("Stopping sorting process...")

    def pause(self) -> None:
        """Pause the sorting process."""
        if self._paused:
            self._paused = False
            self.label.emit("Sorting resumed.")
            self.button.emit("Pause")
        else:
            self._paused = True
            self.label.emit("Sorting paused. Press \"Resume\" to continue.")
            self.button.emit("Resume")

def start_sorting_worker(self) -> None:
    """
    Start the sorting worker thread.

    Args:
        self: The main window object.
    """
    if self.robot_busy:
        self.show_warning("Robot is busy. Please wait until the current operation is finished or cancel it.")
        return
    else:
        self.robot_busy = True
    if hasattr(self, "sorting_worker"):
        self.sorting_worker.stop()
        self.sorting_worker.wait()
    self.sorting_worker = SortingWorker(self)
    self.sorting_worker.label.connect(lambda text: update_sorting_label(self, text))
    self.sorting_worker.button.connect(lambda text: update_sorting_button(self, text))
    self.sorting_worker.start()


def update_sorting_label(self, text: str) -> None:
    """
    Update the sorting label with the given text.

    Args:
        self: The main window object.
        text (str): The text to set in the sorting label.
    """
    self.sorting_label.setText(text)


def update_sorting_button(self, text: str) -> None:
    """
    Update the sorting button with the given text.

    Args:
        self: The main window object.
        text (str): The text to set in the sorting button.
    """
    self.start_sorting_button.setText(text)
    if text == "Start":
        self.start_sorting_button.clicked.disconnect()
        self.start_sorting_button.clicked.connect(lambda: start_sorting_worker(self))
    else:
        self.start_sorting_button.clicked.disconnect()
        self.start_sorting_button.clicked.connect(lambda: self.sorting_worker.pause())


def cancel_sorting(self) -> None:
    """
    Cancel the sorting process and reset the state.

    Args:
        self: The main window object.
    """
    if hasattr(self, "sorting_worker") and self.sorting_worker.isRunning():
        self.sorting_worker.stop()
        self.sorting_worker.wait()
        update_sorting_label(self, "Sorting process was cancelled.")
        update_sorting_button(self, "Start")
    remove_warning(self)