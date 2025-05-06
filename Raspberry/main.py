import time
import json
import threading
import socket  # Added for TCP server
from opcua import Server, ua

# Import functions from other files
from getcolor import capture_part, csv_data as colors_df_for_capture  # Ensure csv_data is loaded
from getsensordata import get_sensor_data

# Global OPC UA node variables
sensordata_var_node = None
opcua_server = None

# TCP Server Configuration
TCP_HOST = '0.0.0.0'  # Listen on all available interfaces
TCP_PORT = 65432  # Port for TCP commands

def handle_tcp_client(conn, addr):
    global sensordata_var_node
    print(f"TCP Connection established from {addr}")
    try:
        while True:
            data = conn.recv(1024)
            if not data:
                print(f"TCP Connection closed by {addr}")
                break
            
            command = data.decode().strip()
            print(f"TCP Command received from {addr}: {command}")

            if command == "TakePicture":
                print("TakePicture command received. Calling capture_part...")
                try:
                    color_data_dict = capture_part()
                    if color_data_dict:
                        response_json = json.dumps(color_data_dict)
                    else:
                        response_json = json.dumps({"error": "Failed to capture part or capture_part returned None"})
                    conn.sendall(response_json.encode())
                    print(f"Sent ColorData over TCP to {addr}: {response_json}")
                except Exception as e:
                    error_msg = json.dumps({"error": f"Exception in capture_part: {str(e)}"})
                    conn.sendall(error_msg.encode())
                    print(f"Sent error over TCP to {addr}: {error_msg}")

            elif command == "GetSensor":
                print("GetSensor command received. Calling get_sensor_data...")
                response_payload = {}
                try:
                    sensor_data_dict = get_sensor_data()
                    if sensor_data_dict:
                        sensor_json_string = json.dumps(sensor_data_dict)
                        if sensordata_var_node:
                            sensordata_var_node.set_value(sensor_json_string)
                            print(f"Updated OPC UA SensorData: {sensor_json_string}")
                            response_payload = {"status": "success", "message": "Sensor data updated on OPC UA server", "data": sensor_data_dict}
                        else:
                            print("Error: sensordata_var_node is not initialized.")
                            response_payload = {"status": "error", "message": "OPC UA sensor node not available"}
                    else:
                        response_payload = {"status": "error", "message": "Failed to get sensor data or get_sensor_data returned None"}
                except Exception as e:
                    print(f"Exception in get_sensor_data: {str(e)}")
                    response_payload = {"status": "error", "message": f"Exception in get_sensor_data: {str(e)}"}
                
                conn.sendall(json.dumps(response_payload).encode())
                print(f"Sent GetSensor response over TCP to {addr}: {json.dumps(response_payload)}")

            else:
                error_msg = json.dumps({"error": f"Unknown command: {command}"})
                conn.sendall(error_msg.encode())
                print(f"Sent unknown command error over TCP to {addr}")

    except ConnectionResetError:
        print(f"TCP connection reset by {addr}")
    except Exception as e:
        print(f"Error in TCP handler for {addr}: {e}")
    finally:
        conn.close()
        print(f"TCP Connection with {addr} closed.")

def start_tcp_command_server():
    global opcua_server  # To allow graceful shutdown check
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((TCP_HOST, TCP_PORT))
    server_socket.listen()
    print(f"TCP Command Server listening on {TCP_HOST}:{TCP_PORT}")

    try:
        while True:
            # Check if OPC UA server is still running, to allow graceful shutdown
            if opcua_server and not opcua_server.running:
                print("TCP Server: OPC UA server stopping, shutting down TCP server.")
                break
            try:
                server_socket.settimeout(1.0)  # Timeout to allow checking opcua_server.running
                conn, addr = server_socket.accept()
                server_socket.settimeout(None)  # Reset timeout after connection
                client_thread = threading.Thread(target=handle_tcp_client, args=(conn, addr), daemon=True)
                client_thread.start()
            except socket.timeout:
                continue  # Continue to check opcua_server.running
            except Exception as e:
                if opcua_server and opcua_server.running:  # Only log if not shutting down
                    print(f"Error accepting TCP connections: {e}")
                break  # Exit loop on other errors
    finally:
        server_socket.close()
        print("TCP Command Server stopped.")

def periodic_sensor_update_task():
    global sensordata_var_node, opcua_server
    while True:
        if opcua_server and not opcua_server.running:
            print("Periodic task: Server stopping, exiting update loop.")
            return  # Exit thread if OPC UA server stops

        if sensordata_var_node:
            try:
                sensor_data_dict = get_sensor_data()
                if sensor_data_dict:
                    sensor_json_string = json.dumps(sensor_data_dict)
                    sensordata_var_node.set_value(sensor_json_string)
                else:
                    error_msg = json.dumps({"error": "Periodic: Failed to get sensor data"})
                    sensordata_var_node.set_value(error_msg)
                    print(f"Periodic update: {error_msg}")
            except Exception as e:
                error_msg = json.dumps({"error": f"Periodic Exception: {str(e)}"})
                if sensordata_var_node:  # Check if node still exists
                    sensordata_var_node.set_value(error_msg)
                print(f"Error in periodic_sensor_update_task: {e}")
        
        # Wait for 60 seconds, but check for server shutdown every second
        for _ in range(60):
            time.sleep(1)
            if opcua_server and not opcua_server.running:
                print("Periodic task: Server stopping during wait, exiting update loop.")
                return

def main():
    global sensordata_var_node, opcua_server

    opcua_server = Server()
    opcua_server.set_endpoint("opc.tcp://0.0.0.0:4840/wnr/server/")
    opcua_server.set_server_name("WNR OPC UA Server")

    # Setup namespace
    uri = "http://watersensor.example.com"
    idx = opcua_server.register_namespace(uri)

    objects_node = opcua_server.get_objects_node()
    device_object = objects_node.add_object(idx, "WNRDevice")

    # String data variable for sensor data (only this is exposed via OPC UA now)
    sensordata_var_node = device_object.add_variable(idx, "SensorData", json.dumps({"info": "No data yet"}), ua.VariantType.String)

    opcua_server.start()
    print(f"OPC UA Server started at {opcua_server.endpoint.geturl()}")

    if 'colors_df' not in globals() or colors_df_for_capture is None:
        print("Warning: colors.csv might not have been loaded correctly by getcolor.py.")
  
    # Start periodic sensor update thread
    update_thread = threading.Thread(target=periodic_sensor_update_task, daemon=True)
    update_thread.start()
    print("Periodic sensor update thread started.")

    # Start TCP command server thread
    tcp_server_thread = threading.Thread(target=start_tcp_command_server, daemon=True)
    tcp_server_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping servers (KeyboardInterrupt)...")
    finally:
        if opcua_server:
            print("Stopping OPC UA server...")
            opcua_server.stop()  # This should signal daemon threads to also wrap up
            print("OPC UA Server stopped.")
        print("Application shutdown complete.")

if __name__ == "__main__":
    main()