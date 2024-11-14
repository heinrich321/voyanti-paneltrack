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
from paneltrack import PaneltrackClient

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

elif os.path.exists('paneltrack\\config.yaml'):
    print("Loading config.yaml")
    with open(r'paneltrack\\config.yaml') as file:
        config = yaml.load(file, Loader=yaml.FullLoader)['options']
        
else:
    sys.exit("No config file found")  


scan_interval = config['scan_interval']
device_address_list = config['device_address_list']
modbus_ip = config['modbus_ip']
modbus_port = config['modbus_port']
ha_discovery_enabled = config['mqtt_ha_discovery']
code_running = True
paneltrack_client_connected = False
mqtt_connected = False
print_initial = True
debug_output = config['debug_output']
disc_payload = {}
repub_discovery = 0
MQTT_BASE_TOPIC = config['mqtt_base_topic']
MQTT_HA_DISCOVERY_TOPIC = config['mqtt_ha_discovery_topic']

def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.will_set(MQTT_BASE_TOPIC + "/availability","offline", qos=0, retain=False)
    global mqtt_connected
    mqtt_connected = True

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print("MQTT disconnected with result code "+str(reason_code))
    global mqtt_connected
    mqtt_connected = False


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, "paneltrack-{}".format(generate_uuid()))
client.on_connect = on_connect
client.on_disconnect = on_disconnect
#client.on_message = on_message

client.username_pw_set(username=config['mqtt_user'], password=config['mqtt_password'])
client.connect(config['mqtt_host'], config['mqtt_port'], 60)
client.loop_start()
time.sleep(2)

def exit_handler():
    print("Script exiting")
    client.publish(MQTT_BASE_TOPIC + "/availability","offline")
    return

atexit.register(exit_handler)

def paneltrack_connect():
    try:
        print("trying to connect %s" % modbus_ip)
        paneltrack_client = PaneltrackClient(modbus_ip, port=modbus_port)
        connected = paneltrack_client.connect()
        print("Modem connected")
        return paneltrack_client, connected
    except IOError as msg:
        print("Modem error connecting: %s" % msg)
        return False

def ha_discovery(parameters):
    for meter_address in device_address_list:
        if ha_discovery_enabled:
            print("Publishing HA Discovery topics...")
            # Define device information
            device = {
                "manufacturer": "Paneltrack",
                "model": "paneltrack",
                "identifiers": [f"paneltrack_{meter_address}"],
                "name": f"Paneltrack {meter_address}"
            }

            # Base availability topic
            availability_topic = f"{MQTT_BASE_TOPIC}_{meter_address}/availability"

            # Define all sensor parameters and publish discovery messages

            for param, details in parameters.items():
                discovery_payload = {
                    "name": param,
                    "unique_id": f"pt_{meter_address}_{param.replace(' ', '_').lower()}",
                    "state_topic": f"{MQTT_BASE_TOPIC}/{meter_address}/{param.replace(' ', '_').lower()}",
                    "availability_topic": availability_topic,
                    "device": device,
                    "device_class": details.get("device_class"),
                    "unit_of_measurement": details.get("unit"),
                }
                discovery_topic = f"{MQTT_HA_DISCOVERY_TOPIC}/sensor/pt_{meter_address}/{param.replace(' ', '_').lower()}/config"
                client.publish(discovery_topic, json.dumps(discovery_payload), retain=True)

            client.publish(availability_topic, "online", retain=True)

print("Connecting to Paneltrack...")
paneltrack_client, paneltrack_client_connected = paneltrack_connect()

parameters = paneltrack_client.get_reg_map()

client.publish(MQTT_BASE_TOPIC + "/availability","offline")
print_initial = True


while code_running == True:
    if paneltrack_client_connected == True:
        if mqtt_connected == True:
            if print_initial:
                ha_discovery(parameters)
            
            for meter_address in device_address_list:
                for param, details in parameters.items():
                    value = paneltrack_client.read_register(param)
                    time.sleep(0.2)
                    client.publish(f"{MQTT_BASE_TOPIC}/{meter_address}/{param.replace(' ', '_').lower()}", value, retain=True)
            
                client.publish(MQTT_BASE_TOPIC + "/availability","online")

            print_initial = False
            time.sleep(scan_interval)

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
        paneltrack_client, paneltrack_client_connected = paneltrack_connect()
        client.publish(MQTT_BASE_TOPIC + "/availability","offline")
        time.sleep(5)
        print_initial = True

client.loop_stop()
