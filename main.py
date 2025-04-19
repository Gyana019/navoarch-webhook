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
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    if messages:
                        sender_id = messages[0]["from"]
                        send_template_reply(sender_id)
        except Exception as e:
            print("❌ Error while processing message:", e)

        return "EVENT_RECEIVED", 200


def send_template_reply(recipient_number):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "template",
        "template": {
            "name": "navoarch_welcome_01",
            "language": {
                "code": "en"
            }
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("📤 Sent template reply:", response.status_code, response.text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
