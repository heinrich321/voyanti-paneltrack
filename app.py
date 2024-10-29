import paho.mqtt.client as mqtt
import time
import yaml
import os
import json
import json
import atexit
import sys
import random
import time
from kehua import KehuaClient

def generate_uuid():
    # Generate random parts of the UUID
    random_part = random.getrandbits(64)
    timestamp = int(time.time() * 1000)  # Get current timestamp in milliseconds
    node = random.getrandbits(48)  # Simulating a network node (MAC address)
    
    # Combine them into UUID format
    uuid_str = f'{timestamp:08x}-{random_part >> 32:04x}-{random_part & 0xFFFF:04x}-{node >> 24:04x}-{node & 0xFFFFFF:06x}'
    return uuid_str

print("Starting up...")

config = {}
script_version = ""

if os.path.exists('/data/options.json'):
    print("Loading options.json")
    with open(r'/data/options.json') as file:
        config = json.load(file)
        print("Config: " + json.dumps(config))

elif os.path.exists('kehua-dev\\config.yaml'):
    print("Loading config.yaml")
    with open(r'kehua-dev\\config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)['options']
        
else:
    sys.exit("No config file found")  


scan_interval = config['scan_interval']
modbus_ip = config['modbus_ip']
modbus_port = config['modbus_port']
ha_discovery_enabled = config['mqtt_ha_discovery']
code_running = True
kehua_client_connected = False
mqtt_connected = False
print_initial = True
debug_output = config['debug_output']
disc_payload = {}
repub_discovery = 0

kehua_model = None

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.will_set(config['mqtt_base_topic'] + "/availability","offline", qos=0, retain=False)
    global mqtt_connected
    mqtt_connected = True

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print("MQTT disconnected with result code "+str(reason_code))
    global mqtt_connected
    mqtt_connected = False


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "kehua-{}".format(generate_uuid()))
client.on_connect = on_connect
client.on_disconnect = on_disconnect
#client.on_message = on_message

client.username_pw_set(username=config['mqtt_user'], password=config['mqtt_password'])
client.connect(config['mqtt_host'], config['mqtt_port'], 60)
client.loop_start()
time.sleep(2)

def exit_handler():
    print("Script exiting")
    client.publish(config['mqtt_base_topic'] + "/availability","offline")
    return

atexit.register(exit_handler)

def kehua_connect():
    try:
        print("trying to connect %s" % modbus_ip)
        kehua_client = KehuaClient(modbus_ip, port=modbus_port)
        connected = kehua_client.connect()
        print("Kehua connected")
        return kehua_client, connected
    except IOError as msg:
        print("Kehua error connecting: %s" % msg)
        return False


def ha_discovery():

    global ha_discovery_enabled
    global packs

    if ha_discovery_enabled:
        
        print("Publishing HA Discovery topic...")

        disc_payload['availability_topic'] = config['mqtt_base_topic'] + "/availability"

        device = {}
        device['manufacturer'] = "Kehua"
        device['model'] = kehua_model
        device['identifiers'] = "kehua_" + kehua_model
        device['name'] = kehua_model
        disc_payload['device'] = device
        client.publish(config['mqtt_ha_discovery_topic']+"/binary_sensor/KH" + 1 + "/" + disc_payload['name'].replace(' ', '_') + "/config",json.dumps(disc_payload),qos=0, retain=True)

    else:
        print("HA Discovery Disabled")


print("Connecting to Kehua...")
kehua_client, kehua_client_connected = kehua_connect()

client.publish(config['mqtt_base_topic'] + "/availability","offline")
print_initial = True

try:
    model = kehua_client.read_model()
except:
    print("Error retrieving model")
    quit()
    


while code_running == True:

    if kehua_client_connected == True:
        if mqtt_connected == True:
            # READ DATA

            if print_initial:
                ha_discovery()
                
            client.publish(config['mqtt_base_topic'] + "/availability","online")

            print_initial = False
            

            repub_discovery += 1
            if repub_discovery*scan_interval > 3600:
                repub_discovery = 0
                print_initial = True
        
        else: #MQTT not connected
            client.loop_stop()
            print("MQTT disconnected, trying to reconnect...")
            client.connect(config['mqtt_host'], config['mqtt_port'], 60)
            client.loop_start()
            time.sleep(5)
            print_initial = True
    else: #BMS not connected
        print("Client disconnected, trying to reconnect...")
        kehua_client, kehua_client_connected = kehua_connect()
        client.publish(config['mqtt_base_topic'] + "/availability","offline")
        time.sleep(5)
        print_initial = True

client.loop_stop()