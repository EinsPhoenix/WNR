import asyncio
from asyncio import create_task
from math import sqrt, pow, atan2, cos, sin

from pydobot import Dobot
from pydobot.enums import PTPMode

from utils.config import read_config
from utils.function import increase_storage


class CustomDobot(Dobot):
    def __init__(self, port) -> None:
        """
        Initialize the CustomDobot class.

        Args:
            port (str): The port to connect to the Dobot device.
        """
        super().__init__(port = port, verbose = False)

    # FIXME: Kontrollieren, ob das der beste Mode ist oder ob andere besser funktionieren
    def move_to(self, x, y, z, r, mode = PTPMode.MOVJ_XYZ, wait = True) -> None:
        """
        Move the Dobot to a specified position.

        Args:
            x (float): The x-coordinate.
            y (float): The y-coordinate.
            z (float): The z-coordinate.
            r (float): The rotation angle.
            mode (int, optional): The movement mode. Defaults to PTPMode.MOVJ_XYZ.
            wait (bool, optional): Whether to wait for the movement to complete. Defaults to True.
        """
        self._set_ptp_cmd(x, y, z, r, mode = mode, wait = wait)


class DoBotControl():
    def __init__(self, main_window: object, homeX: float = 300, homeY: float = 0, homeZ: float = 0, speed: int = 500) -> None:
        """
        Initialize the DoBotControl class.

        Args:
            main_window (object): The main window object.
            homeX (float, optional): The X coordinate of the home position. Default is 300.
            homeY (float, optional): The Y coordinate of the home position. Default is 0.
            homeZ (float, optional): The Z coordinate of the home position. Default is 0.
            speed (int, optional): The speed of the robot. Default is 500.
        """
        self.main_window = main_window
        self.homeX: float = homeX
        self.homeY: float = homeY
        self.homeZ: float = homeZ
        self.bot = None
        self.connected: bool = False
        self.speed: int = speed
        self.color_list: list[str] = ["blue", "green", "red", "yellow"]
        self.green_storage: list[tuple[float, float], int] = [(0, 300)]
        self.blue_storage: list[tuple[float, float], int] = [(50, 300)]
        self.red_storage: list[tuple[float, float], int] = [(0, -300)]
        self.yellow_storage: list[tuple[float, float], int] = [(50, -300)]

    def __del__(self) -> None:
        """Destructor for the DoBotControl class. Disconnects the Dobot device."""
        create_task(self.dobot_disconnect())

    async def dobot_connect(self) -> None:
        """Attempts to connect to the Dobot device."""
        try:
            self.bot = CustomDobot(port = read_config(self.main_window)["robot"]["com_port"], verbose=False)
            self.connected = True
            self.set_speed(self.speed)
        except:
            self.bot = None
            self.connected = False
        return self.connected

    async def dobot_disconnect(self) -> None:
        try:
            if not self.bot is None:
                self.move_home()
                self.bot.close()
            self.connected = False
        except:
            pass
        return self.connected

    def set_speed(self, speed: int) -> None:
        """
        Set the speed of the robot.

        Args:
            speed (int): The speed to set for the robot.
        """
        if speed > 2000:
            speed = 2000
        elif speed < 100:
            speed = 100
        self.speed: int = speed
        self.bot.speed(speed, speed)

    def move_home(self) -> None:
        """Move the robot to the home position."""
        self.move_to_position(self.homeX, self.homeY, self.homeZ, 0)

    def get_current_robot_pos(self) -> tuple[float, float, float, float]:
        """
        Get the current position of the robot.

        Returns:
            tuple[float, float, float, float]: The current position (x, y, z, r) of the robot.
        """
        pos = self.bot.pose()
        return pos[0], pos[1], pos[2], pos[3]

    def move_to_position(self, x: float, y: float, z: float | None = None, r: float | None = None) -> None:
        """
        Move the robot to a specified position.

        Args:
            x (float): The X coordinate of the target position.
            y (float): The Y coordinate of the target position.
            z (float | None, optional): The Z coordinate of the target position.
            r (float | None, optional): The rotation angle of the head.
        """
        _, _, current_z, current_r = self.get_current_robot_pos()
        if z is None:
            z = current_z
        if r is None:
            r = current_r
        self.bot.move_to(x, y, z, r)

    def move_block_to_storage_manual_mode(self, color: str) -> None:
        """
        Move the robot to the storage position based on the color.

        Args:
            color (str): The color of the block.
        """
        # FIXME: Check if hight is good
        storage_factor: int = 30
        storage_x, storage_y = getattr(self, f"{color}_storage")
        storage_level: int = self.main_window.storage_counts[self.color_list.index(color)]
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
        increase_storage(self.main_window, self.color_list.index(color))
        self.move_to_position(target_x, target_y, storage_z + storage_factor)
        self.move_home()


if __name__ == "__main__":
    from time import sleep
    from keyboard import is_pressed, add_hotkey

    async def main():
        dobot_control = DoBotControl()
        await dobot_control.dobot_connect()
        x, y, z, r = dobot_control.get_current_robot_pos()
        print("Control the robot with the following keys:")
        print("    WASD: Move in X/Y direction")
        print("    up/down: Move up/down in Z direction")
        print("    left/right: Rotate in R direction")
        print("    Space: Toggle suction cup")
        print("    H: Move to home position")
        print("    Sort cubes to storage:")
        print("        1: Blue")
        print("        2: Green")
        print("        3: Red")
        print("        4: Yellow")
        print("    Esc: Exit the control loop")
        add_hotkey("+", lambda: dobot_control.bot.suck(True))
        add_hotkey("-", lambda: dobot_control.bot.suck(False))
        add_hotkey("h", lambda: dobot_control.move_home())
        add_hotkey("1", lambda: dobot_control.move_block_to_storage_manual_mode("blue"))
        add_hotkey("2", lambda: dobot_control.move_block_to_storage_manual_mode("green"))
        add_hotkey("3", lambda: dobot_control.move_block_to_storage_manual_mode("red"))
        add_hotkey("4", lambda: dobot_control.move_block_to_storage_manual_mode("yellow"))
        add_hotkey("esc", lambda: create_task(dobot_control.dobot_disconnect()))
        # TODO: Check if this feels good (change step/sleep)
            # Vielleicht kann ich das auch so umschreiben, dass WASD nicht mit dem Grid funktioniert, sondern "aus der Sicht der Arms" bewegt wird
                # w: weg von (0, 0) s: zu (0, 0) a/d: links/rechts drehen
                # Vielleicht kann ich auch beide modi implementieren
        step = 1
        while dobot_control.connected:
            try:
                if is_pressed("w"):
                    x += step
                if is_pressed("s"):
                    x -= step
                if is_pressed("a"):
                    y -= step
                if is_pressed("d"):
                    y += step
                if is_pressed("up"):
                    z += step
                if is_pressed("down"):
                    z -= step
                if is_pressed("left"):
                    r -= step
                if is_pressed("right"):
                    r += step
                # FIXME: Move
                sleep(0.1)
            except:
                pass

    asyncio.run(main())