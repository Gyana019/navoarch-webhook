from flask import Flask, request
import requests
import json
import datetime

app = Flask(__name__)

# WhatsApp API credentials
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
            print("✅ Webhook verified successfully.")
            return challenge, 200
        print("❌ Webhook verification failed.")
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

                reply = generate_auto_reply(msg_body)
                print("🤖 Reply to send:", reply)

                send_whatsapp_message(phone_number, reply)

        except Exception as e:
            print("❌ Error processing message:", str(e))

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
        "text": {
            "body": message
        }
    }

    response = requests.post(url, headers=headers, json=payload)
    print("📤 Message Sent:", response.status_code, response.text)

def generate_auto_reply(text):
    text = text.lower().strip()

    # Keyword-based replies
    if "hi" in text or "hello" in text or "hey" in text:
        return "Hi 👋! Welcome to NAVOARCH – your end-to-end architecture & construction partner. How may we assist you today?"
    elif "quote" in text or "quotation" in text or "estimate" in text:
        return "Please share your site location, area, and type of project so we can provide an accurate quotation."
    elif "call me" in text or "contact" in text or "phone" in text:
        return "Sure! Our team will get in touch with you shortly 📞"
    elif "floor plan" in text or "plan" in text:
        return "We specialize in custom floor plans. Please mention whether it’s residential, commercial, or mixed-use."
    elif "team" in text:
        return "You can connect with our team for design, execution, or turnkey services. How can we assist?"
    elif "services" in text:
        return "We offer: 🏠 Architectural Design, 🛋️ Interiors, 🏗️ Turnkey Execution, 📊 BOQ & Estimation, 🌱 Green Building Advisory."
    elif "site visit" in text:
        return "Yes, we do site visits. Please share your location and preferred time to schedule it."
    elif "project management" in text:
        return "We provide complete project management with real-time updates, budgeting, and team coordination."
    elif "navoarch" in text:
        return "NAVOARCH LLP is a Bhubaneswar-based design-to-build firm delivering sustainable & premium architecture solutions since 2015."

    # Default fallback
    return "Thank you for reaching out to NAVOARCH. One of our team members will get back to you shortly. You can also type 'Quote', 'Call me', or 'Services' to proceed faster."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
