import json
import sqlite3
import os

import paho.mqtt.client as mqtt

BROKER_URL = "broker.emqx.io"
PORT = 1883

TOPIC_GTS = "koica-iot-yugi-GTS"

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_NAME = os.path.join(
    BASE_DIR,
    "koica-iot.db"
)

# ==========================
# DATABASE
# ==========================

def get_device(device_id):

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        SELECT auth_token
        FROM devices
        WHERE id=?
    """, (device_id,))

    result = cur.fetchone()

    conn.close()

    return result

def save_data(
    device_id,
    temp,
    hum,
    lux,
    noise,
    timestamp
):

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO device_data
        (
            device_id,
            temp,
            hum,
            lux,
            noise,
            timestamp
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        device_id,
        temp,
        hum,
        lux,
        noise,
        timestamp
    ))

    conn.commit()
    conn.close()

# ==========================
# MQTT
# ==========================

def on_connect(
    client,
    userdata,
    flags,
    rc
):

    if rc == 0:

        print("Server Connected")

        client.subscribe(
            TOPIC_GTS
        )

        print(
            f"Subscribed: {TOPIC_GTS}"
        )

def on_message(
    client,
    userdata,
    message
):

    try:

        data = json.loads(
            message.payload.decode()
        )

        device_id = data["device_id"]
        token = data["token"]

        temp = data["temp"]
        hum = data["hum"]
        lux = data["lux"]
        noise = data["noise"]

        timestamp = data["timestamp"]

        device = get_device(
            device_id
        )

        if not device:

            print(
                f"Unknown Device: {device_id}"
            )

            return

        db_token = device[0]

        if token != db_token:

            print(
                f"Invalid Token: {device_id}"
            )

            return

        save_data(
            device_id,
            temp,
            hum,
            lux,
            noise,
            timestamp
        )

        print(
            f"Data Saved: {device_id}"
        )

    except Exception as e:

        print(
            "Error:",
            e
        )

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(
    BROKER_URL,
    PORT
)

client.loop_start()

try:

    while True:
        pass

except KeyboardInterrupt:
    print("Disconnecting...")

client.loop_stop()
client.disconnect()