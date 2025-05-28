from json import dumps, loads
from socket import socket, AF_INET, SOCK_STREAM
from sys import path
from time import sleep

path.insert(1,'./DLL')

import DobotDllType as dobot_type


CON_STR = {
    dobot_type.DobotConnect.DobotConnect_NoError:  "DobotConnect_NoError",
    dobot_type.DobotConnect.DobotConnect_NotFound: "DobotConnect_NotFound",
    dobot_type.DobotConnect.DobotConnect_Occupied: "DobotConnect_Occupied"
}


class DoBotControl:
    def __init__(self, homeX: float = 300, homeY: float = 0, homeZ: float = 0, speed: int = 500) -> None:
        """
        Initialize the DoBotControl class.

        Args:
            homeX (float, optional): The X coordinate of the home position. Default is 300.
            homeY (float, optional): The Y coordinate of the home position. Default is 0.
            homeZ (float, optional): The Z coordinate of the home position. Default is 0.
            speed (int, optional): The speed of the robot. Default is 500.
        """
        self.suction: bool = False
        self.api = dobot_type.load()
        self.homeX: float = homeX
        self.homeY: float = homeY
        self.homeZ: float = homeZ
        self.connected: bool = False
        self.dobot_connect()
        if speed > 2000:
            speed = 2000
        elif speed < 100:
            speed = 100
        self.speed: int = speed
        # FIXME: Implement speed setting in DoBotArm class
        # self.robot.speed(speed, speed)
        # FIXME: Check if pos is good
        self.green_storage: list[tuple[float, float], int] = [(0, 300), 0]
        self.blue_storage: list[tuple[float, float], int] = [(20, 280), 0]
        self.red_storage: list[tuple[float, float], int] = [(0, -300), 0]
        self.yellow_storage: list[tuple[float, float], int] = [(20, -280), 0]

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

    def move_home(self) -> None:
        """Move the robot to the home position."""
        lastIndex = dobot_type.SetPTPCmd(self.api, dobot_type.PTPMode.PTPMOVLXYZMode, self.homeX, self.homeY, self.homeZ, 0)[0]
        self.command_delay(lastIndex)
        
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

    def move_to_position(self, x: float, y: float, z: float | None = None) -> None:
        """
        Move the robot to a specified position.

        Args:
            x (float): The X coordinate of the target position.
            y (float): The Y coordinate of the target position.
            z (float | None, optional): The Z coordinate of the target position.
            r (float | None, optional): The rotation angle of the head.
        """
        if z is None:
            # FIXME: Hier muss ich noch die aktuelle Z-Position auslesen
            pass
        lastIndex = dobot_type.SetPTPCmd(self.api, dobot_type.PTPMode.PTPMOVLXYZMode, x, y, z, 0)[0]
        self.command_delay(lastIndex)

    def calibrate_camera(self) -> None:
        """Calibrate the camera by moving the robot to specific position."""
        calibrate_positions: list[tuple[int, int]] = [(0, -300), (200, -200), (300, 0), (200, 200), (0, 300)]
        for i, pos in enumerate(calibrate_positions):
            self.move_to_position(*pos)
            while self.send_message({"type": "calibrate", "payload": {"number": i, "robot_pos": {"x": pos[0], "y": pos[1]}}})["status"] == "error":
                sleep(0.5)

    def command_delay(self, lastIndex):
        # FIXME: implement function that can execute commands instantly
        dobot_type.SetQueuedCmdStartExec(self.api)
        while lastIndex > dobot_type.GetQueuedCmdCurrentIndex(self.api)[0]:
            dobot_type.dSleep(200)
        dobot_type.SetQueuedCmdStopExec(self.api)

if __name__ == "__main__":
    dobot_control = DoBotControl()