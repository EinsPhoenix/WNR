import asyncio
import threading

from stream.command_handler import CommandHandler
from stream.marker_detector import MarkerDetector
from stream.opcua_client import AsyncOPCUAClient
import stream.shared_state as shared_state
from stream.stream_handler import StreamHandler
from stream.ui_window import UIWindow
from stream.video_analyzer import VideoAnalyzer
from utils.config import read_config


class Stream:
    def __init__(self, main_window):
        """
        Initializes the Stream class with the main window reference.

        Args:
            main_window: The main window instance where the stream will be displayed.
        """
        self.main_window = main_window
        self.opcua_client_instance = None
        self.opcua_event_loop = None

    def opcua_client_thread_worker(self, client: AsyncOPCUAClient, server_url: str):
        """
        Worker function to run the OPC UA client's asyncio event loop.
        Connects to the server and starts periodic data fetching.
        """
        self.opcua_event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.opcua_event_loop)
        try:
            self.opcua_event_loop.run_until_complete(client.connect())
            if client.client and client.client.uaclient and client.client.uaclient.protocol:
                self.opcua_event_loop.run_until_complete(client.fetch_data_periodically())
        except Exception as e:
            pass
        finally:
            pending = asyncio.all_tasks(self.opcua_event_loop)
            for task in pending:
                task.cancel()
            if pending:
                self.opcua_event_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            self.opcua_event_loop.close()


    def main(self):
        """Main function to run the modularized ArUco marker and color detection application."""
        config = read_config(self.main_window)
        stream_handler = StreamHandler(
            host = config["stream"]["host"],
            port = config["stream"]["port"]
        )
        if not stream_handler.open():
            return
        marker_detector = MarkerDetector()
        self.video_analyzer = VideoAnalyzer(self.main_window.config_path)
        opcua_server_url = shared_state.OPC_SERVER_URL
        self.opcua_client_instance = AsyncOPCUAClient(opcua_server_url)
        opcua_thread = threading.Thread(
            target=self.opcua_client_thread_worker,
            args=(self.opcua_client_instance, opcua_server_url),
            daemon=True
        )
        opcua_thread.start()
        command_handler = CommandHandler(
            host = config["tcp"]["host"],
            port = config["tcp"]["port"],
            marker_detector = marker_detector,
            video_analyzer = self.video_analyzer
        )
        command_handler.start_server()
        if not stream_handler.wait_for_first_frame(timeout=60):
            command_handler.stop_server()
            stream_handler.close()
            return
        with shared_state.data_lock:
            shared_state.calibrated_marker_origins = marker_detector.load_calibration_data(
                shared_state.CALIBRATION_FILE_PATH
            )
            if shared_state.calibrated_marker_origins:
                self.video_analyzer.calculate_and_store_transformation(
                    shared_state.calibrated_marker_origins
                )
        ui_window = UIWindow(
            stream_handler = stream_handler,
            marker_detector = marker_detector,
            video_analyzer = self.video_analyzer,
        )
        ui_window.setup_window()
        try:
            ui_window.run(self.main_window)
        except KeyboardInterrupt:
            pass
        finally:
            if self.opcua_client_instance and self.opcua_event_loop:
                if self.opcua_client_instance.running:
                    if self.opcua_event_loop and not self.opcua_event_loop.is_closed():
                        try:
                            future = asyncio.run_coroutine_threadsafe(self.opcua_client_instance.stop(), self.opcua_event_loop)
                            future.result(timeout=5.0)
                        except:
                            pass
                        finally:
                            if not self.opcua_event_loop.is_closed():
                                self.opcua_event_loop.call_soon_threadsafe(self.opcua_event_loop.stop)
            if opcua_thread and opcua_thread.is_alive():
                opcua_thread.join(timeout=5)
            command_handler.stop_server()
            stream_handler.close()

    async def start_stream(self) -> bool:
        """
        Starts the stream processing in a separate thread.

        Returns:    
            bool: True if the stream started successfully, False otherwise.
        """
        try:
            self.main_window.stream_running = True
            self.stream_thread = threading.Thread(target=self.main, daemon=True)
            self.stream_thread.start()
            if self.stream_thread.is_alive():
                return True
        except: pass
        return False

    async def stop_stream(self) -> bool:
        """
        Stops the stream processing and cleans up resources.
        Returns:
            bool: False if the stream stopped successfully, True otherwise.
        """
        try:
            print("Stopping stream...")
            if hasattr(self, "stream_thread") and self.stream_thread.is_alive():
                print("Stream thread is alive, attempting to stop it...")
                self.main_window.stream_running = False
                self.stream_thread.join(timeout=5)
                if not self.stream_thread.is_alive():
                    return False
        except: pass
        return True