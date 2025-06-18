from opcua import Server, ua
import random
import asyncio
import json
import config
import os
import datetime
from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import NameOID

CERT_FILE = "./certs/server_cert.pem"
KEY_FILE = "./certs/server_key.pem"

def _generate_self_signed_cert(cert_path, key_path, hostname, app_uri):
    """
    Generates a private key and a self-signed certificate.
    """
    print(f"Generating new certificate for hostname: {hostname} and App URI: {app_uri}")

    cert_dir = os.path.dirname(cert_path)
    if not os.path.exists(cert_dir):
        os.makedirs(cert_dir)
        print(f"Directory {cert_dir} created.")

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    with open(key_path, "wb") as f:
        f.write(key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        ))

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, u"DE"), 
        x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Hessen"), 
        x509.NameAttribute(NameOID.LOCALITY_NAME, u"Fulda"), 
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"OPC UA Server"),
        x509.NameAttribute(NameOID.COMMON_NAME, hostname),
    ])
    
    san_entries = [x509.DNSName(hostname)]
    if app_uri:
        san_entries.append(x509.UniformResourceIdentifier(app_uri))

    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow() - datetime.timedelta(days=1)) # Valid from yesterday
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365 * 5))  # Valid for 5 years
        .add_extension(
            x509.SubjectAlternativeName(san_entries),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None), critical=True,
        )
        .add_extension( 
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True, 
                key_encipherment=True,
                data_encipherment=True,
                key_agreement=False, 
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension( 
            x509.ExtendedKeyUsage([
                x509.oid.ExtendedKeyUsageOID.SERVER_AUTH,
            ]),
            critical=False,
        )
    )

    certificate = builder.sign(key, hashes.SHA256())
  
    with open(cert_path, "wb") as f:
        f.write(certificate.public_bytes(serialization.Encoding.PEM))
    print(f"New certificate was saved in {cert_path} and key in {key_path}.")

async def get_sensor():
    import Adafruit_DHT
    DHT_SENSOR = Adafruit_DHT.DHT22
    DHT_PIN = 4
    
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    if humidity is not None and temperature is not None:
        print(f"Temperature={temperature:.1f}°C  Humidity={humidity:.1f}%")
        return temperature, humidity
    
    else:
        print("Sensor could not be read.")
        return None, None

async def run_server():
    server = Server()

    app_uri = f"urn:{config.OPC_SERVER_HOST.lower()}:{server.get_application_uri().split(':')[-1]}" 
    server.application_uri = app_uri

    if not os.path.exists(CERT_FILE) or not os.path.exists(KEY_FILE):
        print(f"Certificate ({CERT_FILE}) or key ({KEY_FILE}) not found.")
        _generate_self_signed_cert(CERT_FILE, KEY_FILE, config.OPC_SERVER_HOST, server.application_uri)
    else:
        print(f"Using existing certificate {CERT_FILE} and key {KEY_FILE}")
    
    server.load_certificate(CERT_FILE)
    server.load_private_key(KEY_FILE)

    server.set_security_policy([
        ua.SecurityPolicyType.Basic256Sha256_SignAndEncrypt,
        ua.SecurityPolicyType.Basic256Sha256_Sign,
    ])
    
    endpoint = server.set_endpoint(f"opc.tcp://{config.OPC_SERVER_HOST}:{config.OPC_SERVER_PORT}/freeopcua/server/")
    server.set_server_name("SensorDataServer")
    
    uri = "http://example.org"
    idx = server.register_namespace(uri)
    
    try:
        device = server.nodes.objects.add_object(idx, "Device")
        
        fan_speed = device.add_variable(idx, "FanSpeed", 0.0)
        temperature = device.add_variable(idx, "Temperature", 0.0)
        humidity = device.add_variable(idx, "Humidity", 0.0)
        set_fan_speed = device.add_variable(idx, "SetFanSpeed", 0.0)
       
        set_fan_speed.set_writable()
        
        node_ids = {
            "FanSpeed": fan_speed.nodeid.to_string(),
            "Temperature": temperature.nodeid.to_string(),
            "Humidity": humidity.nodeid.to_string(),
            "SetFanSpeed": set_fan_speed.nodeid.to_string(),
        }
        
        node_ids_variable = device.add_variable(
        idx, "NodeIDs", json.dumps(node_ids)
        )
        node_ids_variable.set_writable(False)
        
        print(f"NodeIDs variable created with NodeID: {node_ids}")

        server.start()
        print("Server started successfully.")

        while True:
            current_set_fan_speed = set_fan_speed.get_value()
           
            if current_set_fan_speed != 0:
                fan_speed.set_value(current_set_fan_speed)
            else:
                fan_speed.set_value(random.uniform(0, 100))

           # Comment for Raspberry Pi 
            temperature.set_value(random.uniform(1, 50))
            humidity.set_value(random.uniform(10, 100))
            
            # Uncomment for reading from a real sensor
            
            # sensor_temperature, sensor_humidity = await get_sensor()
            # if sensor_temperature is not None and sensor_humidity is not None:
            #     temperature.set_value(sensor_temperature)
            #     humidity.set_value(sensor_humidity)
       
            await asyncio.sleep(1)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if server:
            server.stop()
            print("Server stopped.")

if __name__ == "__main__":
    asyncio.run(run_server())