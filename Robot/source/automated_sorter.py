from math import sqrt

from dobot_control import DoBotControl
from utils.communication import send_message

class AutomatedSorter(DoBotControl):
    def __init__(self, main_window: object, speed: int = 500) -> None:
        """
        Initialize the AutomatedSorter class.

        Args:
            main_window (object): The main window object.
            speed (int, optional): The speed of the robot. Default is 500.
            host (str, optional): The host address for communication. Default is "localhost".
            port (int, optional): The port number for communication. Default is 65432.
        """
        super().__init__(main_window, speed=speed)
        self.main_window = main_window

    def get_next_block(self) -> tuple[float, float, str]:
        """
        Get the next block position and color from the pi.

        Returns:
            tuple[float, float, str]: The x and y position of the block and its color.
        """
        response = send_message(self, {"type": "color"})
        print(response)
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
        storage_factor: int = 15
        self.move_to_position(block_x, block_y, storage_factor)
        self.move_to_position(block_x, block_y, 0)
        self.bot.suck(True)
        self.move_to_position(block_x, block_y, storage_factor)
        target_storage = getattr(self, f"{color}_storage")
        storage_x, storage_y = target_storage[0]
        i = -1
        match color:
            case "yellow":
                i = 0
            case "red":
                i = 1
            case "blue":
                i = 2
            case "green":
                i = 3
        storage_level = self.main_window.storage_counts[i]
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
        self.bot.suck(False)
        self.move_to_position(storage_x, storage_y, storage_z + storage_factor)
        self.main_window.storage_counts[i] += 1
        self.move_to_position(target_x, target_y, storage_z + storage_factor)
        self.move_home()