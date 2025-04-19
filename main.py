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
        print("\U0001F4E5 Webhook Received:\n", json.dumps(data, indent=2))

        try:
            for entry in data.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    if messages:
                        message = messages[0]
                        sender_id = message["from"]

                        if message.get("type") == "text":
                            user_text = message["text"]["body"].strip().lower()
                            handle_text_reply(sender_id, user_text)
                        else:
                            send_template_reply(sender_id)
        except Exception as e:
            print("❌ Error while processing message:", e)

        return "EVENT_RECEIVED", 200

def handle_text_reply(recipient_number, text):
    if "quote" in text:
        send_text_reply(recipient_number, "Sure! Please share your site location and project type for a quotation.")
    elif "call me" in text:
        send_text_reply(recipient_number, "Got it! Our team will call you shortly.")
    elif "floor plan" in text:
        send_text_reply(recipient_number, "We specialize in customized floor plans. Tell us your plot size and facing direction.")
    elif text in ["hi", "hello", "hey"]:
        send_template_reply(recipient_number)
    else:
        send_text_reply(recipient_number, "Thank you for your message. Our team will respond shortly.")

def send_text_reply(recipient_number, message):
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
            "body": message
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("\U0001F4E4 Sent text reply:", response.status_code, response.text)

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
    print("\U0001F4E4 Sent template reply:", response.status_code, response.text)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
