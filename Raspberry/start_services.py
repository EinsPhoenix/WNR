import threading
import signal
import time
import sys
import subprocess
import os


shutdown_event = threading.Event()
processes = []

def run_script_as_process(script_path, thread_name):
    """Run a Python script as a subprocess."""
    try:
        print(f"Starting {thread_name} from {script_path}...")
        
        process = subprocess.Popen([sys.executable, script_path])
        processes.append(process)
        
        
        while process.poll() is None and not shutdown_event.is_set():
            time.sleep(0.5)
            
        if process.poll() is None:  
            print(f"Terminating {thread_name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"Forcefully killing {thread_name}...")
                process.kill()
                process.wait()
        
        exitcode = process.returncode
        print(f"{thread_name} exited with code {exitcode}")
        
    except Exception as e:
        print(f"Error managing {thread_name}: {e}")

def signal_handler(sig, frame):
    """Handle Ctrl+C and other termination signals."""
    print("\nShutdown signal received. Stopping services...")
    shutdown_event.set()

def main():
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    opcua_script = os.path.join(current_dir, "opcua_Rasp.py")
    stream_script = os.path.join(current_dir, "stream.py")
    
    print("Starting services as separate processes...")
    
    
    opcua_thread = threading.Thread(
        target=run_script_as_process, 
        args=(opcua_script, "OPC UA Server"),
        name="OPCUAProcessManager"
    )
    
    stream_thread = threading.Thread(
        target=run_script_as_process, 
        args=(stream_script, "Video Stream"),
        name="StreamProcessManager"
    )
    
    opcua_thread.daemon = True
    stream_thread.daemon = True
    
    opcua_thread.start()
    stream_thread.start()
    
    print("Process manager threads started. Press Ctrl+C to stop all services.")
    
    try:
        
        while not shutdown_event.is_set():
            
            if not opcua_thread.is_alive() and not stream_thread.is_alive():
                print("All process manager threads terminated. Exiting.")
                break
            time.sleep(0.5)
                
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received in main thread.")
    finally:
        
        shutdown_event.set()
        
        
        for process in processes:
            if process.poll() is None:  
                try:
                    print(f"Terminating process with PID {process.pid}...")
                    process.terminate()
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print(f"Forcefully killing process with PID {process.pid}...")
                    process.kill()
        
        print("Waiting for process manager threads to complete...")
        opcua_thread.join(timeout=5)
        stream_thread.join(timeout=5)
        
        print("All processes terminated. Main program exiting.")

if __name__ == "__main__":
    main()