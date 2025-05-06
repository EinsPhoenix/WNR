import time
import json
import threading
from opcua import Server, ua

# Import functions from other files
from getcolor import capture_part, csv_data as colors_df_for_capture # Ensure csv_data is loaded
from getsensordata import get_sensor_data

# Global OPC UA node variables
takepicture_var_node = None
getsensor_var_node = None
color_var_node = None
sensordata_var_node = None
opcua_server = None

class SubHandler(object):
    """
    Subscription Handler. To receive events from server for a subscription.
    """
    def datachange_notification(self, node, val, data):
        global takepicture_var_node, getsensor_var_node, color_var_node, sensordata_var_node
        
        node_display_name = node.get_display_name().Text
        print(f"Data change on node '{node_display_name}': {val}")

        if node == takepicture_var_node and val is True:
            print("TakePicture event triggered. Calling capture_part...")
            try:
                color_data_dict = capture_part() 
                if color_data_dict:
                    color_json_string = json.dumps(color_data_dict)
                    color_var_node.set_value(color_json_string)
                    print(f"Updated ColorData: {color_json_string}")
                else:
                    error_msg = json.dumps({"error": "Failed to capture part or capture_part returned None"})
                    color_var_node.set_value(error_msg)
                    print(error_msg)
            except Exception as e:
                error_msg = json.dumps({"error": f"Exception in capture_part: {str(e)}"})
                color_var_node.set_value(error_msg)
                print(error_msg)
            finally:
                takepicture_var_node.set_value(False) 
                print("TakePicture reset to False.")

        elif node == getsensor_var_node and val is True:
            print("GetSensor event triggered. Calling get_sensor_data...")
            try:
                sensor_data_dict = get_sensor_data()
                if sensor_data_dict:
                    sensor_json_string = json.dumps(sensor_data_dict)
                    sensordata_var_node.set_value(sensor_json_string)
                    print(f"Updated SensorData: {sensor_json_string}")
                else:
                    error_msg = json.dumps({"error": "Failed to get sensor data or get_sensor_data returned None"})
                    sensordata_var_node.set_value(error_msg)
                    print(error_msg)
            except Exception as e:
                error_msg = json.dumps({"error": f"Exception in get_sensor_data: {str(e)}"})
                sensordata_var_node.set_value(error_msg)
                print(error_msg)
            finally:
                getsensor_var_node.set_value(False) 
                print("GetSensor reset to False.")

    def event_notification(self, event):
        print("New event: ", event)

def periodic_sensor_update_task():
    global sensordata_var_node
    while True:
        if sensordata_var_node:
            print("Periodic task: Calling get_sensor_data...")
            try:
                sensor_data_dict = get_sensor_data()
                if sensor_data_dict:
                    sensor_json_string = json.dumps(sensor_data_dict)
                    sensordata_var_node.set_value(sensor_json_string)
                    print(f"Periodic update: SensorData updated with: {sensor_json_string}")
                else:
                    error_msg = json.dumps({"error": "Periodic: Failed to get sensor data"})
                    sensordata_var_node.set_value(error_msg)
                    print(f"Periodic update: {error_msg}")
            except Exception as e:
                error_msg = json.dumps({"error": f"Periodic Exception: {str(e)}"})
                sensordata_var_node.set_value(error_msg)
                print(f"Error in periodic_sensor_update_task: {e}")
        

        for _ in range(60):
            time.sleep(1)
            
            if not opcua_server or not opcua_server.running:
                 print("Periodic task: Server stopping, exiting update loop.")
                 return


def main():
    global takepicture_var_node, getsensor_var_node, color_var_node, sensordata_var_node, opcua_server

    opcua_server = Server()
    opcua_server.set_endpoint("opc.tcp://0.0.0.0:4840/wnr/server/")
    opcua_server.set_server_name("WNR OPC UA Server")

    # Setup namespace
    uri = "http://watersensor.example.com"
    idx = opcua_server.register_namespace(uri)

    objects_node = opcua_server.get_objects_node()
    device_object = objects_node.add_object(idx, "WNRDevice")

    # Boolean control variables
    takepicture_var_node = device_object.add_variable(idx, "TakePicture", False, ua.VariantType.Boolean)
    takepicture_var_node.set_writable()

    getsensor_var_node = device_object.add_variable(idx, "GetSensor", False, ua.VariantType.Boolean)
    getsensor_var_node.set_writable()

    # String data variables
    color_var_node = device_object.add_variable(idx, "ColorData", json.dumps({"info": "No data yet"}), ua.VariantType.String)
    sensordata_var_node = device_object.add_variable(idx, "SensorData", json.dumps({"info": "No data yet"}), ua.VariantType.String)

    # Create subscription for data changes
    handler = SubHandler()
    subscription = opcua_server.create_subscription(500, handler) # 500 ms publishing interval
    subscription.subscribe_data_change(takepicture_var_node)
    subscription.subscribe_data_change(getsensor_var_node)

    opcua_server.start()
    print(f"OPC UA Server started at {opcua_server.endpoint.geturl()}")

    
    if 'colors_df' not in globals() or colors_df_for_capture is None:
        print("Warning: colors.csv might not have been loaded correctly by getcolor.py.")
  

    update_thread = threading.Thread(target=periodic_sensor_update_task, daemon=True)
    update_thread.start()
    print("Periodic sensor update thread started.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping server...")
    finally:
        if opcua_server:
            opcua_server.stop()
            print("Server stopped.")
       

if __name__ == "__main__":
    main()