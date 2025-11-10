from fastapi import FastAPI
import uvicorn
import os
from twilio.rest import Client
from dotenv import load_dotenv # <-- 1. NEW IMPORT

load_dotenv() # <-- 2. NEW: LOAD ALL VARIABLES FROM .env

# --- Twilio Configuration ---
TO_PHONE_NUMBER = "+917206113301" # Phone number to alert

# --- Load all secrets from environment variables ---
# (These os.environ.get() calls now automatically read from your .env file)
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")
TWIML_BIN_URL = os.environ.get("TWIML_BIN_URL") 

app = FastAPI()

def send_sms():
    """
    Uses Twilio to send an SMS alert.
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER]):
        print("--- ERROR: Twilio credentials not set. Check your .env file. ---")
        return
    
    print("--- Connecting to Twilio to send SMS... ---")
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        message = client.messages.create(
            body="!!! VIOLENCE ALERT DETECTED !!! Check cameras. Email sent with frame captures.",
            from_=TWILIO_PHONE_NUMBER,
            to=TO_PHONE_NUMBER
        )
        print(f"--- SMS alert successfully sent! (SID: {message.sid}) ---")
    except Exception as e:
        print(f"--- ERROR: Failed to send SMS: {e} ---")


def make_voice_call():
    """
    Uses Twilio to make an automated voice call.
    """
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, TWIML_BIN_URL]):
        print("--- ERROR: Twilio credentials or TwiML URL not set. Check your .env file. ---")
        return

    print("--- Connecting to Twilio to make voice call... ---")
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        call = client.calls.create(
            url=TWIML_BIN_URL,
            from_=TWILIO_PHONE_NUMBER,
            to=TO_PHONE_NUMBER
        )
        print(f"--- Voice call initiated! (SID: {call.sid}) ---")
    except Exception as e:
        print(f"--- ERROR: Failed to make voice call: {e} ---")


@app.post("/alert")
async def receive_alert():
    """
    This endpoint receives a "ping" and triggers SMS and a voice call.
    """
    print("-----------------------------------------")
    print("!!! ALERT PING RECEIVED FROM DETECTOR !!!")
    print("--- Triggering Twilio SMS and Call ---")
    print("-----------------------------------------")
    
    send_sms()
    make_voice_call()
    
    return {"status": "alert ping received, Twilio notifications triggered"}


if __name__ == "__main__":
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER, TWIML_BIN_URL]):
        print("--- WARNING: One or more Twilio environment variables are missing! ---")
        print("--- Please check your .env file and make sure all 4 Twilio variables are set. ---")

    print("Starting FastAPI server on http://127.0.0.1:8000")
    uvicorn.run(app, host="127.0.0.1", port=8000)