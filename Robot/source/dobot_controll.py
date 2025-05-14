from asyncio import create_task, run
from pydobot import Dobot
from time import sleep
from math import sqrt, pow


class Robot:
    def __init__(self, speed: int = 500) -> None:
        """
        Initialize the Robot class.

        Args:
            speed (int, optional): The speed of the robot. Default is 500.
        """
        self.device = Dobot(port="COM5", verbose=False)
        if speed > 2000:
            speed = 2000
        self.device.speed(speed, speed)

    def __del__(self):
        """
        Destructor for the Robot class. Disconnects the Dobot device.
        """
        self.disconnect()

    def disconnect(self) -> None:
        """
        Disconnect the Dobot device.
        """
        self.device.move_to(300, 0, 0, 0, wait=True)
        self.device.close()

    async def calibrate_camera(self) -> None:
        """
        Calibrate the camera by moving the robot to specific position.
        """
        self.device.move_to(0, -300, 0, 0, wait=True)
        sleep(2)
        self.device.move_to(200, -200, 0, 0, wait=True)
        sleep(2)
        self.device.move_to(300, 0, 0, 0, wait=True)
        sleep(2)
        self.device.move_to(200, 200, 0, 0, wait=True)
        sleep(2)
        self.device.move_to(0, 300, 0, 0, wait=True)
        sleep(2)

    def get_current_robot_pos(self) -> tuple[int, int, int, int]:
        """
        Get the current x, y, z and r position of the robot.

        Returns:
            tuple[int, int, int, int]: The current x, y, z, and r positions of the robot.
        """
        (x, y, z, r, j1, j2, j3, j4) = self.device.pose()
        return (x, y, z, r)

    def move_to_position(self, target_x: float, target_y: float, target_z: float = 0, target_r: float = 0) -> None:
        """
        Move the robot to the specified position.

        Args:
            x (float): The target x position.
            y (float): The target y position.
            z (float, optional): The target z position. Default is 0.
            r (float, optional): The target r position. Default is 0.
        """
        current_x, current_y, current_z, current_r = self.get_current_robot_pos()
        start = (current_x, current_y)
        end = (target_x, target_y)
        def radius(p):
            return sqrt(pow(p[0], 2) + pow(p[1], 2))
        r_start = radius(start)
        r_end = radius(end)
        steps = 10
        radii = [r_start + i * (r_end - r_start) / (steps - 1) for i in range(steps)]
        dir_x = end[0] - start[0]
        dir_y = end[1] - start[1]
        def find_point_with_radius(r_target, iterations=20):
            low = 0.0
            high = 1.0
            for _ in range(iterations):
                mid = (low + high) / 2
                x = start[0] + mid * dir_x
                y = start[1] + mid * dir_y
                r = radius((x, y))
                if r < r_target:
                    low = mid
                else:
                    high = mid
            x = start[0] + mid * dir_x
            y = start[1] + mid * dir_y
            return (x, y)
        points = [find_point_with_radius(r) for r in radii]
        x_vals = [p[0] for p in points]
        y_vals = [p[1] for p in points]
        for i in range(steps):
            print(f"Moving to point {i}: ({x_vals[i]}, {y_vals[i]})")
            self.device.move_to(x_vals[i], y_vals[i], target_z, target_r, wait=True)
            sleep(0.1)
        

async def main():
    robot = Robot(1000)
    robot.move_to_position(0, -300)
    # calibration = create_task(robot.calibrate_camera())
    # await calibration

if __name__ == "__main__":
    run(main())