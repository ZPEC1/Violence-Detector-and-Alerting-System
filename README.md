# 🛡️ Real-Time Violence Detection & Alert System

A professional, real-time surveillance system built using **MobileNetV2 (Keras/TFLite)** that detects violent activity from live video feeds and instantly triggers **Email**, **SMS**, and **Voice Call alerts** using **Twilio**.

---

## 🧠 Overview

This system operates in two lightweight, decoupled components:

1. **Detector (`detect_violence.py` / `pi_detector.py`)** – Monitors the camera feed in real-time and sends alerts when violence is detected.
2. **Alert Server (`alert_server.py`)** – A FastAPI server that receives the alert signal and manages Twilio-based SMS and voice notifications.

**Architecture:**

```
Camera → Detector → (Email + HTTP Ping) → Alert Server → (SMS + Call)
```

---

## ✨ Features

* ⚡ **Real-Time Detection:** Fast, accurate frame analysis with MobileNetV2 (TFLite on Raspberry Pi)
* 📧 **Multi-Channel Alerts:** Automatic Email (with frame evidence), SMS, and Voice Call
* 🧵 **No Lag:** Multithreaded design keeps camera feed smooth
* 🔒 **Secure:** API keys and credentials stored safely in `.env`
* 🍓 **Cross-Compatible:** Runs on Raspberry Pi or any PC with Python 3.8+

---

## ⚙️ Installation

### 1️⃣ Clone Repository & Install Dependencies

```bash
git clone https://your-repo-url/project.git
cd project
pip install -r requirements.txt
```

Add your trained model file:

* PC: `ModelWeights.weights.h5`
* Raspberry Pi: `model.tflite`

### 2️⃣ Configure Environment

Create a `.env` file in your project root:

```bash
TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxx"
TWILIO_AUTH_TOKEN="your_auth_token"
TWILIO_PHONE_NUMBER="+15551234567"
TWIML_BIN_URL="https://handler.twilio.com/twiml/xxxxx"
GMAIL_APP_PASSWORD="your-16-char-app-password"
```

**Note:** For Gmail, enable 2-Step Verification → [App Passwords](https://myaccount.google.com/apppasswords) → Generate a new 16-character password.

### 3️⃣ Update Email Recipients

In your detector script:

```python
SENDER_EMAIL = "your@gmail.com"
RECEIVER_EMAIL = "recipient@example.com"
```

---

## 💻 Run on PC

```bash
# Terminal 1 – Start Alert Server
python alert_server.py

# Terminal 2 – Start Detector
python detect_violence.py
```

When violence is detected → Email + SMS + Voice Call are triggered automatically.

---

## 🍓 Run on Raspberry Pi

```bash
pip3 install opencv-python requests python-dotenv fastapi uvicorn gpiozero tflite-runtime

# Terminal 1 – Run Alert Server
python3 alert_server.py

# Terminal 2 – Run Pi Detector
python3 pi_detector.py
```

(Optional) Connect an active buzzer to GPIO17 for instant hardware alerts.

---

## 🧰 Tech Stack

* **TensorFlow Lite / Keras** – Model inference
* **OpenCV** – Real-time camera processing
* **FastAPI + Twilio** – Backend alerts
* **GPIOZero** – Hardware control (Pi)
* **Python-Dotenv** – Secure credential management

---

