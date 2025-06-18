import asyncio
from json import dumps, loads
from socket import socket, AF_INET, SOCK_STREAM
from threading import Thread


def start_fetching(self) -> None:
    """
    Connect to the Dobot device and start opcua client.

    Args:
        self: The main window object.
    """
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
    print("Send message")
    try:
        with socket(AF_INET, SOCK_STREAM) as s:
            try:
                s.connect((self.tcp_host, self.tcp_port))
            except:
                s.connect((self.main_window.tcp_host, self.main_window.tcp_port))
            s.sendall(dumps(message_to_send).encode("utf-8"))
            response_data = s.recv(1024)
            response = loads(response_data.decode("utf-8"))
            return response
    except ConnectionRefusedError:
        print("Connection refused. Please check if the server is running.")
        self.main_window.show_warning("Connection refused. Please check if the server is running.")
    except Exception as e:
        print(e)
        self.main_window.show_warning(f"An error occurred: {e}")