from math import sqrt
from time import sleep

from communication import Communication
from dobot_control import DoBotControl

class AutomatedSorter(Communication, DoBotControl):
    def __init__(self, speed: int = 500, host: str = "localhost", port: int = 65432) -> None:
        """
        Initialize the AutomatedSorter class.

        Args:
            speed (int, optional): The speed of the robot. Default is 500.
            host (str, optional): The host address for communication. Default is "localhost".
            port (int, optional): The port number for communication. Default is 65432.
        """
        super().__init__(speed=speed)
        self.host = host
        self.port = port

    def calibrate_camera(self) -> None:
        """Calibrate the camera by moving the robot to specific position."""
        calibrate_positions: list[tuple[int, int]] = [(50, -250), (200, -200), (300, 0), (200, 200), (50, 250)]
        for i, pos in enumerate(calibrate_positions):
            self.move_to_position(*pos)
            sleep(0.5)
            while self.send_message({"type": "calibrate", "payload": {"number": i, "robot_pos": {"x": pos[0], "y": pos[1]}}})["status"] == "error":
                sleep(0.5)
        self.send_message({"type": "calibrate", "payload": {"finish": True}})

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
        self.suck(True)
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
        self.suck(False)
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


if __name__ == "__main__":
    sorter = AutomatedSorter()
    sorter.calibrate_camera()
    sorter.start_sorting()