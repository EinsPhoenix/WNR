import json
import matplotlib.pyplot as plt
import os

def plot_benchmark_data(json_file_path, num_entries=100):
    """
    Liest Benchmark-Daten aus einer JSON-Datei, nimmt eine bestimmte Anzahl von Einträgen
    und erstellt einen Graphen der Geschwindigkeit über die Batch-Namen.

    Args:
        json_file_path (str): Der Pfad zur JSON-Datei.
        num_entries (int): Die Anzahl der zu verarbeitenden Einträge.
    """
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Fehler: Datei nicht gefunden unter {json_file_path}")
        return
    except json.JSONDecodeError:
        print(f"Fehler: Ungültiges JSON-Format in {json_file_path}")
        return

    
    
    batch_keys = sorted(data.keys())

    
    selected_keys = batch_keys[:num_entries]

    if not selected_keys:
        print("Keine Daten zum Plotten vorhanden.")
        return

    batch_names = []
    speeds = []
    batch_times = []

    for key in selected_keys:
        if "speed" in data[key]:
            
            try:
                time_part = key.split('_')[-3:] 
                batch_names.append(":".join(time_part))
            except IndexError:
                batch_names.append(key) 
            speeds.append(data[key]["speed"])
            batch_times.append(data[key]["batchtime"])
        else:
            print(f"Warnung: 'speed' nicht gefunden für Batch {key}")
            
        

    if not speeds:
        print("Keine Geschwindigkeitsdaten zum Plotten gefunden.")
        return

    
    fig, axs = plt.subplots(2, 1, figsize=(15, 10)) 

    
    axs[0].plot(batch_names, speeds, marker='o', linestyle='-', color='blue', label='Speed')
    axs[0].set_xlabel("Batches")
    axs[0].set_ylabel("Speed")
    axs[0].set_title(f"Benchmark Speed über die ersten {len(speeds)} Batches")
    axs[0].tick_params(axis='x', rotation=45)
    axs[0].grid(True)
    axs[0].legend()

    
    axs[1].plot(batch_names, batch_times, marker='x', linestyle='--', color='red', label='Batchtime')
    axs[1].set_xlabel("Batches")
    axs[1].set_ylabel("Batchtime")
    axs[1].set_title(f"Benchmark Batchtime über die ersten {len(batch_times)} Batches")
    axs[1].tick_params(axis='x', rotation=45)
    axs[1].grid(True)
    axs[1].legend()
    
    plt.tight_layout()  
    plt.show()

if __name__ == "__main__":
    
    
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "datacenter", "benchmark.json")
    
    
    
    file_path = r".\benchmark.json"
    
    plot_benchmark_data(file_path, num_entries=100)