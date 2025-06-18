import cv2
import socket
import struct
import time
import threading

from datetime import datetime, timedelta
from PIL import ImageGrab 
import numpy as np      


def robust_video_stream(
    server_ip,
    server_port,
    
    fps=15,
    
    screen_region=None,  
    display_locally=False,
    stream_duration_minutes=0,
    
):
    """
    Robustes Streaming eines Bildschirmbereichs mit automatischer Wiederverbindung.

    Args:
        server_ip: Server IP-Adresse
        server_port: Server Port
        fps: Gewünschte Bilder pro Sekunde
        screen_region: Tuple (x1, y1, x2, y2), das den aufzunehmenden Bildschirmbereich definiert.
                       None für den gesamten primären Bildschirm. (x1, y1) ist die obere linke Ecke,
                       (x2, y2) ist die untere rechte Ecke.
        display_locally: Lokale Anzeige aktivieren/deaktivieren
        stream_duration_minutes: Streaming-Dauer in Minuten pro Verbindung (0 für unbegrenzte Dauer)
    """

    

    try:
        
        
        if screen_region:
            capture_width = screen_region[2] - screen_region[0]
            capture_height = screen_region[3] - screen_region[1]
            print(f"Bildschirmaufnahme konfiguriert für Bereich: {screen_region} ({capture_width}x{capture_height})")
        else:
            
            try:
                temp_img = ImageGrab.grab()
                print(f"Bildschirmaufnahme konfiguriert für den gesamten Bildschirm ({temp_img.width}x{temp_img.height})")
            except Exception:
                print("Bildschirmaufnahme konfiguriert für den gesamten Bildschirm.")
        
        print(f"Ziel-FPS: {fps}")

        running = True
        while running:
            try:
                connection_event = threading.Event()
                client_socket = [None]

                def connect_to_server():
                    print(f"Versuche, Verbindung zu {server_ip}:{server_port} herzustellen...")
                    retry_count = 0
                    max_retries = 10

                    while not connection_event.is_set() and retry_count < max_retries:
                        try:
                            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                            sock.connect((server_ip, server_port))
                            print(f"Verbunden mit Server!")
                            client_socket[0] = sock
                            connection_event.set()
                            return
                        except socket.error as e:
                            retry_count += 1
                            print(
                                f"Verbindungsversuch {retry_count}/{max_retries} fehlgeschlagen: {e}"
                            )
                            time.sleep(2)

                    if retry_count >= max_retries:
                        print("Maximale Anzahl von Verbindungsversuchen erreicht.")
                        

                connect_thread = threading.Thread(target=connect_to_server)
                connect_thread.daemon = True
                connect_thread.start()

                connection_timeout = 60
                connected = connection_event.wait(timeout=connection_timeout)

                if not connected:
                    print(f"Keine Verbindung nach {connection_timeout} Sekunden, versuche erneut...")
                    time.sleep(5) 
                    continue

                stop_streaming = threading.Event()

                if stream_duration_minutes > 0:
                    stream_end_time = datetime.now() + timedelta(
                        minutes=stream_duration_minutes
                    )
                else:
                    stream_end_time = None

                def streaming_timer():
                    """Timer-Thread, um das Streaming nach der angegebenen Zeit zu beenden oder unbegrenzt laufen zu lassen"""
                    if stream_end_time is None:
                        while not stop_streaming.is_set():
                            time.sleep(60) 
                            if not stop_streaming.is_set(): 
                                print("Streaming läuft unbegrenzt weiter...")
                    else:
                        while (
                            datetime.now() < stream_end_time
                            and not stop_streaming.is_set()
                        ):
                            remaining = (
                                stream_end_time - datetime.now()
                            ).total_seconds()
                            if int(remaining) % 60 == 0 and int(remaining) > 0 : 
                                print(f"Streaming für weitere {int(remaining/60)} Minute(n)")
                            elif remaining < 60 and int(remaining) % 10 == 0 and int(remaining) > 0: 
                                 print(f"Streaming für weitere {int(remaining)} Sekunden")
                            time.sleep(1)

                        if not stop_streaming.is_set():
                            print(
                                f"{stream_duration_minutes}-Minuten Streaming-Limit erreicht"
                            )
                            stop_streaming.set()

                timer_thread = threading.Thread(target=streaming_timer)
                timer_thread.daemon = True
                timer_thread.start()

                def send_frames():
                    frame_count = 0
                    loop_start_time = time.time() 
                    
                    duration_msg = f"{stream_duration_minutes} Minuten" if stream_duration_minutes > 0 else "unbegrenzt"
                    print(f"Bildschirm-Streaming gestartet für {duration_msg}...")

                    try:
                        
                        while not stop_streaming.is_set():
                            iter_start_time = time.time() 

                            try:
                                
                                pil_image = ImageGrab.grab(bbox=screen_region)
                                
                                frame = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
                                ret = True
                            except Exception as e:
                                print(f"Fehler bei der Bildschirmaufnahme: {e}")
                                ret = False
                                
                                time.sleep(1) 
                                continue 

                            if not ret:
                                print("Fehler: Kein Frame von der Bildschirmaufnahme erhalten")
                                
                                continue 

                            _, encoded_frame = cv2.imencode(
                                ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
                            )

                            data = encoded_frame.tobytes()
                            message_size = struct.pack("L", len(data))

                            try:
                                if client_socket[0]:
                                    client_socket[0].sendall(message_size + data)
                                    frame_count += 1
                                else:
                                    print("Socket nicht verbunden, kann Frame nicht senden.")
                                    stop_streaming.set() 
                                    break


                                
                                if frame_count % int(fps if fps > 0 else 1) == 0 :
                                    elapsed_total = time.time() - loop_start_time
                                    current_fps_calc = frame_count / elapsed_total if elapsed_total > 0 else 0
                                    print(
                                        f"Aktuelle FPS: {current_fps_calc:.2f}, Frame-Größe: {len(data)} Bytes"
                                    )
                            except (socket.error, BrokenPipeError) as e:
                                print(f"Verbindungsfehler: {e}")
                                stop_streaming.set()
                                break
                            except Exception as e:
                                print(f"Unerwarteter Fehler beim Senden: {e}")
                                stop_streaming.set()
                                break


                            if display_locally:
                                cv2.imshow("Streaming Screen Region", frame)
                                if cv2.waitKey(1) & 0xFF == ord("q"):
                                    stop_streaming.set()
                                    break
                            
                            
                            
                            iter_time = time.time() - iter_start_time
                            sleep_time = (1.0 / fps) - iter_time
                            if sleep_time > 0:
                                time.sleep(sleep_time)

                    except Exception as e:
                        print(f"Fehler im send_frames Thread: {e}")
                        stop_streaming.set() 
                    finally:
                        print("Frame-Sendeschleife beendet.")
                        if client_socket[0]:
                            try:
                                print("Schließe Client-Socket.")
                                client_socket[0].close()
                                client_socket[0] = None 
                            except Exception as e:
                                print(f"Fehler beim Schließen des Sockets: {e}")
                        

                stream_thread = threading.Thread(target=send_frames)
                stream_thread.daemon = True
                stream_thread.start()

                
                while not stop_streaming.is_set():
                    if not stream_thread.is_alive(): 
                        print("Stream-Thread ist nicht mehr aktiv.")
                        stop_streaming.set() 
                        break
                    time.sleep(0.5) 

                print("Streaming für diese Verbindung beendet.")
                if stream_thread.is_alive():
                    stream_thread.join(timeout=5) 
                
                if client_socket[0] is not None: 
                    try:
                        client_socket[0].close()
                        client_socket[0] = None
                    except Exception:
                        pass
                
                
                
                
                if running: 
                    print("Versuche Wiederverbindung in 5 Sekunden...")
                    time.sleep(5)


            except KeyboardInterrupt:
                print("KeyboardInterrupt empfangen, beende Programm.")
                running = False 
                stop_streaming.set() 
            except Exception as e:
                print(f"Unerwarteter Fehler in der Hauptschleife: {e}")
                stop_streaming.set() 
                print("Versuche Neustart in 5 Sekunden...")
                time.sleep(5)

    except KeyboardInterrupt:
        print("Programm wird beendet.")
    finally:
        print("Aufräumarbeiten...")
        
        if display_locally:
            cv2.destroyAllWindows()
        print("Programm beendet.")


if __name__ == "__main__":
    SERVER_IP = "localhost"  
    SERVER_PORT = 9999
    FPS = 15  
    SCREEN_REGION = None

    DISPLAY_LOCALLY = False  
    STREAM_DURATION_MINUTES = 0  

    print("Starte Bildschirm-Streaming-Client...")
    robust_video_stream(
        SERVER_IP,
        SERVER_PORT,
        FPS,
        SCREEN_REGION,
        DISPLAY_LOCALLY,
        STREAM_DURATION_MINUTES,
    )
