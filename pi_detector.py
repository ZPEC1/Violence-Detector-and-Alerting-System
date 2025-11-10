import cv2
import numpy as np
import requests
import time
import os
import threading
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from collections import deque 
from dotenv import load_dotenv

import tflite_runtime.interpreter as tflite 
from gpiozero import Buzzer 

load_dotenv() 


CAMERA_SOURCE = 0 # 0 for default USB/PiCamera
MODEL_FILE_PATH = 'model.tflite' 
FASTAPI_SERVER_URL = "http://127.0.0.1:8000/alert"


SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "zavik0914@gmail.com" 
RECEIVER_EMAIL = "ishmeet2004singh@gmail.com" 
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD")


BUZZER_PIN = 17 # The GPIO pin you wired to
buzzer = Buzzer(BUZZER_PIN)


IMG_SIZE = 128
ColorChannels = 3
CONF_THRESHOLD = 0.80
FRAME_COUNT_THRESHOLD = 5
FRAME_SAVE_COUNT = 3
ALERT_COOLDOWN = 60
last_alert_time = 0

frame_buffer = deque(maxlen=FRAME_SAVE_COUNT)


print("[INFO] Loading TFLite model...")
interpreter = tflite.Interpreter(model_path=MODEL_FILE_PATH)
interpreter.allocate_tensors()


input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
input_shape = input_details[0]['shape'] # Should be [1, 128, 128, 3]

print(f"[INFO] Model loaded. Input shape: {input_shape}")



def send_email_with_frames(frames_to_send):
    """
    This function sends the email with frame attachments.
    """
    if not GMAIL_APP_PASSWORD:
        print("[ERROR] Gmail App Password not found. Check your .env file.")
        return
    print("[INFO] Preparing email with frame attachments...")
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "!!! VIOLENCE ALERT !!!"
    body = "Violence detected by your security system. See attached frames."
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

def send_alert_to_server():
    """
    This function pings the FastAPI server.
    """
    print(f"[INFO] Sending alert ping to server: {FASTAPI_SERVER_URL}")
    try:
        r = requests.post(FASTAPI_SERVER_URL)
        r.raise_for_status() 
        print("[INFO] Alert ping sent successfully to server.")
    except requests.exceptions.ConnectionError:
        print("[ERROR] Could not connect to FastAPI server. Is it running?")
    except Exception as e:
        print(f"[ERROR] An unknown error occurred while pinging server: {e}")

def trigger_all_alerts(frames_to_send):
    """
    This function runs in a separate thread.
    It now ALSO controls the buzzer.
    """
    print("[THREAD] Alert thread started...")
    
    try:
        print("[THREAD] Sounding buzzer...")
        buzzer.on()
        time.sleep(3) 
        buzzer.off()
    except Exception as e:
        print(f"[ERROR] Could not sound buzzer: {e}")


    send_email_with_frames(frames_to_send)
    send_alert_to_server()
    print("[THREAD] Alert thread finished.")


print(f"[INFO] Connecting to camera source: {CAMERA_SOURCE}...")
cap = cv2.VideoCapture(CAMERA_SOURCE)
if not cap.isOpened():
    print(f"Error: Could not open video stream from source {CAMERA_SOURCE}.")
    exit()

detection_counter = 0
print("[INFO] Starting violence detection... Press 'q' to quit.")


while True:
    ret, frame = cap.read()
    if not ret:
        print("Stream ended or error reading frame.")
        break

    frame_buffer.append(frame) 


    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
    frame_resized = cv2.resize(frame_rgb, (IMG_SIZE, IMG_SIZE))
    frame_normalized = frame_resized / 255.0
    

    frame_batch = np.expand_dims(frame_normalized, axis=0).astype(np.float32)
    

    interpreter.set_tensor(input_details[0]['index'], frame_batch)
    

    interpreter.invoke()
    

    prediction = interpreter.get_tensor(output_details[0]['index'])
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
    
    if (detection_counter >= FRAME_COUNT_THRESHOLD) and \
       ((current_time - last_alert_time) > ALERT_COOLDOWN):
        
        print(f"[ALERT] Violence detected! Triggering all alerts in background...")
        cv2.putText(frame, "!!! ALERTING !!!", (20, 80), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
        
        frames_snapshot = list(frame_buffer) 
        alert_thread = threading.Thread(target=trigger_all_alerts, args=(frames_snapshot,))
        alert_thread.start()
        
        last_alert_time = time.time()
        detection_counter = 0
    

    cv2.imshow("Pi Violence Detection (Press 'q' to quit)", frame)
    
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break


print("[INFO] Stopping detection and cleaning up...")
buzzer.off() 
cap.release()
cv2.destroyAllWindows()