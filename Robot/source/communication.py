from json import dumps, loads
from socket import socket, AF_INET, SOCK_STREAM


class Communication:
    def send_message(self, message_to_send: str) -> None:
        """
        Send a command to the rasberry pi, which controls the camera.

        Args:
            message_to_send (str): The message to send.
        """
        try:
            with socket(AF_INET, SOCK_STREAM) as s:
                s.connect((self.host, self.port))
                s.sendall(dumps(message_to_send).encode("utf-8"))
                response_data = s.recv(1024)
                response = loads(response_data.decode("utf-8"))
                print(f"Received response: {response}")
                return response
        except ConnectionRefusedError:
            print("Connection refused. Please check if the server is running.")
        except Exception as e:
            print(f"An error occurred: {e}")