# 🌐 IoT Simulation System with Secure Remote Device Management

### Developed by Adhyoda

A Python-based IoT simulation platform implementing a three-layer architecture (**Device → Gateway → Server**) using MQTT and EMQX Broker. The system supports real-time telemetry transmission, local gateway synchronization, and secure remote device management without requiring service restarts.

---

## 📖 Overview

This project simulates an Internet of Things (IoT) ecosystem consisting of:

* **Device Layer** – Simulated sensors that generate and transmit telemetry data.
* **Gateway Layer** – Local collector responsible for receiving, validating, and storing device information.
* **Server Layer** – Centralized management and monitoring platform.

In addition to data collection, the system implements a **Remote Device Management Protocol**, allowing administrators to update device configurations centrally from the server and automatically synchronize those changes across the entire architecture.

---

## ✨ Key Features

### 📡 IoT Three-Tier Architecture

The system is divided into three independent components:

* Device (Sensor Node)
* Gateway (Edge Collector)
* Server (Central Management)

### 🔄 Real-Time Configuration Synchronization

Device configuration changes can be performed directly from the server and propagated automatically through MQTT.

Supported configuration updates include:

* Device ID
* Device Description
* Device Location
* Authentication Token

### 🔐 Secure Authentication

Each device uses an authentication token to communicate with the server.

The server validates every incoming transmission before processing data.

### 🗄️ Distributed Database Synchronization

Configuration updates are automatically synchronized across:

* Central Database (`koica-iot.db`)
* Gateway Database (`gateway.db`)
* Device Configuration File (`device_config.json`)

### ⚡ Zero-Restart Management

Device credentials and metadata can be updated without restarting:

* Device Service
* Gateway Service
* Server Service

---

## 🏗️ System Architecture

```text
Device (Sensor)
      │
      ▼
MQTT Broker (EMQX)
      │
      ▼
Gateway
      │
      ▼
Central Server
      │
      ▼
SQLite Database
```

---

## 🔄 Configuration Synchronization Workflow

When an administrator updates or registers a device from the Server:

### Step 1 — Update Master Database

The Server updates the master database using:

```sql
INSERT OR REPLACE
```

on:

```text
koica-iot.db
```

### Step 2 — Broadcast Device Configuration

The Server publishes the updated device information to the MQTT broker.

Configuration topic:

```text
koica-iot-yugi-STG
```

MQTT settings:

```text
QoS = 1
Retain = True
```

### Step 3 — Gateway Synchronization

The Gateway receives the management message and updates:

```text
gateway.db
```

### Step 4 — Device Configuration Update

Matching devices receive the update and:

* Refresh authentication tokens in memory
* Rewrite local configuration files

```text
device_config.json
```

### Step 5 — Secure Data Transmission

Subsequent telemetry transmissions automatically use the updated credentials and are validated by the server.

---

## 🛠️ Technology Stack

| Technology | Purpose                      |
| ---------- | ---------------------------- |
| Python     | Core Application Development |
| MQTT       | Messaging Protocol           |
| EMQX       | MQTT Broker                  |
| SQLite     | Local & Central Database     |
| JSON       | Device Configuration Storage |
| Paho MQTT  | MQTT Client Library          |

---

## 📂 Project Structure

```text
simulation-iot-server-gateway-device-with-security/
│
├── server/
│   ├── server.py
│   └── koica-iot.db
│
├── gateway/
│   ├── gateway.py
│   └── gateway.db
│
├── device/
│   ├── device.py
│   └── device_config.json
│
├── requirements.txt
└── README.md
```

---

## 🚀 Getting Started

### Clone Repository

```bash
git clone https://github.com/adhyoda/simulation-iot-server-gateway-device-with-security.git
```

### Enter Project Directory

```bash
cd simulation-iot-server-gateway-device-with-security
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Start Components

Run each component in separate terminals:

#### Server

```bash
python server.py
```

#### Gateway

```bash
python gateway.py
```

#### Device

```bash
python device.py
```

---

## 🔐 Security Features

* Device Authentication Token
* Server-Side Validation
* Secure Configuration Distribution
* Database Synchronization Integrity
* MQTT QoS 1 Message Delivery
* Retained Configuration Messages

---

## 📊 Learning Objectives

This project demonstrates:

* IoT System Design
* MQTT Communication
* Edge Computing Concepts
* Distributed Configuration Management
* Secure Device Provisioning
* Database Synchronization
* Remote Device Administration

---

## 🔮 Future Improvements

Potential enhancements include:

* TLS/SSL MQTT Communication
* Device Certificate Authentication
* Web Dashboard Monitoring
* Device Health Monitoring
* OTA (Over-The-Air) Firmware Updates
* Docker Deployment
* Multi-Gateway Support

---

## 👨‍💻 Author

### Adhyoda

Physics Student | Graphic Designer | Aspiring Art Director & Producer

Areas of Interest:

* Internet of Things (IoT)
* Cybersecurity
* Edge Computing
* Machine Learning
* Creative Technology

GitHub: https://github.com/adhyoda

---

## 📜 License

This project is developed for educational, research, and portfolio purposes.

Feel free to use, modify, and expand the project for learning and experimentation.

---

⭐ If you find this project useful, consider giving it a star.
