import cv2
import pandas as pd

#Reading csv file with pandas and giving names to each column
index = ["color", "color_name", "hex", "R", "G", "B"]
colors_df = pd.read_csv('colors.csv', names=index, header=None)

#function to calculate minimum distance from all colors and get the most matching color
def get_color_name(R,G,B, colors_df):
    minimum = 10000
    cname = "Unknown"
    for i in range(len(colors_df)):
        # Ensure RGB values from CSV are integers for comparison
        try:
            csv_r = int(colors_df.loc[i, "R"])
            csv_g = int(colors_df.loc[i, "G"])
            csv_b = int(colors_df.loc[i, "B"])
        except ValueError:
            # Skip rows with non-integer RGB values if any
            continue
            
        d = abs(R - csv_r) + abs(G - csv_g) + abs(B - csv_b)
        if d <= minimum:
            minimum = d
            cname = colors_df.loc[i, "color_name"]
    return cname

# Function to get the dominant color from the center of an image
def get_dominant_color_from_image_center(image_array, colors_df):
    """
    Analyzes a 20x20 pixel square in the center of the image to find the dominant color.

    Args:
        image_array (numpy.ndarray): The image data.
        colors_df (pd.DataFrame): DataFrame containing color definitions.

    Returns:
        str: The name of the dominant color.
    """
    height, width, _ = image_array.shape
    
    center_x = width // 2
    center_y = height // 2
    
    square_size = 20
    half_size = square_size // 2
    
    # Define the ROI (Region of Interest)
    start_x = max(0, center_x - half_size)
    start_y = max(0, center_y - half_size)
    end_x = min(width, center_x + half_size)
    end_y = min(height, center_y + half_size)
    
    roi = image_array[start_y:end_y, start_x:end_x]
    
    if roi.size == 0:
        print("Error: Region of Interest is empty. Image might be too small.")
        return "Error: ROI empty"

    # Calculate the average color of the ROI
    # cv2.mean returns (B, G, R, Alpha/None)
    avg_bgr_color = cv2.mean(roi)
    
    avg_b = int(avg_bgr_color[0])
    avg_g = int(avg_bgr_color[1])
    avg_r = int(avg_bgr_color[2])
    
    # Get the color name
    color_name = get_color_name(avg_r, avg_g, avg_b, colors_df)
    
    return color_name, avg_r, avg_g, avg_b
    



def take_picture():
    """
    Captures an image from the default camera and saves it as image_temp.jpg.

    Returns:
        numpy.ndarray: The captured image frame, or None if capture failed.
    """
    # Try to open the first available camera
    cap = cv2.VideoCapture(0) 
    
    if not cap.isOpened():
        print("Error: Kamera konnte nicht geöffnet werden.")
        # Try another camera ID if 0 does not work
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("Error: Auch Kamera 1 konnte nicht geöffnet werden.")
            return None

    # Read a single frame from the camera
    ret, frame = cap.read()
    
    # Release the camera resource
    cap.release()
    
    if not ret:
        print("Error: Bild konnte nicht von der Kamera aufgenommen werden.")
        return None
    
    # Save the captured frame, overwriting if the file exists
    save_path = "image_temp.jpg"
    try:
        cv2.imwrite(save_path, frame)
        print(f"Bild erfolgreich als {save_path} gespeichert.")
    except Exception as e:
        print(f"Error: Bild konnte nicht gespeichert werden unter {save_path}: {e}")
       
        
    return frame


def capture_part():
    
    index=["color","color_name","hex","R","G","B"]
    csv_data = pd.read_csv('colors.csv', names=index, header=None)
    
    img = take_picture()

    if img is None:
        
        return None # Return None or an error structure if image capture fails

    dominant_color, r, g, b = get_dominant_color_from_image_center(img, csv_data)
    
    print(f"Die vorherrschende Farbe in der Mitte des aufgenommenen Bildes ist: {dominant_color} (R: {r}, G: {g}, B: {b})")

    return {
        "color": dominant_color,
        "rgb": f"{r},{g},{b}"
    }
    