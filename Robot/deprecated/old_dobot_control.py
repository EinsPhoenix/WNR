from json import dumps, loads
from math import sqrt, atan2, cos, sin
from pydobot import Dobot
from socket import socket, AF_INET, SOCK_STREAM
from time import sleep


class Robot:
    def __init__(self, speed: int = 500,  host: str = "localhost", port: int = 65432) -> None:
        """
        Initialize the Robot class.

        Args:
            speed (int, optional): The speed of the robot. Default is 500.
            host (str, optional): The host address. Default is "localhost".
            port (int, optional): The port number. Default is 65432.
        """
        self.device = Dobot(port="COM6", verbose=False)
        if speed > 2000:
            speed = 2000
        elif speed < 100:
            speed = 100
        self.speed: int = speed
        self.device.speed(speed, speed)
        self.device.move_to(250, 0, 0, 0, wait=True)
        self.host = host
        self.port = port
        # FIXME: Check if pos is good
        self.green_storage: list[tuple[float, float], int] = [(0, 300), 0]
        self.blue_storage: list[tuple[float, float], int] = [(50, 300), 0]
        self.red_storage: list[tuple[float, float], int] = [(0, -300), 0]
        self.yellow_storage: list[tuple[float, float], int] = [(50, -300), 0]

    def __del__(self) -> None:
        """Destructor for the Robot class. Disconnects the Dobot device."""
        self.disconnect()

    def disconnect(self) -> None:
        """Disconnect the Dobot device."""
        try:
            self.move_to_position(300, 0, 50)
            self.device.close()
        except:
            pass

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

    def calibrate_camera(self) -> None:
        """Calibrate the camera by moving the robot to specific position."""
        calibrate_positions: list[tuple[int, int]] = [(50, -250, 10), (200, -200, 15), (300, 0, 20), (200, 200, 15), (50, 250, 10)]
        for i, pos in enumerate(calibrate_positions):
            self.move_to_position(*pos)
            sleep(0.5)
            while self.send_message({"type": "calibrate", "payload": {"number": i, "robot_pos": {"x": pos[0], "y": pos[1]}}})["status"] == "error":
                sleep(0.5)
        self.send_message({"type": "calibrate", "payload": {"finish": True}})

    def get_current_robot_pos(self) -> tuple[float, float, float, float]:
        """
        Get the current x, y, z and r position of the robot.

        Returns:
            tuple[float, float, float, float]: The current x, y, z, and r positions of the robot.
        """
        (x, y, z, r, j1, j2, j3, j4) = self.device.pose()
        return x, y, z, r

    def move_to_position(self, target_x: float, target_y: float, target_z: float | None = None, target_r: float | None = None) -> None:
        """
        Move the robot to the specified position.

        Args:
            x (float): The target x position.
            y (float): The target y position.
            z (float | None, optional): The target z position. Default is None.
            r (float | None, optional): The target r position. Default is None.
        """
        current_x, current_y, current_z, current_r = self.get_current_robot_pos()
        if target_z is None:
            target_z = current_z
        if target_r is None:
            target_r = current_r
        # measure_amount = int(self.speed / 10) + 1
        measure_amount: int = 3
        current_radius: float = sqrt(pow(current_x, 2) + pow(current_y, 2))
        target_radius: float = sqrt(pow(target_x, 2) + pow(target_y, 2))
        target_z += (target_radius - current_radius) / 10
        current_angle: float = atan2(current_y, current_x)
        target_angle: float = atan2(target_y, target_x)
        angle_diff: float = target_angle - current_angle
        radii: list[float] = [current_radius + i * (target_radius - current_radius) / (measure_amount - 1) for i in range(measure_amount)]
        # print(f"Moving from ({current_x}, {current_y}, {current_z}) to ({target_x}, {target_y}, {target_z})")
        for i in range(1, measure_amount):
            angle: float = current_angle + angle_diff / (measure_amount - 1) * i
            x: float = radii[i] * cos(angle)
            y: float = radii[i] * sin(angle)
            z: float = current_z + (target_z - current_z) / (measure_amount - 1) * i
            r: float = current_r + (target_r - current_r) / (measure_amount - 1) * i
            # print(f"Moving to: ({x:.2f}, {y:.2f}, {z:.2f})")
            if i == measure_amount - 1:
                self.device.move_to(x, y, z, r, wait=True)
            else:
                self.device.move_to(x, y, z, r, wait=False)
            # sleep(0.01)

    def get_next_block(self) -> tuple[float, float, str]:
        """
        Get the next block position and color from the pi.
        """
        response = self.send_message({"type": "color"})
        for object in response["objects"]:
            if object["robot_pos"]["x"] > 55:
                if object["bgr"] == "255,0,0":
                    color = "blue"
                elif object["bgr"] == "0,255,0":
                    color = "green"
                elif object["bgr"] == "0,0,255":
                    color = "red"
                elif object["bgr"] == "0,255,255":
                    color = "yellow"
                else:
                    raise ValueError(f"Unknown color: {object['bgr']}")
                return object["robot_pos"]["x"], object["robot_pos"]["y"], color
        return 0, 0, "none"

    def move_block_to_storage(self, block_x: float, block_y: float, color: str) -> None:
        """
        Move the robot to the storage position based on the color.

        Args:
            block_x (float): The x position of the block.
            block_y (float): The y position of the block.
            color (str): The color of the block.
        """
        # FIXME: Check if hight is good
        storage_factor: int = 30
        self.move_to_position(block_x, block_y, storage_factor)
        self.move_to_position(block_x, block_y, 0)
        self.device.suck(True)
        self.move_to_position(block_x, block_y, storage_factor)
        target_storage = getattr(self, f"{color}_storage")
        storage_x, storage_y = target_storage[0]
        storage_level: int = target_storage[1]
        storage_z: float = storage_level * storage_factor
        storage_radius: float = sqrt(pow(storage_x, 2) + pow(storage_y, 2))
        target_radius: float = storage_radius - 50
        scale: float = target_radius / storage_radius
        storage_x: float = storage_x * pow(0.98, storage_level)
        storage_y: float = storage_y * pow(0.98, storage_level)
        target_x: float = storage_x * scale
        target_y: float = storage_y * scale
        self.move_to_position(target_x, target_y, storage_z + storage_factor)
        self.move_to_position(storage_x, storage_y, storage_z + storage_factor)
        self.move_to_position(storage_x, storage_y, storage_z)
        self.device.suck(False)
        self.move_to_position(storage_x, storage_y, storage_z + storage_factor)
        getattr(self, f"{color}_storage")[1] += 1
        self.move_to_position(target_x, target_y, storage_z + storage_factor)

    def start_sorting(self) -> None:
        """Start the sorting process."""
        while True:
            block_x, block_y, color = self.get_next_block()
            if color == "none":
                print("No more blocks to sort.")
                break
            print(f"Moving block at ({block_x}, {block_y}) with color {color} to storage.")
            self.move_block_to_storage(block_x, block_y, color)


def main() -> None:
    robot = Robot(2000)
    # robot.calibrate_camera()
    while True:
        command = input("Enter command (move, pick, quit): ")
        if command == "move":
            x = float(input("Enter x: "))
            y = float(input("Enter y: "))
            z = float(input("Enter z: "))
            robot.move_to_position(x, y, z)
            robot.move_to_position(300, 0, 50)
        elif command == "pick":
            color = input("Enter color (green, blue, red, yellow): ")
            block_x = 300
            block_y = 0
            robot.move_block_to_storage(block_x, block_y, color)
            robot.move_to_position(300, 0, 50)
        elif command == "quit":
            robot.disconnect()
            break
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()