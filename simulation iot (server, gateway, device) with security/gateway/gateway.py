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

# 🟢 Perbaikan: Semua nama topik diseragamkan menggunakan 'yugi'
TOPIC_GTD = "koica-iot-U1-GTD"
TOPIC_DTG = "koica-iot-U1-DTG"
TOPIC_GTS = "koica-iot-U1-GTS"
TOPIC_STG = "koica-iot-U1-STG"  # Ditambahkan & disamakan

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
        client.subscribe(TOPIC_STG)  
        print(f"Subscribed: {TOPIC_DTG} & {TOPIC_STG}")
    else:
        print(f"❌ Failed with code {rc}")


def on_message(client, userdata, message):
    global devices_temp_data

    try:
        msg_payload = message.payload.decode()

        # 🔴 HANDLE MANAJEMEN PERANGKAT DARI SERVER
        if message.topic == TOPIC_STG:
            data = json.loads(msg_payload)
            action = data.get("action")
            dev_id = data.get("device_id")
            
            if action == "SET_DEVICE":
                desc = data.get("description")
                tkn = data.get("token")
                
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                cur.execute("""
                    INSERT OR REPLACE INTO devices (id, description, auth_token, status)
                    VALUES (?, ?, ?, 'offline')
                """, (dev_id, desc, tkn))
                conn.commit()
                conn.close()
                print(f"⚙️ DB Lokal Diperbarui via Server: {dev_id} - {desc}")
                
            # 🔴 TAMBAHKAN KONDISI INI:
            elif action == "DELETE_DEVICE":
                conn = sqlite3.connect(DB_NAME)
                cur = conn.cursor()
                
                # Hapus device dari registry lokal gateway
                cur.execute("DELETE FROM devices WHERE id=?", (dev_id,))
                
                conn.commit()
                conn.close()
                print(f"🗑️ DB Lokal Menghapus Device via Server: {dev_id}")
                
            return

        # 🟢 2. HANDLE DATA SENSOR DARI DEVICE
        if message.topic == TOPIC_DTG:
            data = json.loads(msg_payload)
            device_id = data["device_id"]
            temp = data["temp"]
            hum = data["hum"]
            lux = data["lux"]
            noise = data["noise"]
            timestamp = data["timestamp"]
            token = data["token"]

            # --- CHECK DEVICE REGISTRY ---
            if not device_exists(device_id):
                print(f"❌ Unknown device: {device_id}")
                return

            # --- UPDATE STATUS & SAVE RAW ---
            update_device_status(device_id, timestamp)
            save_raw_data(device_id, temp, hum, lux, noise, timestamp)

            # --- AGGREGATION LOGIC ---
            if device_id not in devices_temp_data:
                devices_temp_data[device_id] = {
                    "temp": 0, "hum": 0, "lux": 0, "noise": 0, "count": 0
                }
            
            devices_temp_data[device_id]["temp"] += temp
            devices_temp_data[device_id]["hum"] += hum
            devices_temp_data[device_id]["lux"] += lux
            devices_temp_data[device_id]["noise"] += noise
            devices_temp_data[device_id]["count"] += 1

            count = devices_temp_data[device_id]["count"]
            print(f"📥 {device_id} | Count={count}")

            # --- SEND AVG TO SERVER (Dikembalikan kodenya agar tidak hilang) ---
            if count >= 5:
                avg_payload = {
                    "device_id": device_id,
                    "token": token,  # Meneruskan token device ke server untuk divalidasi
                    "temp": devices_temp_data[device_id]["temp"] / count,
                    "hum": devices_temp_data[device_id]["hum"] / count,
                    "lux": devices_temp_data[device_id]["lux"] / count,
                    "noise": devices_temp_data[device_id]["noise"] / count,
                    "timestamp": timestamp
                }

                client.publish(TOPIC_GTS, json.dumps(avg_payload))
                print("📤 Sent to Server:")
                print(avg_payload)

                # Reset counter memory gateway kembali ke 0
                devices_temp_data[device_id] = {
                    "temp": 0, "hum": 0, "lux": 0, "noise": 0, "count": 0
                }

    except Exception as e:
        print("Error:", e)

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
# MAIN LOOP (POLLING DEVICE)
# ==========================

try:
    while True:
        client.publish(
            TOPIC_GTD,
            "CMD;SEND_DATA"
        )
        print("📡 Requesting data...")
        time.sleep(5)

except KeyboardInterrupt:
    print("\nDisconnecting...")

client.loop_stop()
client.disconnect()