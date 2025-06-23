from json import load, dumps


def read_config(self) -> dict:
    """
    Reads the configuration file and returns the configuration as a dictionary.

    Args:
        self: The main window object.

    Returns:
        dict: The configuration dictionary.
    """
    with open(self.config_path, "r") as config_file:
        config = load(config_file)
    return config


def save_config(
        self,
        dark_mode: bool = None,
        x_offset: float = None,
        x_offset_factor: float = None,
        com_port: str = None,
        speed: int = None,
        stream_host: str = None,
        stream_port: int = None,
        y_offset: float = None,
        y_offset_factor: float = None,
        tcp_host: str = None,
        tcp_port: int = None,
        db_host: str = None,
        db_port: int = None
    ) -> None:
    """
    Toggle the dark mode style sheet for the main window.

    Args:
        self: The main window object.
        dark_mode (bool, optional): If True, enable dark mode. If False, disable dark mode. Defaults to None.
        x_offset (float, optional): The X offset for the robot's position. Defaults to None.
        x_offset_factor (float, optional): The X offset factor for the robot's position. Defaults to None.
        com_port (str, optional): The COM port to set for the robot. Defaults to None.
        speed (int, optional): The speed to set for the robot. Defaults to None.
        stream_host (str, optional): The host address for the video stream. Defaults to None.
        stream_port (int, optional): The port number for the video stream. Defaults to None.
        y_offset (float, optional): The Y offset for the robot's position. Defaults to None.
        y_offset_factor (float, optional): The Y offset factor for the robot's position. Defaults to None.
        tcp_host (str, optional): The host address for TCP communication. Defaults to None.
        tcp_port (int, optional): The port number for TCP communication. Defaults to None.
        db_host (str, optional): The IP address for the database connection. Defaults to None.
        db_port (int, optional): The port number for the database connection. Defaults to None.
    """
    with open(self.config_path, "r") as config_file:
        config = load(config_file)
    if dark_mode is not None:
        config["ui"]["dark_mode"] = dark_mode
    if x_offset is not None:
        config["robot"]["x_offset"] = x_offset
    if x_offset_factor is not None:
        config["robot"]["x_offset_factor"] = x_offset_factor
    if com_port is not None:
        config["robot"]["com_port"] = com_port
    if speed is not None:
        if speed > 2000:
            speed = 2000
        elif speed < 100:
            speed = 100
        config["robot"]["speed"] = speed
    stream_reconnect = False
    if stream_host is not None:
        if config["stream"]["host"] != stream_host:
            stream_reconnect = True
        config["stream"]["host"] = stream_host
    if stream_port is not None:
        if stream_port < 0 or stream_port > 65535:
            stream_port = 9999
        if config["stream"]["port"] != stream_port:
            stream_reconnect = True
        config["stream"]["port"] = stream_port
    if y_offset is not None:
        config["robot"]["y_offset"] = y_offset
    if y_offset_factor is not None:
        config["robot"]["y_offset_factor"] = y_offset_factor
    tcp_reconnect = False
    if tcp_host is not None:
        if config["tcp"]["host"] != tcp_host:
            tcp_reconnect = True
        config["tcp"]["host"] = tcp_host
    if tcp_port is not None:
        if tcp_port < 0 or tcp_port > 65535:
            tcp_port = 65432
        if config["tcp"]["port"] != tcp_port:
            tcp_reconnect = True
        config["tcp"]["port"] = tcp_port
    db_reconnect = False
    if db_host is not None:
        if config["db"]["host"] != db_host:
            db_reconnect = True
        config["db"]["host"] = db_host
    if db_port is not None:
        if db_port < 0 or db_port > 65535:
            db_port = 12345
        if config["db"]["port"] != db_port:
            db_reconnect = True
        config["db"]["port"] = db_port
    with open(self.config_path, "w") as config_file:
        config_file.write(dumps(config, indent=4))
    set_offset(self.stream.video_analyzer)
    if tcp_reconnect or stream_reconnect:
        self.raspi_connection_toggle.set_checked(False)
        self.raspi_connection_toggle.set_checked(True)
    if db_reconnect:
        self.db_connection_toggle.set_checked(False)
        self.db_connection_toggle.set_checked(True)


def set_offset(self) -> None:
    """Sets the offsets for the calculated block positions based on the configuration."""
    robot_config = read_config(self)["robot"]
    self.x_offset = robot_config["x_offset"]
    self.x_offset_factor = robot_config["x_offset_factor"]
    self.y_offset = robot_config["y_offset"]
    self.y_offset_factor = robot_config["y_offset_factor"]