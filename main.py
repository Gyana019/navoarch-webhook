from flask import Flask, request, jsonify
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

app = Flask(__name__)

# === Google Sheets Setup ===
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("creds/your_creds.json", scope)
client = gspread.authorize(creds)
sheet = client.open("NAVOARCH_Lead_Log").sheet1

# === In-memory user session
user_sessions = {}

# === WhatsApp Credentials
WHATSAPP_TOKEN = 'EAAOYazi12RkBO5EyUFpbVWbA8b0AdU5NMxZB0mqm3l5DPzBi2paAUZBeeiYiAPbzDYndE1Prz6T8OOCRKrD1pmqYdoHw9ZCfcfrCYuJpR8zS5JEfc6kEmRXWaC1f5zbf6BXIwrdkqVf95BOSlsqA7qG9Iw7cY9EiZBeF94BTCO8NBqY9YiKZCvyMT0ZCA2ZAxW3PlCZCF1rJE8k9L9PDdxplAkFiNrTD'
PHONE_NUMBER_ID = '651744254683036'

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
    requests.post(url, headers=headers, json=payload)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    try:
        phone = data['entry'][0]['changes'][0]['value']['messages'][0]['from']
        msg_body = data['entry'][0]['changes'][0]['value']['messages'][0].get('text', {}).get('body', '').strip()

        state = user_sessions.get(phone, {})

        # Step 1: Interest Selection
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

        # Step 4: Preferred Time
        elif "interest" in state and "email" in state and "name" in state and "time" not in state:
            user_sessions[phone]["time"] = msg_body
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Save to Google Sheet
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

    except Exception as e:
        print(f"Error: {e}")
    return jsonify({"status": "received"}), 200

@app.route("/", methods=["GET"])
def index():
    return "NAVOARCH Webhook is running!", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
