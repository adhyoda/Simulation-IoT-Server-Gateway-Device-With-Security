import sqlite3
import os

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DB_NAME = os.path.join(
    BASE_DIR,
    "koica-iot.db"
)

def init_db():

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS devices (
            id TEXT PRIMARY KEY,
            description TEXT,
            gw_id TEXT,
            auth_token TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS device_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT,
            temp REAL,
            hum REAL,
            lux REAL,
            noise REAL,
            timestamp TEXT,

            FOREIGN KEY(device_id)
            REFERENCES devices(id)
        )
    """)

    devices = [

        (
            "node_D1109",
            "Cloud Big Data Classroom",
            "gw_001",
            "token123"
        ),

        (
            "node_D1110",
            "Smart Factory Classroom",
            "gw_001",
            "token456"
        )

    ]

    cur.executemany("""
        INSERT OR REPLACE INTO devices
        (
            id,
            description,
            gw_id,
            auth_token
        )
        VALUES (?, ?, ?, ?)
    """, devices)

    conn.commit()
    conn.close()

    print("Server DB Initialized")

if __name__ == "__main__":
    init_db()