import json
import uuid
import random
from datetime import datetime, timedelta


colors = ["blue", "green", "red", "yellow", "purple", "orange", "black", "white"]


start_time = datetime(2025, 3, 10, 14, 30)


data_entries = []

for i in range(1000):
    entry = {
        "uuid": str(uuid.uuid4()),
        "color": random.choice(colors),
        "sensor_data": {
            "temperature": round(random.uniform(15.0, 30.0), 1),
            "humidity": random.randint(30, 80),
        },
        "timestamp": (start_time + timedelta(minutes=i)).strftime("%Y-%m-%d %H:%M:%S"),
        "energy_consume": round(random.uniform(0.1, 1.0), 3),
        "energy_cost": round(random.uniform(0.005, 0.02), 5),
    }
    data_entries.append(entry)


json_data = {"type": "data", "data": data_entries}

with open("large_data.json", "w") as json_file:
    json.dump(json_data, json_file, indent=2)

print("JSON-Datei mit 200 Einträgen wurde erfolgreich erstellt!")
