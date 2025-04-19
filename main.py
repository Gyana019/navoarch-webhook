from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "navoarch_token"
ACCESS_TOKEN = "EAAOYazi12RkBO5toZAc7HX3Wh9C8m6upC8bZAYholpb0emycZA8xy2hvv7Xj5hNYUQ9ZAE1SaQkktohuRrPefkKGvCc1jLBmwVmBxILVXeXc1xbv3OTtGbHyPtnWPCmJOit3qmVIHYNrPrDyfeOcpI6BQa0Jrw76o10SHco3lD5Dy4P0K041KjNkI9RaciFxTEBvjiBAbDxARMC8KXbaBHRMp6cZD"
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
        print("\ud83d\udcc5 Webhook Received:\n", json.dumps(data, indent=2))

        try:
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    if messages:
                        from_number = messages[0]["from"]
                        send_template_reply(from_number)
        except Exception as e:
            print("\u274c Error while processing message:", e)

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
            "language": { "code": "en" },
            "components": [
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "0",
                    "parameters": [{"type": "payload", "payload": "BUILD_PROJECT"}]
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "1",
                    "parameters": [{"type": "payload", "payload": "HOME_DESIGN"}]
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "2",
                    "parameters": [{"type": "payload", "payload": "TALK_TEAM"}]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("\ud83d\udce4 Template Reply Sent:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
