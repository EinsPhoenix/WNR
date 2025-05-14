from math import sqrt, atan2, cos, sin
from socket import socket, AF_INET, SOCK_STREAM
from json import dumps, loads
from time import sleep


class Robot:
    def __init__(self, speed: int = 500) -> None:
        """
        Initialize the Robot class.

        Args:
            speed (int, optional): The speed of the robot. Default is 500.
        """
        if speed > 2000:
            speed = 2000
        elif speed < 100:
            speed = 100
        self.speed = speed

    def calibrate_camera(self) -> None:
        """Calibrate the camera by moving the robot to specific position."""
        calibrate_positions: list[tuple[int, int]] = [(0, -300), (200, -200), (300, 0), (200, 200), (0, 300)]
        for i, pos in enumerate(calibrate_positions):
            self.move_to_position(*pos)
            while self.send_message({"type": "calibrate", "payload": {"number": i, "robot_pos": {"x": pos[0], "y": pos[1]}}})["status"] == "error":
                sleep(0.5)

    def send_message(self, message_to_send: str, host: str = "localhost", port: int = 65432) -> None:
        """
        Send a command to the rasberry pi, which controls the camera.

        Args:
            message_to_send (str): The message to send.
            host (str, optional): The host address. Default is "localhost".
            port (int, optional): The port number. Default is 65432.
        """
        try:
            with socket(AF_INET, SOCK_STREAM) as s:
                s.connect((host, port))
                s.sendall(dumps(message_to_send).encode("utf-8"))
                response_data = s.recv(1024)
                response = loads(response_data.decode("utf-8"))
                print(f"Received response: {response}")
                return response
        except ConnectionRefusedError:
            print("Connection refused. Please check if the server is running.")
        except Exception as e:
            print(f"An error occurred: {e}")
                

    def move_to_position(self, target_x: float, target_y: float, target_z: float | None = None, target_r: float | None = None) -> None:
        """
        Move the robot to the specified position.

        Args:
            x (float): The target x position.
            y (float): The target y position.
            z (float | None, optional): The target z position. Default is None.
            r (float | None, optional): The target r position. Default is None.
        """
        current_x = 200
        current_y = 0
        current_z = 0
        current_r = 0
        if target_z is None:
            target_z = current_z
        if target_r is None:
            target_r = current_r
        measure_amount = int(self.speed / 10) + 1
        current_radius = sqrt(pow(current_x, 2) + pow(current_y, 2))
        target_radius = sqrt(pow(target_x, 2) + pow(target_y, 2))
        target_z += (target_radius - current_radius) / 4
        current_angle = atan2(current_y, current_x)
        target_angle = atan2(target_y, target_x)
        angle_diff = target_angle - current_angle
        radii = [current_radius + i * (target_radius - current_radius) / (measure_amount - 1) for i in range(measure_amount)]
        print(f"Moving to ({target_x}, {target_y}, {target_z}) with speed {self.speed}")
        for i in range(1, measure_amount):
            angle = current_angle + angle_diff / (measure_amount - 1) * i
            x = radii[i] * cos(angle)
            y = radii[i] * sin(angle)
            z = current_z + (target_z - current_z) / (measure_amount - 1) * i
            print(f"Step {i}: Moving to ({x}, {y}, {z})")


if __name__ == "__main__":
    robot = Robot()
    robot.move_to_position(300, 0)