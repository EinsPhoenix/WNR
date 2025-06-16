import asyncio
from json import dumps, loads
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread

from stream.main import main


def connect_to_everything(self) -> None:
    """
    Connect to the Dobot device and start opcua client.

    Args:
        self: The main window object.
    """
    from automated_sorter import AutomatedSorter
    self.sorter = AutomatedSorter(self)
    self.stream_thread = Thread(target=main, daemon=True, args=(self,))
    self.stream_thread.start()

    def run_async_scheduler() -> None:
        """Run the async scheduler in a separate thread."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.fetcher.start_scheduler())
        loop.close()

    self.fetcher_thread = Thread(target=run_async_scheduler, daemon=True)
    self.fetcher_thread.start()
    self.post_main_widget()


def send_message(self, message_to_send: dict) -> str | None:
    """
    Send a command to the rasberry pi, which controls the camera.

    Args:
        self: The main window object.
        message_to_send (dict): The message to send.

    Returns:
        str | None: The response from the server, or None if an error occurred.
    """
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            s.connect((self.tcp_host, self.tcp_port))
            s.sendall(dumps(message_to_send).encode("utf-8"))
            response_data = s.recv(1024)
            response = loads(response_data.decode("utf-8"))
            return response
    except ConnectionRefusedError:
        self.show_warning("Connection refused. Please check if the server is running.")
    except Exception as e:
        self.show_warning(f"An error occurred: {e}")