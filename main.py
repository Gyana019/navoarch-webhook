from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "navoarch_token"
ACCESS_TOKEN = "EAAOYazi12RkBO43CkBqkvVgCjBeghvJCYymEHMJxZBVuEzZCnRILLVLsQOQgOPfx9L97scNrU1U1Amr4fQBQkg50ixza0AfpBqXtsVSeuXHkaLjXUbagLwvKb2dQ2xyyoeNmh9IK6vZAMuib6ZAmL4RZCNxGxDzWu8QxK8dcXRqyZBFpaRZCqhK35HIR9mWei41AEMyWzm24BSQKJGpbMdjgkykTs37"
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
                        phone_number_id = value["metadata"]["phone_number_id"]
                        from_number = messages[0]["from"]
                        message_text = messages[0].get("text", {}).get("body", "").lower()

                        if message_text in ["hi", "hello", "hey"]:
                            send_template_reply(from_number)
                        else:
                            send_fallback_reply(from_number)
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

def send_fallback_reply(recipient_number):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "text",
        "text": {
            "body": "Thanks for reaching out to NAVOARCH. Please choose one of the options above or say 'Hello' to start."
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Sent fallback reply:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
