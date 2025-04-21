from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "navoarch_token"
ACCESS_TOKEN = "EAAOYazi12RkBO5RgSvAG8UnWGoXdac486stH73F6N1P24q09wXiAUu9tRMeoeoeKfzPAKZBpouQcaSPLl41hE7CDiQUU6UkWfL3wGEZA1DtGaIOIZCejZASEYeZBsm7N3Aq9mPtcnyGAt1MtZCh9WwZA67moJYGeJAUBBgWWsc3WDlZCOeRYTZCSi3aRhOjN7FJt47WsYcgUV2p0HZBmwsZAASWLfPZB65UZD"  # Replace with your permanent token
PHONE_NUMBER_ID = "651744254683036"

# In-memory session storage
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
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Sent template:", response.status_code, response.text)

def send_text_message(recipient_number, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Sent text:", response.status_code, response.text)

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return request.args.get("hub.challenge")
        return "Verification failed", 403

    if request.method == "POST":
        data = request.get_json()
        print("📥 Webhook received:\n", json.dumps(data, indent=2))

        try:
            entry = data.get("entry", [])[0]
            change = entry.get("changes", [])[0]
            value = change.get("value", {})
            message = value.get("messages", [{}])[0]
            sender = message.get("from")

            if "interactive" in message:
                title = message["interactive"]["button_reply"]["title"].lower()
                print("🔘 Button clicked:", title)

                session_data[sender] = {"interest": title}
                send_text_message(sender, "Great! May I know your name?")
                session_data[sender]["step"] = "awaiting_name"

            elif "text" in message:
                text = message["text"]["body"].strip()
                step = session_data.get(sender, {}).get("step")

                if step == "awaiting_name":
                    session_data[sender]["name"] = text
                    session_data[sender]["step"] = "awaiting_phone"
                    send_text_message(sender, "Thanks! Could you please share your phone number?")
                elif step == "awaiting_phone":
                    session_data[sender]["phone"] = text
                    session_data[sender]["step"] = "awaiting_time"
                    send_text_message(sender, "Noted. When would be a good time to talk?")
                elif step == "awaiting_time":
                    session_data[sender]["time"] = text
                    session_data[sender]["step"] = "done"
                    send_text_message(sender, "Perfect! Our team will reach out to you shortly. ✨")
                elif text.lower() in ["hi", "hello"]:
                    send_template(sender, "navoarch_welcome_01")
                else:
                    send_text_message(sender, "Hi 👋, please tap one of the buttons above to continue.")

        except Exception as e:
            print("❌ Error in webhook:", str(e))

        return "OK", 200
