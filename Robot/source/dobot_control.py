from math import sqrt, pow, atan2, cos, sin

import dll.DobotDllType as dobot_type


CON_STR = {
    dobot_type.DobotConnect.DobotConnect_NoError:  "DobotConnect_NoError",
    dobot_type.DobotConnect.DobotConnect_NotFound: "DobotConnect_NotFound",
    dobot_type.DobotConnect.DobotConnect_Occupied: "DobotConnect_Occupied"
}


class DoBotControl():
    def __init__(self, homeX: float = 300, homeY: float = 0, homeZ: float = 0, speed: int = 500) -> None:
        """
        Initialize the DoBotControl class.

        Args:
            homeX (float, optional): The X coordinate of the home position. Default is 300.
            homeY (float, optional): The Y coordinate of the home position. Default is 0.
            homeZ (float, optional): The Z coordinate of the home position. Default is 0.
            speed (int, optional): The speed of the robot. Default is 500.
            host (str, optional): The host address. Default is "localhost".
            port (int, optional): The port number. Default is 65432.
        """
        self.suction: bool = False
        self.api = dobot_type.load()
        self.homeX: float = homeX
        self.homeY: float = homeY
        self.homeZ: float = homeZ
        self.connected: bool = False
        self.dobot_connect()
        self.set_speed(speed)
        # FIXME: Check if pos is good
        self.green_storage: list[tuple[float, float], int] = [(0, 300), 0]
        self.blue_storage: list[tuple[float, float], int] = [(50, 300), 0]
        self.red_storage: list[tuple[float, float], int] = [(0, -300), 0]
        self.yellow_storage: list[tuple[float, float], int] = [(50, -300), 0]

    def __del__(self) -> None:
        """Destructor for the DoBotControl class. Disconnects the Dobot device."""
        self.dobot_disconnect()

    def dobot_connect(self, velocity: int = 100, acceleration: int = 100, joint_velocity: int = 200, joint_acceleration: int = 200) -> None:
        """
        Attempts to connect to the Dobot device.

        Args:
            velocity (int, optional): The velocity for the robot. Default is 100.
            acceleration (int, optional): The acceleration for the robot. Default is 100.
            joint_velocity (int, optional): The joint velocity for the robot. Default is 200.
            joint_acceleration (int, optional): The joint acceleration for the robot. Default is 200.
        """
        if not self.connected:
            state = dobot_type.ConnectDobot(self.api, "", 115200)[0]
            if state == dobot_type.DobotConnect.DobotConnect_NoError:
                dobot_type.SetQueuedCmdClear(self.api)
                dobot_type.SetHOMEParams(self.api, self.homeX, self.homeY, self.homeZ, 0, isQueued=1)
                dobot_type.SetPTPJointParams(self.api, joint_velocity, joint_acceleration, joint_velocity, joint_acceleration,
                    joint_velocity, joint_acceleration, joint_velocity, joint_acceleration, isQueued=1)
                dobot_type.SetPTPCommonParams(self.api, velocity, acceleration, isQueued=1)
                dobot_type.SetHOMECmd(self.api, temp=0, isQueued=1)
                self.connected = True
            else:
                raise ConnectionError(f"Unable to connect. Connect status: {CON_STR[state]}")

    def dobot_disconnect(self) -> None:
        self.move_home()
        dobot_type.DisconnectDobot(self.api)
        self.connected = False

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
        dobot_type.SetPTPCommonParams(self.api, self.speed, self.speed, isQueued=1)

    def move_home(self) -> None:
        """Move the robot to the home position."""
        dobot_type.SetQueuedCmdStopExec(self.api)
        dobot_type.SetQueuedCmdClear(self.api)
        self.move_to_position(self.homeX, self.homeY, self.homeZ, 0)

    def get_current_robot_pos(self) -> tuple[float, float, float, float]:
        """
        Get the current position of the robot.

        Returns:
            tuple[float, float, float, float]: The current position (x, y, z, r) of the robot.
        """
        pos = dobot_type.GetPose(self.api)
        return pos[0], pos[1], pos[2], pos[3]

    # FIXME: Wenn die so funktioniert, wie ich hoffe kann ich die andere Move Funktion in die Tonne kloppen
    def move_to_position(self, x: float, y: float, z: float | None = None, r: float | None = None) -> None:
        """
        Move the robot to a specified position.

        Args:
            x (float): The X coordinate of the target position.
            y (float): The Y coordinate of the target position.
            z (float | None, optional): The Z coordinate of the target position.
            r (float | None, optional): The rotation angle of the head.
        """
        current_x, current_y, current_z, current_r = self.get_current_robot_pos()
        if target_z is None:
            target_z = current_z
        if target_r is None:
            target_r = current_r
        lastIndex = dobot_type.SetPTPCmd(self.api, 0, x, y, z, r)[0]
        self.command_delay(lastIndex)

    def special_move_to_position(self, target_x: float, target_y: float, target_z: float | None = None, target_r: float | None = None) -> None:
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
        measure_amount = int(self.speed / 10) + 1
        current_radius: float = sqrt(pow(current_x, 2) + pow(current_y, 2))
        target_radius: float = sqrt(pow(target_x, 2) + pow(target_y, 2))
        target_z += (target_radius - current_radius) / 10
        current_angle: float = atan2(current_y, current_x)
        target_angle: float = atan2(target_y, target_x)
        angle_diff: float = target_angle - current_angle
        radii: list[float] = [current_radius + i * (target_radius - current_radius) / (measure_amount - 1) for i in range(measure_amount)]
        dobot_type.SetQueuedCmdClear(self.api)
        dobot_type.SetQueuedCmdStartExec(self.api)
        for i in range(1, measure_amount):
            angle: float = current_angle + angle_diff / (measure_amount - 1) * i
            x: float = radii[i] * cos(angle)
            y: float = radii[i] * sin(angle)
            z: float = current_z + (target_z - current_z) / (measure_amount - 1) * i
            r: float = current_r + (target_r - current_r) / (measure_amount - 1) * i
            dobot_type.SetPTPCmd(self.api, 1, x, y, z, r, isQueued=1)

    def command_delay(self, lastIndex: int) -> None:
        """
        Delays commands until the last command is executed.

        Args:
            lastIndex (int): The index of the last command.
        """
        dobot_type.SetQueuedCmdStartExec(self.api)
        while lastIndex > dobot_type.GetQueuedCmdCurrentIndex(self.api)[0]:
            # TODO: Testen, ob 200 zu viel sind oder ob ich auch weniger nehmen kann
            dobot_type.dSleep(200)
        dobot_type.SetQueuedCmdStopExec(self.api)

    def suck(self, on: bool) -> None:
        """
        Toggle the suction cup on or off.

        Args:
            on (bool): True to turn on the suction cup, False to turn it off.
        """
        if on and not self.suction:
            lastIndex = dobot_type.SetEndEffectorSuctionCup(self.api, True, True, isQueued=0)[0]
            self.suction = True
            self.command_delay(lastIndex)
        elif not on and self.suction:
            lastIndex = dobot_type.SetEndEffectorSuctionCup(self.api, True, False, isQueued=0)[0]
            self.suction = False
            self.command_delay(lastIndex)

    def move_block_to_storage_manual_mode(self, color: str) -> None:
        """
        Move the robot to the storage position based on the color.

        Args:
            color (str): The color of the block.
        """
        # FIXME: Check if hight is good
        storage_factor: int = 30
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
        self.move_home()


if __name__ == "__main__":
    from time import sleep
    from keyboard import is_pressed, add_hotkey
    dobot_control = DoBotControl()
    dobot_type.SetQueuedCmdClear(dobot_control.api)
    dobot_type.SetQueuedCmdStartExec(dobot_control.api)
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
    add_hotkey("space", lambda: dobot_control.suck(not dobot_control.suction))
    add_hotkey("h", lambda: dobot_control.move_home())
    add_hotkey("1", lambda: dobot_control.move_block_to_storage_manual_mode("blue"))
    add_hotkey("2", lambda: dobot_control.move_block_to_storage_manual_mode("green"))
    add_hotkey("3", lambda: dobot_control.move_block_to_storage_manual_mode("red"))
    add_hotkey("4", lambda: dobot_control.move_block_to_storage_manual_mode("yellow"))
    add_hotkey("esc", lambda: dobot_control.dobot_disconnect())
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
            dobot_type.SetPTPCmd(dobot_control.api, 1, x, y, z, r, isQueued=1)
            sleep(0.1)
        except:
            pass