import psutil
import matplotlib.pyplot as plt
import time
import datetime

def main():
    timestamps = []
    ram_usage_percent = []
    cpu_usage_percent = [] 
    disk_read_mb_per_sec = []
    disk_write_mb_per_sec = []

    print("Überwachung gestartet. Drücken Sie Strg+C, um zu stoppen und Diagramme zu generieren.")
    print("Daten werden jede Sekunde erfasst.")

    
    last_time = time.time()
    try:
        
        last_disk_io = psutil.disk_io_counters()
        if last_disk_io is None:
            print("Fehler: Konnte initiale Festplatten-I/O-Zähler nicht abrufen. Skript wird beendet.")
            return
    except Exception as e:
        print(f"Fehler beim Abrufen der initialen Festplatten-I/O-Zähler: {e}. Skript wird beendet.")
        return

    try:
        while True:
            
            time.sleep(1)

            current_time = time.time()
            time_delta = current_time - last_time

            
            current_datetime = datetime.datetime.now()
            timestamps.append(current_datetime)

            
            ram_percent = psutil.virtual_memory().percent
            ram_usage_percent.append(ram_percent)

            
            
            
            
            cpu_percent = psutil.cpu_percent(interval=None) 
            cpu_usage_percent.append(cpu_percent)

            
            current_disk_io = psutil.disk_io_counters()
            
            if current_disk_io is not None and last_disk_io is not None and time_delta > 0:
                
                read_bytes_delta = current_disk_io.read_bytes - last_disk_io.read_bytes
                write_bytes_delta = current_disk_io.write_bytes - last_disk_io.write_bytes

                
                read_mb_s = (read_bytes_delta / (1024 * 1024)) / time_delta
                write_mb_s = (write_bytes_delta / (1024 * 1024)) / time_delta

                disk_read_mb_per_sec.append(read_mb_s)
                disk_write_mb_per_sec.append(write_mb_s)
            elif current_disk_io is None:
                print(f"Warnung: Konnte aktuelle Festplatten-I/O-Zähler um {current_datetime.strftime('%H:%M:%S')} nicht abrufen. Überspringe dieses Intervall für Festplattenstatistiken.")
                
                disk_read_mb_per_sec.append(0)
                disk_write_mb_per_sec.append(0)
            else: 
                disk_read_mb_per_sec.append(0)
                disk_write_mb_per_sec.append(0)

            
            last_time = current_time
            if current_disk_io is not None: 
                last_disk_io = current_disk_io

    except KeyboardInterrupt:
        print("\nÜberwachung gestoppt. Diagramme werden generiert...")

        if not timestamps:
            print("Keine Daten erfasst.")
            return
        
        
        min_len = min(len(timestamps), len(ram_usage_percent), len(cpu_usage_percent), len(disk_read_mb_per_sec), len(disk_write_mb_per_sec))
        if min_len == 0:
            print("Keine konsistenten Daten zum Plotten erfasst.")
            return

        ts_plot = timestamps[:min_len]
        ram_plot = ram_usage_percent[:min_len]
        cpu_plot = cpu_usage_percent[:min_len] 
        read_plot = disk_read_mb_per_sec[:min_len]
        write_plot = disk_write_mb_per_sec[:min_len]


        
        plt.figure(figsize=(12, 6))
        plt.plot(ts_plot, ram_plot, label='RAM Auslastung (%)', color='blue', marker='.', linestyle='-')
        plt.xlabel('Zeit')
        plt.ylabel('RAM Auslastung (%)')
        plt.title('RAM Entwicklung über die Zeit')
        plt.legend()
        plt.grid(True)
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M:%S'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        ram_filename = 'ram_entwicklung.png'
        plt.savefig(ram_filename)
        print(f"RAM-Entwicklungsgraph gespeichert als {ram_filename}")

        
        plt.figure(figsize=(12, 6))
        plt.plot(ts_plot, cpu_plot, label='CPU Auslastung (%)', color='purple', marker='.', linestyle='-')
        plt.xlabel('Zeit')
        plt.ylabel('CPU Auslastung (%)')
        plt.title('CPU Entwicklung über die Zeit')
        plt.legend()
        plt.grid(True)
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M:%S'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        cpu_filename = 'cpu_auslastung.png'
        plt.savefig(cpu_filename)
        print(f"CPU-Auslastungsgraph gespeichert als {cpu_filename}")

        
        plt.figure(figsize=(12, 6))
        plt.plot(ts_plot, read_plot, label='SSD Lesen (MB/s)', color='green', marker='.', linestyle='-')
        plt.plot(ts_plot, write_plot, label='SSD Schreiben (MB/s)', color='red', marker='.', linestyle='-')
        plt.xlabel('Zeit')
        plt.ylabel('Datenrate (MB/s)')
        plt.title('SSD Lese-/Schreibbelastung über die Zeit')
        plt.legend()
        plt.grid(True)
        plt.gca().xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%H:%M:%S'))
        plt.xticks(rotation=45)
        plt.tight_layout()
        ssd_filename = 'ssd_belastung.png'
        plt.savefig(ssd_filename)
        print(f"SSD-Belastungsgraph gespeichert als {ssd_filename}")
        
        

    except Exception as e:
        print(f"Ein unerwarteter Fehler ist aufgetreten: {e}")

if __name__ == "__main__":
    print("Um dieses Skript auszuführen, benötigen Sie 'psutil' und 'matplotlib'.")
    print("Sie können diese mit pip installieren:")
    print("pip install psutil matplotlib")
    print("-" * 30)
    main()