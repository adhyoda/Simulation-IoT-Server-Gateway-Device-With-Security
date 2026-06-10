import json
import sqlite3
import time
import os

import paho.mqtt.client as mqtt

# ==========================
# CONFIG
# ==========================

BROKER_URL = "broker.emqx.io"
PORT = 1883

TOPIC_GTD = "koica-iot-yugi-GTD"
TOPIC_DTG = "koica-iot-yugi-DTG"
TOPIC_GTS = "koica-iot-yugi-GTS"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_NAME = os.path.join(
    BASE_DIR,
    "gateway.db"
)

# ==========================
# AGGREGATION MEMORY
# ==========================

devices_temp_data = {}

# ==========================
# DATABASE FUNCTIONS
# ==========================

def device_exists(device_id):

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM devices WHERE id=?",
        (device_id,)
    )

    result = cur.fetchone()

    conn.close()

    return result is not None


def update_device_status(device_id, timestamp):

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        UPDATE devices
        SET status='online',
            last_seen=?
        WHERE id=?
    """, (
        timestamp,
        device_id
    ))

    conn.commit()
    conn.close()


def save_raw_data(
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
        INSERT INTO raw_data
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
# MQTT CALLBACKS
# ==========================

def on_connect(client, userdata, flags, rc):

    if rc == 0:

        print("✅ Gateway Connected")

        client.subscribe(TOPIC_DTG)

        print(
            f"Subscribed: {TOPIC_DTG}"
        )

    else:

        print(
            f"❌ Failed with code {rc}"
        )


def on_message(
    client,
    userdata,
    message
):

    global devices_temp_data

    try:

        data = json.loads(
            message.payload.decode()
        )

        device_id = data["device_id"]

        temp = data["temp"]
        hum = data["hum"]
        lux = data["lux"]
        noise = data["noise"]

        timestamp = data["timestamp"]

        token = data["token"]

        # ----------------------
        # CHECK DEVICE REGISTRY
        # ----------------------

        if not device_exists(
            device_id
        ):

            print(
                f"❌ Unknown device: {device_id}"
            )

            return

        # ----------------------
        # UPDATE STATUS
        # ----------------------

        update_device_status(
            device_id,
            timestamp
        )

        # ----------------------
        # SAVE RAW DATA
        # ----------------------

        save_raw_data(
            device_id,
            temp,
            hum,
            lux,
            noise,
            timestamp
        )

        # ----------------------
        # AGGREGATION
        # ----------------------

        if device_id not in devices_temp_data:

            devices_temp_data[
                device_id
            ] = {

                "temp": 0,
                "hum": 0,
                "lux": 0,
                "noise": 0,
                "count": 0
            }

        devices_temp_data[
            device_id
        ]["temp"] += temp

        devices_temp_data[
            device_id
        ]["hum"] += hum

        devices_temp_data[
            device_id
        ]["lux"] += lux

        devices_temp_data[
            device_id
        ]["noise"] += noise

        devices_temp_data[
            device_id
        ]["count"] += 1

        count = devices_temp_data[
            device_id
        ]["count"]

        print(
            f"📥 {device_id} | Count={count}"
        )

        # ----------------------
        # SEND AVG TO SERVER
        # ----------------------

        if count >= 5:

            avg_payload = {

                "device_id": device_id,

                "token": token,

                "temp":
                    devices_temp_data[
                        device_id
                    ]["temp"] / count,

                "hum":
                    devices_temp_data[
                        device_id
                    ]["hum"] / count,

                "lux":
                    devices_temp_data[
                        device_id
                    ]["lux"] / count,

                "noise":
                    devices_temp_data[
                        device_id
                    ]["noise"] / count,

                "timestamp": timestamp
            }

            client.publish(
                TOPIC_GTS,
                json.dumps(
                    avg_payload
                )
            )

            print(
                "📤 Sent to Server:"
            )

            print(
                avg_payload
            )

            devices_temp_data[
                device_id
            ] = {

                "temp": 0,
                "hum": 0,
                "lux": 0,
                "noise": 0,
                "count": 0
            }

    except Exception as e:

        print(
            "Error:",
            e
        )

# ==========================
# MQTT CLIENT
# ==========================

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(
    BROKER_URL,
    PORT
)

client.loop_start()

# ==========================
# MAIN LOOP
# ==========================

try:

    while True:

        client.publish(
            TOPIC_GTD,
            "CMD;SEND_DATA"
        )

        print(
            "📡 Requesting data..."
        )

        time.sleep(5)

except KeyboardInterrupt:

    print(
        "\nDisconnecting..."
    )

client.loop_stop()
client.disconnect()