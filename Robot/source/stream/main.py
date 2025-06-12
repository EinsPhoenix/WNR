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


opcua_event_loop = None
opcua_client_instance = None


def opcua_client_thread_worker(client: AsyncOPCUAClient, server_url: str):
    """
    Worker function to run the OPC UA client's asyncio event loop.
    Connects to the server and starts periodic data fetching.
    """
    global opcua_event_loop
    opcua_event_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(opcua_event_loop)
    try:
        opcua_event_loop.run_until_complete(client.connect())
        if client.client and client.client.uaclient and client.client.uaclient.protocol:
            opcua_event_loop.run_until_complete(client.fetch_data_periodically())
    except Exception as e:
        pass
    finally:
        pending = asyncio.all_tasks(opcua_event_loop)
        for task in pending:
            task.cancel()
        if pending:
            opcua_event_loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        opcua_event_loop.close()


def main(self):
    """Main function to run the modularized ArUco marker and color detection application."""
    global opcua_client_instance
    config = read_config(self)
    stream_handler = StreamHandler(
        host = config["stream"]["host"],
        port = config["stream"]["port"]
    )
    if not stream_handler.open():
        return
    marker_detector = MarkerDetector()
    video_analyzer = VideoAnalyzer()
    opcua_server_url = shared_state.OPC_SERVER_URL
    opcua_client_instance = AsyncOPCUAClient(opcua_server_url)
    opcua_thread = threading.Thread(
        target=opcua_client_thread_worker,
        args=(opcua_client_instance, opcua_server_url),
        daemon=True
    )
    opcua_thread.start()
    command_handler = CommandHandler(
        host = config["tcp"]["host"],
        port = config["tcp"]["port"],
        marker_detector = marker_detector,
        video_analyzer = video_analyzer
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
            video_analyzer.calculate_and_store_transformation(
                shared_state.calibrated_marker_origins
            )
    ui_window = UIWindow(
        stream_handler=stream_handler,
        marker_detector=marker_detector,
        video_analyzer=video_analyzer,
    )
    ui_window.setup_window()
    try:
        ui_window.run(self)
    except KeyboardInterrupt:
        pass
    finally:
        if opcua_client_instance and opcua_event_loop:
            if opcua_client_instance.running:
                future = asyncio.run_coroutine_threadsafe(opcua_client_instance.stop(), opcua_event_loop)
                try:
                    future.result(timeout=10)
                except Exception as e:
                    pass
            if opcua_event_loop.is_running():
                opcua_event_loop.call_soon_threadsafe(opcua_event_loop.stop)
        if opcua_thread and opcua_thread.is_alive():
            opcua_thread.join(timeout=5)
        command_handler.stop_server()
        stream_handler.close()


if __name__ == "__main__":
    main()
