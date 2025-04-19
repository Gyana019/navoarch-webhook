from flask import Flask, request
import requests
import json
import datetime

app = Flask(__name__)

# WhatsApp API Credentials
VERIFY_TOKEN = "navoarch_token"
ACCESS_TOKEN = "EAAOYazi12RkBOxtG4zyHqthQigSagLQQf8rcNZCjkTM7SWzbYHKjhThiX6xq1l9JgwXtyu7XRS0E2hFHPAsnhc6zzLtcVG10V49s4OOPMFZAhcCwvMOPWvl70akjetnwluMhr03buQsGZAHq5v8roe0spbreYvZAtVBmQ2Rzl4yKqcCMIAl2RywTZAAZAYXEO8BS8bF8Crp75lFLW5kQYiZBHPAlZCgZD"
PHONE_NUMBER_ID = "651744254683036"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook verified successfully!")
            return challenge, 200
        return "Forbidden", 403

    if request.method == "POST":
        data = request.get_json()
        print("📥 Webhook Payload:\n", json.dumps(data, indent=2))

        try:
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']

            if 'messages' in value:
                message = value['messages'][0]
                phone_number = message['from']
                msg_body = message['text']['body']

                print(f"📩 {phone_number} said: {msg_body}")

                reply = generate_auto_reply(msg_body)
                send_whatsapp_message(phone_number, reply)

        except Exception as e:
            print("❌ Error in handling message:", e)

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
    print("📤 Message Sent:", response.status_code, response.text)

def generate_auto_reply(text):
    text = text.lower()

    if "quote" in text:
        return "Please share your plot size, location, and type of project — we'll send a custom quote."
    elif "call me" in text:
        return "Sure! A team member will get in touch with you shortly."
    elif "floor plan" in text:
        return "We provide detailed floor planning. Please specify your requirement (residential/commercial)."
    elif "hi" in text or "hello" in text:
        return "Hi 👋! Welcome to NAVOARCH. How can we assist you today?"
    else:
        return "Thank you for reaching out to NAVOARCH. We’ll get back to you shortly."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
