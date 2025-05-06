import Adafruit_DHT

DHT_SENSOR = Adafruit_DHT.DHT11
DHT_PIN = 4  

def get_sensor_data():
    """
    Liest Temperatur und Luftfeuchtigkeit vom DHT11 Sensor.

    Returns:
        dict: Ein Dictionary mit den Sensordaten oder None bei einem Fehler.
              Format: {'sensordata': {'temperature': WERT, 'humidity': WERT}}
    """
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)

    if humidity is not None and temperature is not None:
        return {
            'sensordata': {
                'temperature': round(temperature, 1),
                'humidity': round(humidity, 1)
            }
        }
    else:
       
        return None
