# simulation-iot-server-gateway-device-with-security

# IoT Simulation System (Server, Gateway, & Device) with Remote Management

Sistem simulasi IoT berbasis Python dan MQTT (menggunakan broker EMQX) yang mengimplementasikan arsitektur tiga lapis: **Device (Sensor)**, **Gateway (Kolektor Lokal)**, dan **Server (Pusat Data)**. 

Proyek ini dilengkapi dengan **Protokol Manajemen Remote**, memungkinkan administrator mengubah konfigurasi perangkat (`device_id`, deskripsi, lokasi, dan `auth_token`) secara terpusat dari Server. Perubahan tersebut otomatis disinkronisasikan ke database lokal Gateway (`gateway.db`) dan file konfigurasi fisik Device (`device_config.json`) secara *real-time* via MQTT tanpa perlu *restart* sistem.

---

## 🏗️ Arsitektur Sistem & Alur Sinkronisasi

Ketika administrator melakukan penambahan atau perubahan perangkat di terminal Server, alur otomatisasi berikut akan berjalan:

1. **Server Pusat** memperbarui database master (`koica-iot.db`) menggunakan `INSERT OR REPLACE`.
2. **Server** menyiarkan (*broadcast*) data baru tersebut ke broker MQTT pada topik manajemen `koica-iot-yugi-STG` dengan parameter `qos=1` dan `retain=True`.
3. **Gateway** menerima pesan tersebut, lalu memperbarui tabel `devices` di database lokalnya (`gateway.db`).
4. **Device** yang memiliki ID kecocokan mendengarkan pesan tersebut, memperbarui token di memori, lalu menulis ulang file konfigurasinya (`device_config.json`).
5. Sesi pengiriman data selanjutnya akan otomatis menggunakan token baru dan divalidasi dengan aman oleh Server.


