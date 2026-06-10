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

    cur.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            description TEXT,
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
    # REGISTER DEVICES
    # ----------------------

    devices = [

        (
            "node_D1109",
            "Cloud Big Data Classroom"
        ),

        (
            "node_D1110",
            "Smart Factory Classroom"
        )

    ]

    for device in devices:

        cur.execute("""
            INSERT OR IGNORE
            INTO devices
            (
                id,
                description
            )
            VALUES (?, ?)
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