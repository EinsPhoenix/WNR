from time import sleep
from pydobot import Dobot


class Robot:
    def __init__(self, x_grid_pos: str, y_grid_pos: int) -> None:
        """
        Initialize the Robot class.

        Args:
            x_pos (str): The start x position of the robot as char "A, B, C".
            y_pos (int): The start y position of the robot as int "1, 2, 3".
        """
        self.x_grid_pos = x_grid_pos
        self.y_grid_pos = y_grid_pos
        self.device = Dobot(port="COM5", verbose=False)
        self.device.speed(500, 500)
        # self.device.speed(2000, 2000)
        (self.start_x, self.start_y, self.start_z, self.start_r, j1, j2, j3, j4) = self.device.pose()
        self.device.move_to(self.start_x, self.start_y, self.start_z + 30, self.start_r, wait = True)

    def get_current_robot_pos(self) -> tuple[int, int, int, int]:
        """
        Get the current x, y, z and r position of the robot.

        Returns:
            tuple[int, int, int, int]: The current x, y, z, and r positions of the robot.
        """
        (x, y, z, r, j1, j2, j3, j4) = self.device.pose()
        return (x, y, z, r)

    def move_to_grid_pos(self, x_grid_pos: str, y_grid_pos: int) -> None:
        """
        Move the robot to the specified grid position.

        Args:
            x_grid_pos (str): The target x position on the grid for the robot.
            y_grid_pos (int): The target y position on the grid for the robot.
        """
        x_coord = ord(x_grid_pos) - ord(self.x_grid_pos)
        y_coord = y_grid_pos - self.y_grid_pos
        # TODO: If y = M or more we need to move y first
        # y movement
        x, y, z, r = self.get_current_robot_pos()
        print(f"x: {x}, y: {y}, z: {z}, r: {r}")
        self.device.move_to(x + x_coord * 15, y + y_coord * 20, z, r, wait=True)
        x, y, z, r = self.get_current_robot_pos()
        print(f"x: {x}, y: {y}, z: {z}, r: {r}")
        self.x_grid_pos = x_grid_pos
        self.y_grid_pos = y_grid_pos
        sleep(2.5)

# def register_brick_position(x_pos: str, y_pos: int) -> None:
#     """
#     Register the position of the brick in the database.

#     Args:
#         x_pos (str): The x position of the brick as char "A, B, C".
#         y_pos (int): The y position of the brick as int "1, 2, 3".
#     """
    

if __name__ == "__main__":
    # Set up the robot at (O, 16) directly over the hole 
    robot = Robot("O", 16)
    robot.move_to_grid_pos("O", 7)
    robot.device.move_to(robot.start_x, robot.start_y, robot.start_z, robot.start_r, wait=True)
    # robot.device.move_to(robot.start_x, robot.start_y, robot.start_z + 10, robot.start_r, wait=True)
    robot.device.close()

# TODO: Wenn ich nach x:215 y:0 z: 10 gehe sollte ich über (O, 16) rauskommen egal von wo ich starte
    # HOFFE ICH
"""
Start pos (O, 16)
(venv) PS C:\Users\Jan\Documents\Projects\GitRepos\WNR\tests> py .\move_brick.py
x: 215.523681640625, y: 0.0, z: 4.821693420410156, r: 0.0
Response: AA AA:34:10:0:0F 86 57 43 00 00 34 C3 48 4B 9A 40 00 00 00 00 9E 78 1F C2 E3 F3 80 42 4B 3B AA 41 9E 78 1F 42:236
x: 215.52366638183594, y: -180.0, z: 4.821689605712891, r: 0.0

# Start pos (O, 18)
(venv) PS C:\Users\Jan\Documents\Projects\GitRepos\WNR\tests> py .\move_brick.py
x: 235.2189178466797, y: 0.0, z: -8.969039916992188, r: 0.0
Response: AA AA:34:10:0:0A 38 6B 43 FF FF 2A C3 40 81 0F C1 00 00 00 00 E2 10 10 C2 49 43 93 42 DF 37 95 41 E2 10 10 42:53
x: 235.21890258789062, y: -170.99998474121094, z: -8.96905517578125, r: 0.0
"""