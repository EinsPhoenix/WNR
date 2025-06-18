import cv2
import socket
import struct
import time
import asyncio  
from datetime import datetime, timedelta
import config


async def try_connect_to_server(server_ip, server_port, max_retries=5, retry_delay=3):
    """Attempts to connect to the server with retries."""
    print(f"Attempting to connect to {server_ip}:{server_port}...")
    for attempt in range(max_retries):
        try:
            reader, writer = await asyncio.open_connection(server_ip, server_port)
            print("Successfully connected to server!")
            return reader, writer
        except (socket.error, ConnectionRefusedError, OSError) as e:
            print(f"Connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt + 1 < max_retries:
                await asyncio.sleep(retry_delay)
            else:
                print("Maximum connection attempts reached.")
                return None, None
    return None, None


async def streaming_timer_async(stop_event, stream_duration_minutes):
    """Timer coroutine to end streaming after specified time or run indefinitely."""
    if stream_duration_minutes <= 0:
        print("Streaming indefinitely (timer perspective)...")
        while not stop_event.is_set():
            await asyncio.sleep(60)  
            if not stop_event.is_set():  
                print("Streaming continues indefinitely (timer check)...")
        print("Indefinite streaming timer stopping.")
        return

    print(f"Streaming timer started for {stream_duration_minutes} minutes.")
    
    loop = asyncio.get_running_loop()
    end_time_abs = loop.time() + stream_duration_minutes * 60
    last_printed_minute = -1

    while not stop_event.is_set():
        current_time_abs = loop.time()
        if current_time_abs >= end_time_abs:
            break

        remaining_seconds = end_time_abs - current_time_abs
        current_minute_remaining = int(remaining_seconds / 60)

        if current_minute_remaining != last_printed_minute and current_minute_remaining >= 0:
            
            if last_printed_minute == -1 or current_minute_remaining < last_printed_minute:
                if current_minute_remaining > 0:  
                    print(f"Streaming for {current_minute_remaining} more minutes")
                last_printed_minute = current_minute_remaining

        await asyncio.sleep(1)  

    if not stop_event.is_set():
        print(f"{stream_duration_minutes}-minute streaming limit reached. Stopping stream.")
        stop_event.set()
    else:
        print("Streaming timer stopping due to external event.")


async def send_frames_async(reader, writer, cap, target_fps, display_locally, stop_event, resolution):
    """Coroutine to capture, encode, and send frames."""
    loop = asyncio.get_running_loop()
    frame_count = 0
    start_time = time.monotonic()  
    print(f"Frame sending coroutine started...")

    
    actual_camera_fps = cap.get(cv2.CAP_PROP_FPS)
    if actual_camera_fps <= 0:
        actual_camera_fps = target_fps if target_fps > 0 else 30  

    sleep_duration = 1.0 / target_fps if target_fps > 0 else 0

    try:
        while not stop_event.is_set():
            frame_read_start_time = time.monotonic()

            
            ret, frame = await loop.run_in_executor(None, cap.read)
            if not ret:
                print("Error: No frame from camera")
                stop_event.set()
                break

            
            
            if frame.shape[1] != resolution[0] or frame.shape[0] != resolution[1]:
                frame = await loop.run_in_executor(None, cv2.resize, frame, resolution)

            
            encode_param = [cv2.IMWRITE_JPEG_QUALITY, 80]
            ret_encode, encoded_frame_np = await loop.run_in_executor(None, cv2.imencode, ".jpg", frame, encode_param)

            if not ret_encode:
                print("Error: Failed to encode frame. Skipping.")
                continue

            data = encoded_frame_np.tobytes()
            message_size = struct.pack("L", len(data))

            try:
                writer.write(message_size + data)
                await writer.drain()
                frame_count += 1

                if frame_count % (int(actual_camera_fps) or 30) == 0:  
                    elapsed = time.monotonic() - start_time
                    fps_calc = frame_count / elapsed if elapsed > 0 else 0
                    print(f"Streaming FPS: {fps_calc:.2f}, Frame size: {len(data)} bytes")

            except (ConnectionResetError, BrokenPipeError, OSError) as e:
                print(f"Connection error while sending: {e}")
                stop_event.set()
                break

            processing_time = time.monotonic() - frame_read_start_time

            if display_locally:
                await loop.run_in_executor(None, cv2.imshow, "Streaming Video", frame)
                
                
                key = await loop.run_in_executor(None, cv2.waitKey, 1)
                if key != -1 and key & 0xFF == ord('q'):
                    print("Local display quit signal (q) received.")
                    stop_event.set()
                    break
            elif sleep_duration > 0:
                
                
                current_sleep = max(0, sleep_duration - processing_time)
                if current_sleep > 0:
                    await asyncio.sleep(current_sleep)
                

    except Exception as e:
        print(f"Error in send_frames_async: {e}")
        stop_event.set()  
    finally:
        print("send_frames_async finished.")
        


async def robust_video_stream_async(
    server_ip,
    server_port,
    resolution=(1920, 1080),
    fps=15,
    camera_index=0,
    display_locally=False,
    stream_duration_minutes=0,
):
    """
    Robust video streaming with automatic reconnection using asyncio.
    Args are the same as the original function.
    """
    cap = None
    try:
        
        cap = cv2.VideoCapture(camera_index, config.STREAMING_PROTOCOL)
        if not cap.isOpened():
            print(f"Error: Camera {camera_index} could not be opened.")
            return

        
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, resolution[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, resolution[1])
        cap.set(cv2.CAP_PROP_FPS, fps)

        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps_cam = cap.get(cv2.CAP_PROP_FPS)
        print(f"Camera settings: {actual_width}x{actual_height} at {actual_fps_cam} FPS (requested {fps} FPS)")
        
        current_resolution = (actual_width, actual_height)

        running = True
        while running:
            reader, writer = None, None
            stop_streaming_event = asyncio.Event()  

            try:
                print("Attempting to establish connection...")
                reader, writer = await try_connect_to_server(server_ip, server_port)

                if reader is None or writer is None:
                    print("Failed to connect. Retrying in 5 seconds...")
                    if not running:
                        break  
                    await asyncio.sleep(5)
                    continue

                print("Connection established. Starting stream session.")

                timer_task = asyncio.create_task(
                    streaming_timer_async(stop_streaming_event, stream_duration_minutes),
                    name="StreamingTimer"
                )
                send_task = asyncio.create_task(
                    send_frames_async(reader, writer, cap, fps, display_locally, stop_streaming_event, current_resolution),
                    name="SendFrames"
                )

                
                done, pending = await asyncio.wait(
                    [timer_task, send_task],
                    return_when=asyncio.FIRST_COMPLETED
                )

                stop_streaming_event.set()  

                for task in pending:
                    print(f"Cancelling pending task: {task.get_name()}")
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        print(f"Task {task.get_name()} was cancelled successfully.")
                    except Exception as e_cancel:
                        print(f"Exception in pending task {task.get__name()} during cancellation: {e_cancel}")

                for task in done:
                    if task.exception():
                        print(f"Task {task.get_name()} completed with an exception: {task.exception()}")
                    else:
                        print(f"Task {task.get_name()} completed normally.")

                print("Stream session ended.")

            except KeyboardInterrupt:
                print("KeyboardInterrupt received in connection loop. Exiting...")
                running = False
                stop_streaming_event.set()  
            except ConnectionRefusedError:  
                print("Connection refused by server (main loop). Retrying in 10 seconds...")
                if not running:
                    break
                await asyncio.sleep(10)
            except Exception as e:
                print(f"Main stream loop error: {e}. Retrying in 5 seconds...")
                stop_streaming_event.set()  
                if not running:
                    break
                await asyncio.sleep(5)
            finally:
                if writer:
                    print("Closing client writer...")
                    writer.close()
                    try:
                        await writer.wait_closed()
                    except Exception as e_close:
                        print(f"Error during writer.wait_closed(): {e_close}")

                if not running:
                    print("Exiting main streaming loop.")
                else:  
                    print("Preparing to re-attempt connection or exiting...")


    except KeyboardInterrupt:
        print("Program terminated by user (outer).")
    except Exception as e:
        print(f"Unhandled error in robust_video_stream_async: {e}")
    finally:
        if cap is not None:
            print("Releasing camera.")
            cap.release()
        if display_locally:
            print("Destroying OpenCV windows.")
            cv2.destroyAllWindows()
        print("Async video stream function finished.")


if __name__ == "__main__":
    print("Starting async robust video stream...")
    try:
        asyncio.run(robust_video_stream_async(
            config.SERVER_IP,
            config.SERVER_PORT,
            config.RESOLUTION,
            config.FPS,
            config.CAMERA_INDEX,
            config.DISPLAY_LOCALLY,
            config.STREAM_DURATION_MINUTES,
        ))
    except KeyboardInterrupt:
        print("Program terminated by user (main execution).")
    except Exception as e:
        print(f"Error running asyncio event loop: {e}")
    finally:
        print("Async stream program has shut down.")
