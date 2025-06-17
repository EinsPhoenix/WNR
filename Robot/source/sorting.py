import asyncio
from datetime import datetime
from time import sleep, perf_counter, time

from PySide6.QtCore import Signal, QThread

import stream.shared_state as shared_state
from utils.config import read_config
from utils.gui import remove_warning

class SortingWorker(QThread):
    label = Signal(str)
    button = Signal(str)

    def __init__(self, main_window: object) -> None:
        """
        Initialize the sorting worker.

        Args:
            main_window (object): The main window object.
        """
        super().__init__()
        self.main_window = main_window
        self._running = True
        self._paused = False

    def run(self) -> None:
        """Start the sorting process with its own event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self._async_run())
        finally:
            loop.close()

    async def _async_run(self) -> None:
        """Start the sorting process."""
        self.button.emit("Pause")
        self.label.emit(f"Waiting for energy prices to be fetched...")
        result = False
        for i in range(3, 0, -1):
            result = await self.main_window.fetcher.run_daily_fetch()
            if result:
                break
            i -= 1
        if not result:
            self.label.emit("Energy prices could not be fetched.")
            self.button.emit("Start")
            self.main_window.robot_busy = False
            return
        self.label.emit("Sorting in progress...\nStop the process by pressing the \"Stop\" button.")
        while True:
            while self._paused:
                if self._running is False:
                    self.label.emit("Sorting process was stopped.")
                    self.button.emit("Start")
                    self.main_window.robot_busy = False
                    return
                sleep(0.1)
            timer = perf_counter()
            block_x, block_y, color = self.main_window.sorter.get_next_block()
            if color == "none":
                self.label.emit("No more blocks to sort.")
                self.button.emit("Start")
                self.main_window.robot_busy = False
                break
            self.label.emit(f"Moving block at ({block_x}, {block_y}) with color {color} to storage.")
            self.main_window.sorter.move_block_to_storage(block_x, block_y, color)
            elapsed_time = perf_counter() - timer
            await self.main_window.db.generate_robot_struct(
                color = color,
                temperature = shared_state.temperature,
                humidity = shared_state.humidity,
                timestamp = str(datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
                energy_consume = elapsed_time / 3600 * 60 * 0.000001,
                energy_cost = self._get_energy_cost()
            )
            if self._running is False:
                self.label.emit("Sorting process was stopped.")
                self.button.emit("Start")
                self.main_window.robot_busy = False
                break

    def _get_energy_cost(self) -> float:
        """Get the energy cost for the current sorting operation."""
        return 187
        # FIXME:
        with open(self.main_window.fetcher.json_file_path, 'r', encoding='utf-8') as f:
            energy_data = shared_state.energy_data
        now = int(time() * 1000)
        for entry in energy_data["api_response"]["data"]:
            if entry["start_timestamp"] <= now <= entry["end_timestamp"]:
                return entry["marketprice"]

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
    if self.db.connected:
        if self.robot_busy:
            # FIXME:
            # self.show_warning("Robot is busy. Please wait until the current operation is finished or cancel it.")
            # return
            pass
        else:
            self.robot_busy = True
        self.sorter.set_speed(read_config(self)["robot"]["speed"])
        if hasattr(self, "sorting_worker"):
            self.sorting_worker.stop()
            self.sorting_worker.wait()
        self.sorting_worker = SortingWorker(self)
        self.sorting_worker.label.connect(lambda text: update_sorting_label(self, text))
        self.sorting_worker.button.connect(lambda text: update_sorting_button(self, text))
        self.sorting_worker.start()
    else:
        self.show_warning("Database connection is not established. Please connect to the database first.")
        return


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