import json
import random
import time
import paho.mqtt.client as mqtt
from datetime import datetime

# MQTT Configuration
BROKER_URL = "broker.emqx.io"
PORT = 1883

TOPIC_GTD = "koica-iot-yugi-GTD"  # Gateway -> Device
TOPIC_DTG = "koica-iot-yugi-DTG"  # Device -> Gateway

# ==========================
# Load Device Configuration
# ==========================
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(
    BASE_DIR,
    "device_config.json"
)

with open(CONFIG_FILE, "r") as f:
    config = json.load(f)

DEVICE_ID = config["device_id"]
AUTH_TOKEN = config["token"]

# ==========================
# Helper Functions
# ==========================
def save_config():
    """Save updated token to config file"""
    global AUTH_TOKEN

    config["token"] = AUTH_TOKEN

    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def generate_sensor_data():
    return {
        "temp": random.randint(20, 30),
        "hum": random.randint(30, 60),
        "lux": random.randint(100, 500),
        "noise": random.randint(25, 55)
    }

# ==========================
# MQTT Callbacks
# ==========================
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected as {DEVICE_ID}")

        client.subscribe(TOPIC_GTD)

        print(f"Subscribed: {TOPIC_GTD}")

    else:
        print(f"❌ Connection failed: {rc}")

def on_message(client, userdata, message):
    global AUTH_TOKEN

    try:
        msg = message.payload.decode()

        # --------------------------
        # Command from Gateway
        # --------------------------
        if message.topic == TOPIC_GTD:

            if msg == "CMD;SEND_DATA":

                sensor = generate_sensor_data()

                payload = {
                    "device_id": DEVICE_ID,
                    "token": AUTH_TOKEN,
                    "temp": sensor["temp"],
                    "hum": sensor["hum"],
                    "lux": sensor["lux"],
                    "noise": sensor["noise"],
                    "timestamp": datetime.now().isoformat()
                }

                client.publish(
                    TOPIC_DTG,
                    json.dumps(payload)
                )

                print("📤 Sent:", payload)

    except Exception as e:
        print("Error:", e)

# ==========================
# MQTT Setup
# ==========================
client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_URL, PORT)

client.loop_start()

# ==========================
# Main Loop
# ==========================
try:
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nDisconnecting...")

client.loop_stop()
client.disconnect()