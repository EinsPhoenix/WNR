import socket
import json
import sys
import os


class TcpClient:
    def __init__(self, host="localhost", port=12345):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False

    def connect(self):
        """Connect to the server and return True if successful, False otherwise."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"Connected to server at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def authenticate(self, password):
        """Handle the password authentication with the server."""
        if not self.connected:
            print("Not connected to server.")
            return False

        try:
            prompt = self.socket.recv(1024).decode("utf-8")
            print(f"Server: {prompt}", end="")

            self.socket.sendall(password.encode("utf-8"))

            response = self.socket.recv(1024).decode("utf-8")
            print(f"Server: {response}")

            return "Access granted" in response
        except Exception as e:
            print(f"Authentication error: {e}")
            self.connected = False
            return False

    def receive_response(self, buffer_size=4096):
        """Receive and parse JSON response from the server."""
        if not self.connected:
            print("Not connected to server.")
            return None

        try:

            response_data = ""
            while not response_data.endswith("\n"):
                chunk = self.socket.recv(buffer_size).decode("utf-8")
                if not chunk:
                    self.connected = False
                    return None
                response_data += chunk

            # Parse JSON response
            try:
                return json.loads(response_data.strip())
            except json.JSONDecodeError as e:
                print(f"Error parsing response: {e}")
                print(f"Raw response: {response_data}")
                return None

        except Exception as e:
            print(f"Error receiving response: {e}")
            self.connected = False
            return None

    def send_json(self, data):
        """Send JSON data to the server and return the response."""
        if not self.connected:
            print("Not connected to server.")
            return False

        try:
            json_data = json.dumps(data)
            self.socket.sendall(json_data.encode("utf-8"))

            response = self.receive_response()

            if response:
                status = response.get("status", "unknown")
                message = response.get("message", "No message provided")

                if status == "success":
                    print(f"\033[92mSuccess:\033[0m {message}")
                elif status == "error":
                    print(f"\033[91mError:\033[0m {message}")
                else:
                    print(f"Response ({status}): {message}")

            return response
        except Exception as e:
            print(f"Error sending data: {e}")
            self.connected = False
            return None

    def close(self):
        """Close the connection to the server."""
        if self.socket:
            self.socket.close()
            self.connected = False
            print("Connection closed.")


def load_json_from_file(filename="test.json"):
    """Load JSON data from a file in the same directory as the script."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)

    if not os.path.exists(file_path):
        print(f"ERROR: JSON file '{filename}' not found!")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            return data
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in '{filename}': {e}")
        return None


def main():
    server_password = "1234"

    client = TcpClient()

    if not client.connect():
        return

    if not client.authenticate(server_password):
        print("Authentication failed. Exiting.")
        client.close()
        return

    print("Authentication successful!")

    json_data = load_json_from_file()
    if json_data:
        response = client.send_json(json_data)
        if not response:
            print("Failed to get response for initial JSON data.")

    try:
        while True:
            print("\nOptions:")
            print("1. Send a message")
            print("2. Send a command")
            print("3. Send custom JSON")
            print("4. Exit")

            choice = input("Choose an option (1-4): ")

            if choice == "1":
                message = input("Enter your message: ")
                data = {"type": "message", "content": message}
                client.send_json(data)

            elif choice == "2":
                command = input("Enter command: ")
                data = {"type": "command", "command": command}
                client.send_json(data)

            elif choice == "3":
                try:
                    custom_json = input("Enter JSON data: ")
                    data = json.loads(custom_json)
                    client.send_json(data)
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON: {e}")

            elif choice == "4":
                break

            else:
                print("Invalid option. Please try again.")

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        client.close()


if __name__ == "__main__":
    main()
