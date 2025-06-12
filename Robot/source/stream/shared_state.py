''' Shared state for the ArUco marker and color detection system. Also for the UiWindow. '''

import numpy as np
import threading


# For ArUco Marker and Calibration
PHYSICAL_MARKER_ID_TO_TRACK = 0
MAX_CALIBRATION_PROFILE_ID = 5
CALIBRATION_FILE_PATH = "stream/marker_origins.json"


COLOR_SETTINGS_WINDOW_NAME = "Color Settings"
COLOR_ANALYSIS_WINDOW_NAME = "Color Analysis Input"


# For the minimum size a square is detected
MIN_AREA_COLOR_FILTER = 800


# HSV Color Ranges for Color Detection
S_MIN = 40
V_MIN = 40

COLOR_RANGES_HSV = {
    "red": {
        "lower": np.array([0, S_MIN, V_MIN]),
        "upper": np.array([10, 255, 255]),
        "draw_color": (0, 0, 255),
    },
    "red1": {
        "lower": np.array([150, S_MIN, V_MIN]),
        "upper": np.array([179, 255, 255]),
        "draw_color": (0, 255, 255),
    },
    "green": {
        "lower": np.array([35, S_MIN, V_MIN]),
        "upper": np.array([85, 255, 255]),
        "draw_color": (0, 255, 0),
    },
    "blue": {
        "lower": np.array([70, S_MIN, V_MIN]),
        "upper": np.array([170, 255, 255]),
        "draw_color": (255, 0, 0),
    },
    "yellow": {
        "lower": np.array([20, S_MIN, V_MIN]),
        "upper": np.array([35, 255, 255]),
        "draw_color": (0, 255, 255),
    },

}


# Filter Variables
### Color Filter
COLOR_FILTER = {
    "red": [
        (np.array([0, S_MIN, V_MIN]), np.array([10, 255, 255])),
        (np.array([150, S_MIN, V_MIN]), np.array([179, 255, 255]))
    ],
    "green": [(np.array([35, S_MIN, V_MIN]), np.array([85, 255, 255]))],
    "blue": [(np.array([70, S_MIN, V_MIN]), np.array([170, 255, 255]))],
    "yellow": [(np.array([20, S_MIN, V_MIN]), np.array([35, 255, 255]))]
}

### Desaturation Filter for filtering out white objects
S_DESATURATED_THRESHOLD = 130
S_WHITE_MAX = 35
V_WHITE_MIN = 253

# OPCUA Config
OPC_SERVER_URL = "opc.tcp://192.168.1.103:4840/freeopcua/server/"
OPC_RECONNECT_TIMEOUT = 800
OPC_FETCH_INTERVAL = 10

# calibration data and marker origins
calibrated_marker_origins = []
current_detected_marker_centers = {}
current_detected_color_objects_info = []
data_lock = threading.RLock()
global_transformation_matrix = None

# For UI
g_zoom_scale = 1.0
g_zoom_center_original_x = None
g_zoom_center_original_y = None
g_current_roi_top_left_x = 0
g_current_roi_top_left_y = 0
g_is_fullscreen = False
g_window_name = "ArUco Marker and Color Detection"

g_roi_selection_active = False
g_roi_selection_start = None
g_roi_selection_end = None
g_roi_confirmed = False
g_roi_rotation_angle = 0


# Temperature and Humidity
temperature = 0.0
humidity = 0.0

# Fan Speed
fan_speed = 0.0