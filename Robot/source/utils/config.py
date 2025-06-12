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


# FIXME: Hier muss ich wahrscheinlich noch die Verbindungen neu aufbauen, wenn ich den Host und den Port ändere
    # Alternativ kann ich auch die Verbindung nur über die Toggle neu aufbauen
def save_config(
        self,
        dark_mode: bool = None,
        com_port: str = None,
        speed: int = None,
        tcp_host: str = None,
        tcp_port: int = None,
        stream_host: str = None,
        stream_port: int = None,
        db_host: str = None,
        db_port: int = None
    ) -> None:
    """
    Toggle the dark mode style sheet for the main window.

    Args:
        self: The main window object.
        dark_mode (bool, optional): If True, enable dark mode. If False, disable dark mode. Defaults to None.
        com_port (str, optional): The COM port to set for the robot. Defaults to None.
        speed (int, optional): The speed to set for the robot. Defaults to None.
        tcp_host (str, optional): The host address for TCP communication. Defaults to None.
        tcp_port (int, optional): The port number for TCP communication. Defaults to None.
        stream_host (str, optional): The host address for the video stream. Defaults to None.
        stream_port (int, optional): The port number for the video stream. Defaults to None.
        db_host (str, optional): The IP address for the database connection. Defaults to None.
        db_port (int, optional): The port number for the database connection. Defaults to None.
    """
    with open(self.config_path, "r") as config_file:
        config = load(config_file)
    if dark_mode is not None:
        config["ui"]["dark_mode"] = dark_mode
    if com_port is not None:
        config["robot"]["com_port"] = com_port
    if speed is not None:
        if speed > 2000:
            speed = 2000
        elif speed < 100:
            speed = 100
        config["robot"]["speed"] = speed
    if tcp_host is not None:
        config["tcp"]["host"] = tcp_host
    if tcp_port is not None:
        if tcp_port < 0 or tcp_port > 65535:
            tcp_port = 65432
        config["tcp"]["port"] = tcp_port
    if stream_host is not None:
        config["stream"]["host"] = stream_host
    if stream_port is not None:
        if stream_port < 0 or stream_port > 65535:
            stream_port = 9999
    if db_host is not None:
        config["db"]["ip"] = db_host
    if db_port is not None:
        if db_port < 0 or db_port > 65535:
            db_port = 12345
        config["stream"]["port"] = stream_port
    with open(self.config_path, "w") as config_file:
        config_file.write(dumps(config, indent=4))