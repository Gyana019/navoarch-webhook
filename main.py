from flask import Flask, request
import requests
import json
import datetime

app = Flask(__name__)

VERIFY_TOKEN = "navoarch_token"
ACCESS_TOKEN = "YOUR_PERMANENT_WA_ACCESS_TOKEN"
PHONE_NUMBER_ID = "651744254683036"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    if request.method == "POST":
        data = request.get_json()
        print("Received:", json.dumps(data, indent=2))

        try:
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']
            message = value['messages'][0]
            phone_number = message['from']
            msg_body = message['text']['body']

            # LOGGING (print or insert into Google Sheets here)
            print(f"{datetime.datetime.now()}: {phone_number} said: {msg_body}")

            # REPLYING BASED ON KEYWORDS
            reply = generate_auto_reply(msg_body)
            send_whatsapp_message(phone_number, reply)

        except Exception as e:
            print("Error handling message:", e)

        return "EVENT_RECEIVED", 200

def send_whatsapp_message(to, message):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("Message Sent:", response.status_code, response.text)

def generate_auto_reply(text):
    text_lower = text.lower()
    if "quote" in text_lower:
        return "Thank you for your interest. Please share your project details, and we’ll send a quote shortly!"
    elif "call me" in text_lower:
        return "Sure! One of our team members will reach out to you soon."
    elif "floor plan" in text_lower:
        return "We can help with floor plans. Are you looking for residential, commercial, or custom?"
    elif "hi" in text_lower or "hello" in text_lower:
        return "Hi! 👋 Welcome to NAVOARCH. How can we assist you today?"
    else:
        return "Thank you for reaching out! We’ll get back to you shortly."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
