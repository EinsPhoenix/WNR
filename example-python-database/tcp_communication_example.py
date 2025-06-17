import socket
import json
import sys
import os


# === 1. TcpClient Class ===
# Handles TCP connection, authentication, and communication with the server.
class TcpClient:
    """
    Manages the TCP connection and communication with the Rust server.
    """

    def __init__(self, host="localhost", port=12345):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False

    # --- 1.1 Connection ---
    def connect(self):
        """Establishes a connection to the server."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.connected = True
            print(f"INFO: Connected to server at {self.host}:{self.port}")
            return True
        except socket.error as e:
            print(f"ERROR: Connection failed: {e}")
            self.socket = None
            return False
        except Exception as e:
            print(f"ERROR: Unexpected connection error: {e}")
            self.socket = None
            return False

    # --- 1.2 Authentication ---
    def authenticate(self, password):
        """Handles password authentication with the server."""
        if not self.connected or not self.socket:
            print("ERROR: Not connected to server.")
            return False

        try:
            # Receive prompt, send password, check response
            prompt = self.socket.recv(1024).decode("utf-8")
            print(f"Server: {prompt}", end="")
            self.socket.sendall(password.encode("utf-8"))
            response = self.socket.recv(1024).decode("utf-8")
            print(f"Server: {response}")

            if "Access granted" in response:
                print("INFO: Authentication successful.")
                return True
            else:
                print("ERROR: Authentication failed.")
                self.close()
                return False
        except socket.error as e:
            print(f"ERROR: Socket error during authentication: {e}")
            self.close()
            return False
        except Exception as e:
            print(f"ERROR: Unexpected authentication error: {e}")
            self.close()
            return False

    # --- 1.3 Receiving Responses ---
    def receive_response(self, buffer_size=4096):
        """Receives a complete JSON response terminated by a newline."""
        if not self.connected or not self.socket:
            print("ERROR: Not connected to server.")
            return None

        try:
            response_data = ""
            # Read until newline is received
            while not response_data.endswith("""status":"success"}"""):
                chunk = self.socket.recv(buffer_size).decode("utf-8")
                if not chunk:  # Connection closed by server
                    print("INFO: Server closed the connection.")
                    self.connected = False
                    self.socket = None
                    return None
                response_data += chunk

            # Parse JSON response
            try:
                return json.loads(response_data.strip())
            except json.JSONDecodeError as e:
                print(f"ERROR: Invalid JSON received: {e}")
                print(f"Raw response data: {response_data}")
                return None
        except socket.error as e:
            print(f"ERROR: Socket error receiving response: {e}")
            self.close()
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error receiving response: {e}")
            self.close()
            return None

    # --- 1.4 Sending JSON Data ---
    def send_json(self, data):
        """Sends a Python dictionary as a JSON string to the server."""
        if not self.connected or not self.socket:
            print("ERROR: Not connected to server.")
            return None

        try:
            json_data = json.dumps(data)
            self.socket.sendall(json_data.encode("utf-8"))
            # Server sends newline *after* its response.

            response = self.receive_response()

            # Print formatted response
            if response:
                status = response.get("status", "unknown")
                message = response.get("message", "No message provided")
                if status == "success":
                    print(f"\033[92mServer Response (Success):\033[0m {message}")
                elif status == "error":
                    print(f"\033[91mServer Response (Error):\033[0m {message}")
                else:
                    print(f"Server Response ({status}): {message}")
            else:
                print("WARNING: No valid response received from server.")

            return response
        except socket.error as e:
            print(f"ERROR: Socket error sending data: {e}")
            self.close()
            return None
        except Exception as e:
            print(f"ERROR: Unexpected error sending data: {e}")
            self.close()
            return None

    # --- 1.5 Closing Connection ---
    def close(self):
        """Closes the socket connection if open."""
        if self.socket:
            try:
                self.socket.close()
                print("INFO: Connection closed.")
            except Exception as e:
                print(f"ERROR: Error closing socket: {e}")
            finally:
                self.socket = None
                self.connected = False


# === 2. Helper Functions ===
def load_json_from_file(filename="test.json"):
    """Loads JSON data from a file located in the script's directory."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(script_dir, filename)

    if not os.path.exists(file_path):
        print(f"ERROR: JSON file '{file_path}' not found!")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            print(f"INFO: Successfully loaded JSON from '{filename}'.")
            return data
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in '{filename}': {e}")
        return None
    except IOError as e:
        print(f"ERROR: Could not read file '{filename}': {e}")
        return None
    except Exception as e:
        print(f"ERROR: Unexpected error loading '{filename}': {e}")
        return None


# === 3. Main Execution Logic ===
def main():
    """
    Main function: Connects, authenticates, sends initial data,
    and enters an interactive loop.
    """
    # --- 3.1 Initialization ---
    # Its an example so do not hardcode the password
    server_password = "1234"
    client = TcpClient()

    # --- 3.2 Connection & Authentication ---
    if not client.connect():
        print("ERROR: Failed to connect to server. Exiting.")
        return
    if not client.authenticate(server_password):
        print("ERROR: Authentication failed. Exiting.")
        return

    print("\nINFO: Authentication successful! Ready to send data.")

    # --- 3.3 Send Initial JSON Data ---
    initial_json_data = load_json_from_file("test.json")
    if initial_json_data:
        print("INFO: Sending initial data from 'test.json'...")
        response = client.send_json(initial_json_data)
        if not response:
            print("WARNING: Did not receive response for initial JSON data.")
    else:
        print("WARNING: Could not load 'test.json', skipping initial send.")

    # --- 3.4 Interactive User Loop ---
    try:
        while True:
            print("\n--- Options ---")
            print("1. Send message (type: 'message')")
            print("2. Send command (type: 'command')")
            print("3. Send custom JSON")
            print("4. Exit")

            choice = input("Choose an option (1-4): ")

            if choice == "1":
                message_content = input("Enter your message: ")
                data_to_send = {"type": "message", "content": message_content}
                client.send_json(data_to_send)
            elif choice == "2":
                command_content = input(
                    "Enter command (e.g., init, reset, load, help, status, exit): "
                )
                data_to_send = {"type": "command", "command": command_content}
                client.send_json(data_to_send)
            elif choice == "3":
                custom_json_str = input(
                    'Enter JSON data (e.g., {"type":"data", "data":{...}}): '
                )
                try:
                    data_to_send = json.loads(custom_json_str)
                    if isinstance(data_to_send, dict):
                        client.send_json(data_to_send)
                    else:
                        print(
                            "ERROR: Input is valid JSON but not an object/dictionary."
                        )
                except json.JSONDecodeError as e:
                    print(f"ERROR: Invalid JSON format: {e}")
            elif choice == "4":
                print("INFO: Exiting...")
                break
            else:
                print("ERROR: Invalid option. Please choose 1-4.")

    except KeyboardInterrupt:
        print("\nINFO: Program interrupted by user (Ctrl+C).")
    finally:
        # --- 3.5 Cleanup ---
        print("INFO: Cleaning up and closing connection...")
        client.close()


# === 4. Script Entry Point ===
if __name__ == "__main__":
    main()
