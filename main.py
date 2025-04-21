from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "navoarch_token"
ACCESS_TOKEN = "EAAOYazi12RkBOzXbN8jzUXcwJDOAgTuU6Otp0cFfD9RUytg7Q8zx3IOvC1lllHGCZAC6GG23zu7QwdapQnsjlQhnPZCVGn9ZCPY7A3uD8lILRnyZCmKu6ZCwXwHyrt5IGcIrJ4TZChtg9R81AcakxYZCQdPdUm23FnhOAXlZCpucKonbgFuC2ALG1Ns4Y0uKkywGaZBY6yieBBT1qSQ9rXuX6gftYmZCIZD"  # Replace with your permanent token
PHONE_NUMBER_ID = "651744254683036"

session_data = {}

def send_template(recipient_number, template_name):
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
            "name": template_name,
            "language": {"code": "en"}
        }
    }
    requests.post(url, headers=headers, json=payload)

def send_text(recipient, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, headers=headers, json=payload)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge"), 200
        return "Unauthorized", 403

    if request.method == "POST":
        data = request.get_json()
        try:
            value = data["entry"][0]["changes"][0]["value"]
            message = value.get("messages", [{}])[0]
            sender = message.get("from")

            if "interactive" in message:
                choice = message["interactive"]["button_reply"]["title"].lower()
                session_data[sender] = {"interest": choice, "step": "awaiting_name"}
                send_text(sender, "Great! May I know your name?")
                return "ok", 200

            if "text" in message:
                text = message["text"]["body"]
                state = session_data.get(sender, {})

                if state.get("step") == "awaiting_name":
                    session_data[sender]["name"] = text
                    session_data[sender]["step"] = "awaiting_phone"
                    send_text(sender, "Thanks! Please share your phone number.")
                elif state.get("step") == "awaiting_phone":
                    session_data[sender]["phone"] = text
                    session_data[sender]["step"] = "awaiting_time"
                    send_text(sender, "Perfect. When would be a good time for our team to contact you?")
                elif state.get("step") == "awaiting_time":
                    session_data[sender]["callback_time"] = text
                    session_data[sender]["step"] = "done"
                    send_text(sender, "✅ Thank you! Our team will reach out to you shortly.")
                elif text.lower() in ["hi", "hello"]:
                    send_template(sender, "navoarch_welcome_01")
                else:
                    send_text(sender, "👋 Please type 'Hi' or select from the buttons to proceed.")

        except Exception as e:
            print("❌ Error:", str(e))

        return "ok", 200
