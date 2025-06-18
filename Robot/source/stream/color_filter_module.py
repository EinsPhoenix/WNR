import cv2
import numpy as np
import stream.shared_state as shared_state

def _find_large_connected_components_mask(binary_mask: np.ndarray, min_area: int) -> np.ndarray:
    """
    Finds connected components in a binary mask and returns a mask
    of components larger than min_area.
    Uses 8-connectivity.
    """
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary_mask, 8, cv2.CV_32S)
    output_mask = np.zeros_like(binary_mask, dtype=np.uint8)
    for i in range(1, num_labels):
        if stats[i, cv2.CC_STAT_AREA] >= min_area:
            output_mask[labels == i] = 255
    return output_mask

def apply_color_filter(frame: np.ndarray, min_area: int = 100) -> np.ndarray:
    """
    Filters the frame to keep only specified colors (Red, Green, Blue, Yellow)
    in regions larger than min_area, excluding overexposed white areas and attempting
    to reduce noise from patterns.
    Args:
        frame: The input BGR frame.
        min_area: The minimum area for a color region to be kept.
    Returns:
        A BGR frame with only the filtered color regions.
    """
    hsv_image = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    lower_white = np.array([0, 0, shared_state.V_WHITE_MIN])
    upper_white = np.array([179, shared_state.S_WHITE_MAX, 255])
    overexposed_mask = cv2.inRange(hsv_image, lower_white, upper_white)
    non_overexposed_mask = cv2.bitwise_not(overexposed_mask)
    sufficiently_saturated_mask = cv2.inRange(hsv_image,
                                              np.array([0, shared_state.S_DESATURATED_THRESHOLD, 0]),
                                              np.array([179, 255, 255]))
    kernel_size = 3
    kernel = np.ones((kernel_size, kernel_size), np.uint8)
    color_ranges = shared_state.COLOR_FILTER
    final_object_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    for color_name, ranges in color_ranges.items():
        current_color_mask = np.zeros(frame.shape[:2], dtype=np.uint8)
        for lower_bound, upper_bound in ranges:
            mask_part = cv2.inRange(hsv_image, lower_bound, upper_bound)
            current_color_mask = cv2.bitwise_or(current_color_mask, mask_part)
        current_color_mask = cv2.bitwise_and(current_color_mask, sufficiently_saturated_mask)
        current_color_mask = cv2.bitwise_and(current_color_mask, non_overexposed_mask)
        current_color_mask_opened = cv2.morphologyEx(current_color_mask, cv2.MORPH_OPEN, kernel)
        large_components_of_color = _find_large_connected_components_mask(current_color_mask_opened, min_area)
        final_object_mask = cv2.bitwise_or(final_object_mask, large_components_of_color)
    result_frame = cv2.bitwise_and(frame, frame, mask=final_object_mask)
    return result_frame