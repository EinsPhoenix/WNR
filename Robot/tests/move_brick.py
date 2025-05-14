from time import sleep
from pydobot import Dobot


class Robot:
    def __init__(self, x_grid_pos: str, y_grid_pos: int, speed: int = 500) -> None:
        """
        Initialize the Robot class.

        Args:
            x_pos (str): The start x position of the robot as char "A, B, C".
            y_pos (int): The start y position of the robot as int "1, 2, 3".
            speed (int, optional): The speed of the robot. Default is 500.
        """
        self.x_grid_pos = x_grid_pos
        self.y_grid_pos = y_grid_pos
        self.x_step_mm = 20
        self.y_step_mm = 20
        # Move to P10: ca. O10 (20, 5) and (5, 20) (-145, -375, 0)
        self.x_step_vector = (20, 5)
        self.y_step_vector = (10, 20)
        self.device = Dobot(port="COM5", verbose=False)
        if speed > 2000:
            speed = 2000
        self.device.speed(speed, speed)
        (self.start_x, self.start_y, self.start_z, self.start_r, j1, j2, j3, j4) = self.device.pose()
        self.grid_origin = (-220, -375, 0)
        self.device.move_to(self.start_x, self.start_y, 0, self.start_r, wait = True)

    def get_current_robot_pos(self) -> tuple[int, int, int, int]:
        """
        Get the current x, y, z and r position of the robot.

        Returns:
            tuple[int, int, int, int]: The current x, y, z, and r positions of the robot.
        """
        (x, y, z, r, j1, j2, j3, j4) = self.device.pose()
        return (x, y, z, r)

    def new_move_to_grid_pos(self, x_grid_pos: str, y_grid_pos: int) -> None:
        """
        Move the robot to the specified grid position.

        Args:
            x_grid_pos (str): The target x position on the grid for the robot.
            y_grid_pos (int): The target y position on the grid for the robot.
        """
        x_steps = ord(x_grid_pos.upper()) - ord('A')
        y_steps = y_grid_pos - 1
        x0, y0, z0 = self.grid_origin
        x_target = x0 + x_steps * self.x_step_vector[0] + y_steps * self.y_step_vector[0]
        print(f"x: {x0} + {x_steps} * {self.x_step_vector[0]} + {y_steps} * {self.y_step_vector[0]} = {x_target}")
        y_target = y0 + x_steps * self.x_step_vector[1] + y_steps * self.y_step_vector[1]
        print(f"y: {y0} + {x_steps} * {self.x_step_vector[1]} + {y_steps} * {self.y_step_vector[1]} = {y_target}")
        x, y, z, r = self.get_current_robot_pos()
        print(f"Moving to grid position: {x}, {y} -> ({x_target}, {y_target})")
        self.device.move_to(x_target, y_target, z0, r=0, wait=True)
        self.x_grid_pos = x_grid_pos
        self.y_grid_pos = y_grid_pos
        sleep(5)


if __name__ == "__main__":
    # Set up the robot at (P, 16) directly over the hole 
    robot = Robot("P", 16, 100)
    robot.new_move_to_grid_pos("P", 10)
    robot.device.move_to(230, robot.start_y, -30, robot.start_r, wait=True)
    robot.device.close()