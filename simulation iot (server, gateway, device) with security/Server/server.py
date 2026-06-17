import json
import sqlite3
import os
import paho.mqtt.client as mqtt

# ==========================
# CONFIG
# ==========================

BROKER_URL = "broker.emqx.io"
PORT = 1883

# 🟢 Perbaikan: Topik disamakan menggunakan nama 'yugi' agar klop dengan gateway & device
TOPIC_GTS = "koica-iot-U1-GTS"
TOPIC_STG = "koica-iot-U1-STG"  

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_NAME = os.path.join(
    BASE_DIR,
    "koica-iot.db"
)

# ==========================
# DATABASE FUNCTIONS
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


# 🟢 KODE YANG HILANG DIKEMBALIKAN: Fungsi Tambah/Ubah Device ke DB Master & MQTT
def remote_set_device(device_id, description, gw_id, token):
    try:
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT OR REPLACE INTO devices (id, description, gw_id, auth_token)
            VALUES (?, ?, ?, ?)
        """, (device_id, description, gw_id, token))
        
        conn.commit()
        conn.close()
        print(f"⚙️ [Master DB] Berhasil memperbarui data perangkat: {device_id}")

        # Broadcast data baru ke Gateway & Device via MQTT
        payload = {
            "action": "SET_DEVICE",
            "device_id": device_id,
            "description": description,
            "token": token
        }

        client.publish(TOPIC_STG, json.dumps(payload), qos=1, retain=True)
        print(f"📣 [MQTT Broadcast] Perintah update '{device_id}' telah disiarkan.")

    except Exception as e:
        print("❌ Gagal melakukan remote set device:", e)


# Fungsi untuk Hapus Device di Master DB & Broadcast ke Gateway
def remote_delete_device(device_id):
    try:
        # 1. Hapus dari Master Database Server (koica-iot.db)
        conn = sqlite3.connect(DB_NAME)
        cur = conn.cursor()
        
        cur.execute("DELETE FROM devices WHERE id=?", (device_id,))
        
        conn.commit()
        conn.close()
        print(f"🗑️ [Master DB] Berhasil menghapus perangkat: {device_id}")

        # 2. Bungkus perintah hapus menjadi JSON untuk dikirim ke Gateway & Device
        payload = {
            "action": "DELETE_DEVICE",
            "device_id": device_id
        }

        # 3. Publish ke topik manajemen STG dengan retain=True
        client.publish(TOPIC_STG, json.dumps(payload), qos=1, retain=True)
        print(f"📣 [MQTT Broadcast] Perintah hapus '{device_id}' telah dikirim.")

    except Exception as e:
        print("❌ Gagal melakukan remote delete device:", e)


# ==========================
# MQTT CALLBACKS
# ==========================

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Server Connected")
        client.subscribe(TOPIC_GTS)
        print(f"Subscribed: {TOPIC_GTS}")
    else:
        print(f"❌ Connection failed with code {rc}")


def on_message(client, userdata, message):
    try:
        data = json.loads(message.payload.decode())

        device_id = data["device_id"]
        token = data["token"]
        temp = data["temp"]
        hum = data["hum"]
        lux = data["lux"]
        noise = data["noise"]
        timestamp = data["timestamp"]

        device = get_device(device_id)

        if not device:
            print(f"Unknown Device: {device_id}")
            return

        db_token = device[0]

        if token != db_token:
            print(f"Invalid Token: {device_id}")
            return

        save_data(
            device_id,
            temp,
            hum,
            lux,
            noise,
            timestamp
        )

        print(f"Data Saved: {device_id}")

    except Exception as e:
        print("Error:", e)


# ==========================
# MQTT CLIENT SETUP
# ==========================

client = mqtt.Client()

client.on_connect = on_connect
client.on_message = on_message

client.connect(BROKER_URL, PORT)
client.loop_start()


# ==========================
# MAIN LOOP / INTERACTION (Diletakkan paling bawah secara rapi)
# ==========================
try:
    print("\n🖥️  SERVER MANAJEMEN KOICA-IOT RUNNING...")
    print("Ketik 'tambah' atau 'hapus' untuk manajemen device, atau Ctrl+C untuk keluar.\n")
    
    while True:
        cmd = input("Server-Admin OS> ").strip().lower()
        
        if cmd == "tambah":
            print("--- Form Tambah/Ubah Perangkat ---")
            dev_id = input("Masukkan Device ID (ex: node_D1109): ")
            desc = input("Masukkan Deskripsi Ruangan/Lokasi: ")
            gw = input("Masukkan Gateway ID penanggung jawab (ex: gw_001): ")
            tkn = input("Masukkan Token Keamanan Baru: ")
            
            if dev_id and tkn:
                remote_set_device(dev_id, desc, gw, tkn)
            else:
                print("❌ ID dan Token tidak boleh kosong!")
                
        elif cmd == "hapus":
            print("--- Form Hapus Perangkat ---")
            dev_id = input("Masukkan Device ID yang ingin dihapus: ")
            
            if dev_id:
                remote_delete_device(dev_id)
            else:
                print("❌ ID tidak boleh kosong!")
                
except KeyboardInterrupt:
    print("\nDisconnecting Server...")

# 🟢 Pembersihan koneksi yang duplikat dihapus
client.loop_stop()
client.disconnect()