from flask import Flask, request
import requests
import json

app = Flask(__name__)

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
            return challenge, 200
        return "Forbidden", 403

    if request.method == "POST":
        data = request.get_json()
        print("📥 Webhook Received:\n", json.dumps(data, indent=2))

        try:
            entry = data['entry'][0]
            changes = entry['changes'][0]
            value = changes['value']

            if 'messages' in value:
                message = value['messages'][0]
                phone_number = message['from']
                msg_body = message['text']['body']

                print(f"📩 Message from {phone_number}: {msg_body}")

                # Auto reply with button template message
                send_button_template(phone_number)

        except Exception as e:
            print("❌ Error processing message:", str(e))

        return "EVENT_RECEIVED", 200

def send_button_template(to):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "template",
        "template": {
            "name": "navoarch_welcome_01",  # must be pre-approved in Meta
            "language": {
                "code": "en"
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Template Message Sent:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
