# 🛡️ Real-Time Violence Detection & Alert System

This project provides a complete, real-time violence detection system using a Keras/MobileNetV2 model. When violence is detected, it automatically triggers a multi-channel alert, sending an **email with frame-grab evidence** and initiating an **immediate SMS and voice call** via Twilio.

The system is built as two main components:
1.  **Detector (`detect_violence.py`):** A lightweight client that uses OpenCV to watch a camera feed. It runs the Keras model for inference and is responsible for sending the email alert.
2.  **Alert Server (`alert_server.py`):** A robust FastAPI server that receives a simple "ping" from the detector and handles all the Twilio API logic (SMS/Call).

This decoupled, multithreaded architecture ensures that the camera feed **never lags** while the alerts are being sent.

## 🏛️ System Architecture

The two-part system works as follows:

1.  The **Detector** (`detect_violence.py`) monitors the camera feed.
2.  When `N` consecutive frames are classified as "Violence," it triggers an alert.
3.  A **background thread** is immediately started to prevent camera lag.
4.  This thread does two jobs:
    * **Sends an email** (via Gmail) with the last 3 captured frames as attachments.
    * **Sends an HTTP ping** to the `http://127.0.0.1:8000/alert` endpoint.
5.  The **Alert Server** (`alert_server.py`), which is running constantly, receives this ping.
6.  The server then executes its two tasks: sending an **SMS alert** and making a **voice call** using Twilio.



## ✨ Key Features

* **Real-Time Detection:** Uses a lightweight MobileNetV2 model for fast inference.
* **Multi-Channel Alerts:** Notifies you via Email, SMS, and Voice Call.
* **Image Proof:** The email alert automatically includes saved frames as attachments.
* **No Lag:** Asynchronous (multithreaded) alert handling ensures the camera stream never freezes.
* **Decoupled & Robust:** A separate FastAPI server handles critical API alerts, so the detector's only job is to detect.
* **Secure:** All API keys and secrets are managed safely in a `.env` file.

---

## 🚀 Getting Started

Follow these steps to set up and run the system.

### 1. Prerequisites

* Python 3.8+
* A webcam
* A Google Account (for sending email)
* A Twilio Account (for SMS/Calls)

### 2. Installation

1.  **Clone the repository:**
    ```bash
    git clone https://your-repo-url/project.git
    cd project
    ```

2.  **Install all required libraries:**
    (This uses the `requirements.txt` file you created)
    ```bash
    pip install -r requirements.txt
    ```

3.  **Download Model Weights:**
    Make sure your trained model file, `ModelWeights.weights.h5`, is in the main project folder.

### 3. Configuration (The `.env` File)

This is the most important step. Create a file named `.env` in the root of your project folder.

1.  **Create the `.env` file:**
    ```bash
    # This is your .env file
    # --- Twilio Secrets (for alert_server.py) ---
    TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxx"
    TWILIO_AUTH_TOKEN="your_auth_token_here"
    TWILIO_PHONE_NUMBER="+15551234567"
    TWIML_BIN_URL="[https://handler.twilio.com/twiml/xxxxx](https://handler.twilio.com/twiml/xxxxx)"

    # --- Gmail Secret (for detect_violence.py) ---
    GMAIL_APP_PASSWORD="your-16-char-app-password"
    ```

2.  **Fill in your values:**

    * **Twilio Values:** Get these from your [Twilio Dashboard](https://www.twilio.com/console).
    * **`TWIML_BIN_URL`:** Log in to Twilio, go to "TwiML Bins," create a new bin, and paste this XML content. The URL it gives you is your `TWIML_BIN_URL`.
        ```xml
        <?xml version="1.0" encoding="UTF-8"?>
        <Response>
          <Say>
            This is an automated security alert. A violence event has been detected at your location. Please check your cameras immediately.
          </Say>
        </Response>
        ```
    * **`GMAIL_APP_PASSWORD`:** You **cannot** use your regular password.
        1.  Go to your Google Account and enable **2-Step Verification**.
        2.  Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords).
        3.  Generate a new 16-character password for "Mail" on "Other." Use this password.

### 4. Update Email Addresses

In `detect_violence.py`, update the sender and receiver emails:
```python
# --- Email Configuration ---
SENDER_EMAIL = "your-email@gmail.com" # <-- YOUR GMAIL
RECEIVER_EMAIL = "email-to-alert@example.com" # <-- WHERE TO SEND IT
