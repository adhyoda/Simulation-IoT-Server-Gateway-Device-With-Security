import sqlite3
import os

# ==========================
# DATABASE CONFIG
# ==========================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_NAME = os.path.join(
    BASE_DIR,
    "gateway.db"
)

# ==========================
# INIT DATABASE
# ==========================

def init_db():

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    # ----------------------
    # DEVICE REGISTRY
    # ----------------------
    # 🔴 MODIFIKASI: Ditambahkan kolom auth_token TEXT
    cur.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            description TEXT,
            auth_token TEXT,
            status TEXT DEFAULT 'offline',
            last_seen TEXT
        )
    """)

    # ----------------------
    # RAW DATA CACHE
    # ----------------------

    cur.execute("""
        CREATE TABLE IF NOT EXISTS raw_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            temp REAL,
            hum REAL,
            lux REAL,
            noise REAL,
            timestamp TEXT,
            synced INTEGER DEFAULT 0,

            FOREIGN KEY(device_id)
            REFERENCES devices(id)
        )
    """)

    # ----------------------
    # REGISTER INITIAL DEVICES
    # ----------------------
    # 🔴 MODIFIKASI: Ditambahkan token bawaan awal biar sinkron sama database server
    devices = [

        (
            "node_D1109",
            "Cloud Big Data Classroom",
            "token123"
        ),

        (
            "node_D1110",
            "Smart Factory Classroom",
            "token456"
        )

    ]

    for device in devices:

        cur.execute("""
            INSERT OR REPLACE
            INTO devices
            (
                id,
                description,
                auth_token
            )
            VALUES (?, ?, ?)
        """, device)

    conn.commit()
    conn.close()

    print("✅ Gateway DB Initialized")
    print(f"📁 Location: {DB_NAME}")


# ==========================
# MAIN
# ==========================

if __name__ == "__main__":
    init_db()