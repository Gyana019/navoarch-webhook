from flask import Flask, request, jsonify
import requests
import gspread
import os
import json
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# === Google Sheets Setup using ENV VAR ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_json = os.getenv("GOOGLE_CREDS_JSON")
creds_dict = json.loads(creds_json)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open("NAVOARCH_Lead_Log").sheet1

# === In-memory user session tracking
user_sessions = {}

# === WhatsApp API Credentials (set these in Render Env too)
WHATSAPP_TOKEN = os.getenv("EAAOYazi12RkBO5EyUFpbVWbA8b0AdU5NMxZB0mqm3l5DPzBi2paAUZBeeiYiAPbzDYndE1Prz6T8OOCRKrD1pmqYdoHw9ZCfcfrCYuJpR8zS5JEfc6kEmRXWaC1f5zbf6BXIwrdkqVf95BOSlsqA7qG9Iw7cY9EiZBeF94BTCO8NBqY9YiKZCvyMT0ZCA2ZAxW3PlCZCF1rJE8k9L9PDdxplAkFiNrTD")  # your WhatsApp token
PHONE_NUMBER_ID = os.getenv("651744254683036")  # your phone number ID

def send_whatsapp_message(phone, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }
    try:
        response = requests.post(url, headers=headers, json=payload)
        print("Message sent:", response.status_code, response.text)
    except Exception as e:
        print("Failed to send message:", e)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("Incoming:", data)

    try:
        phone = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
        msg_body = data['entry'][0]['changes'][0]['value']['messages'][0].get('text', {}).get('body', '').strip()
        print(f"Message from {phone}: {msg_body}")

        state = user_sessions.get(phone, {})

        # Step 1: Interest
        if msg_body in ["Design Services Only", "End-to-End Execution", "Talk to Our Team"]:
            user_sessions[phone] = {"interest": msg_body}
            send_whatsapp_message(phone, "Great! Could you please share your Email ID?")

        # Step 2: Email
        elif "interest" in state and "email" not in state:
            user_sessions[phone]["email"] = msg_body
            send_whatsapp_message(phone, "Thanks! May I know your Name?")

        # Step 3: Name
        elif "interest" in state and "email" in state and "name" not in state:
            user_sessions[phone]["name"] = msg_body
            send_whatsapp_message(phone, "Noted. When would you prefer a quick call from our architect?")

        # Step 4: Time → Save to Google Sheet
        elif "interest" in state and "email" in state and "name" in state and "time" not in state:
            user_sessions[phone]["time"] = msg_body
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            sheet.append_row([
                phone,
                state.get("interest", ""),
                state.get("email", ""),
                state.get("name", ""),
                msg_body,
                now
            ])

            send_whatsapp_message(phone, "✅ Thank you! Our team will contact you at your preferred time.")
            user_sessions.pop(phone)

        else:
            send_whatsapp_message(phone, "Sorry, I didn't understand that. Please start again by selecting a service option.")
            user_sessions.pop(phone, None)

    except Exception as e:
        print(f"[ERROR] Webhook failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "received"}), 200

@app.route("/", methods=["GET"])
def index():
    return "NAVOARCH Webhook is running securely!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
