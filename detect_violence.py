import cv2
import numpy as np
import tensorflow as tf
import requests
import time
import os
import threading # <-- 1. NEW IMPORT

# Email libraries
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from collections import deque 

# Keras libraries
from tensorflow.keras.layers import Input, Dense
from tensorflow.keras.models import Model
from tensorflow.keras.applications import MobileNetV2

from dotenv import load_dotenv

load_dotenv() 

# --- 1. Configuration ---
CAMERA_SOURCE = 0
MODEL_WEIGHTS_PATH = 'ModelWeights.weights.h5'
FASTAPI_SERVER_URL = "http://127.0.0.1:8000/alert"

# --- Email Configuration ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "zavik0914@gmail.com"
RECEIVER_EMAIL = "zavik.khanchi@gmail.com"
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")

# --- Detection Logic ---
IMG_SIZE = 128
ColorChannels = 3
CONF_THRESHOLD = 0.90
FRAME_COUNT_THRESHOLD = 5
FRAME_SAVE_COUNT = 3
ALERT_COOLDOWN = 60
last_alert_time = 0

frame_buffer = deque(maxlen=FRAME_SAVE_COUNT)

# --- 2. Model Definition ---
def load_model_structure():
    # ... (This function is unchanged)
    input_tensor = Input(shape=(IMG_SIZE, IMG_SIZE, ColorChannels))
    baseModel = MobileNetV2(pooling='avg',
                            include_top=False,
                            input_tensor=input_tensor)
    headModel = baseModel.output
    headModel = Dense(1, activation="sigmoid")(headModel)
    model = Model(inputs=baseModel.input, outputs=headModel)
    return model

# --- 3. Email Sending Function ---
def send_email_with_frames(frames_to_send):
    # ... (This function is unchanged)
    if not GMAIL_APP_PASSWORD:
        print("[ERROR] Gmail App Password not found. Check your .env file.")
        return
    print("[INFO] Preparing email with frame attachments...")
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "!!! VIOLENCE ALERT DETECTED !!!"
    body = "Violence detected by your security system. See attached frames for evidence."
    msg.attach(MIMEText(body, 'plain'))
    temp_files = []
    try:
        for i, frame in enumerate(frames_to_send):
            filename = f"temp_frame_{i}.jpg"
            cv2.imwrite(filename, frame)
            temp_files.append(filename)
            with open(filename, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {filename}")
            msg.attach(part)
        print(f"[INFO] Connecting to {SMTP_SERVER} to send email...")
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls(context=context)
            server.login(SENDER_EMAIL, GMAIL_APP_PASSWORD)
            server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
            print("[INFO] Email alert sent successfully!")
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
    finally:
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)

# --- 4. Server Alert Function ---
def send_alert_to_server():
    # ... (This function is unchanged)
    print(f"[INFO] Sending alert ping to server: {FASTAPI_SERVER_URL}")
    try:
        r = requests.post(FASTAPI_SERVER_URL)
        r.raise_for_status() 
        print("[INFO] Alert ping sent successfully to server.")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to FastAPI server. Is it running?")
    except Exception as e:
        print(f"[ERROR] An unknown error occurred while pinging server: {e}")

# --- 5. NEW: Wrapper Function for Threading ---
def trigger_all_alerts(frames_to_send):
    """
    This function runs in a separate thread so it doesn't block the camera.
    """
    print("[THREAD] Alert thread started...")
    # 1. Send the email with frames
    send_email_with_frames(frames_to_send)
    
    # 2. Ping the server to trigger SMS/Call
    send_alert_to_server()
    print("[THREAD] Alert thread finished.")

# --- 6. Initialization ---
print("[INFO] Loading Keras model structure...")
model = load_model_structure()
model.load_weights(MODEL_WEIGHTS_PATH)
print("[INFO] Model weights loaded successfully.")

print(f"[INFO] Connecting to camera source: {CAMERA_SOURCE}...")
cap = cv2.VideoCapture(CAMERA_SOURCE)
if not cap.isOpened():
    print(f"Error: Could not open video stream from source {CAMERA_SOURCE}.")
    exit()

detection_counter = 0
print("[INFO] Starting violence detection... Press 'q' to quit.")

# --- 7. Main Processing Loop ---
while True:
    ret, frame = cap.read()
    if not ret:
        print("Stream ended or error reading frame.")
        break

    frame_buffer.append(frame) 

    frame_resized = cv2.resize(frame, (IMG_SIZE, IMG_SIZE))
    frame_normalized = frame_resized / 255.0
    frame_batch = np.expand_dims(frame_normalized, axis=0)
    
    prediction = model.predict(frame_batch, verbose=0)
    probability = prediction[0][0]

    found_violence = False
    if probability >= CONF_THRESHOLD:
        found_violence = True
        display_label = f"VIOLENCE: {probability * 100:.1f}%"
        color = (0, 0, 255)
    else:
        display_label = f"Non-Violence: {(1.0 - probability) * 100:.1f}%"
        color = (0, 255, 0)

    if found_violence:
        detection_counter += 1
    else:
        detection_counter = 0

    cv2.putText(frame, display_label, (20, 40), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    current_time = time.time()
    
    # --- 8. MODIFIED: Alert Trigger Logic ---
    if (detection_counter >= FRAME_COUNT_THRESHOLD) and \
       ((current_time - last_alert_time) > ALERT_COOLDOWN):
        
        print(f"[ALERT] Violence detected! Triggering all alerts in background...")
        cv2.putText(frame, "!!! ALERTING !!!", (20, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        
        # --- DO NOT CALL THE SLOW FUNCTIONS HERE ---
        # send_email_with_frames(list(frame_buffer))  <-- REMOVED
        # send_alert_to_server()                        <-- REMOVED
        
        # --- INSTEAD: Start the new thread ---
        # We copy the buffer to ensure the thread has the correct frames
        frames_snapshot = list(frame_buffer) 
        alert_thread = threading.Thread(target=trigger_all_alerts, args=(frames_snapshot,))
        alert_thread.start()
        
        # Reset cooldown and counter immediately
        last_alert_time = time.time()
        detection_counter = 0

    cv2.imshow("Violence Detection Stream (Press 'q' to quit)", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- 9. Cleanup ---
print("[INFO] Stopping detection and cleaning up...")
cap.release()
cv2.destroyAllWindows()