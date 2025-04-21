from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "navoarch_token"
ACCESS_TOKEN = "EAAOYazi12RkBOZBTZBj56wTr6XX7XLTjJmolyf3zKQ6ABEqfLwiPM8besoikVabro5VWfABorAr1wrHttlQxMWLgWkgtyYIpZAxN5VkibZAVrlYjRcTGWrdxlupMP83MCqq189HekS1eOF26uCyMCx6qpTyhmDdArZAVnZBTkwc8RZBdeM6hZAT0rUNnLkv4hHypT7capZBSg55iO5phZCoyC7kAJOqYgZD"  # Replace this with your valid access token
PHONE_NUMBER_ID = "651744254683036"

# Memory store (replace with DB in real project)
session_data = {}

def send_template(recipient, template_name):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
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
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        if mode == "subscribe" and token == VERIFY_TOKEN:
            return challenge, 200
        return "Forbidden", 403

    if request.method == "POST":
        data = request.get_json()
        print("📩 Incoming webhook:", json.dumps(data, indent=2))

        try:
            changes = data["entry"][0]["changes"][0]
            value = changes["value"]
            message = value.get("messages", [{}])[0]
            sender = message.get("from")
            wa_id = value.get("contacts", [{}])[0].get("wa_id")

            if "interactive" in message:
                # Match on BUTTON TEXT instead of ID
                button_text = message["interactive"]["button_reply"]["title"].strip().lower()
                print("🟢 Button text clicked:", button_text)

                if button_text == "plan a building project":
                    session_data[sender] = {"interest": "Building Project", "step": "ask_name"}
                    send_text(sender, "Great! May I know your name?")
                elif button_text == "home design assistance":
                    session_data[sender] = {"interest": "Home Design", "step": "ask_name"}
                    send_text(sender, "Sure! Could you share your name?")
                elif button_text == "talk to our team":
                    session_data[sender] = {"interest": "Direct Talk", "step": "ask_name"}
                    send_text(sender, "Let’s get started! What’s your name?")
                else:
                    send_text(sender, "Sorry, I didn’t get that. Please choose from the options shown.")

            elif "text" in message:
                user_input = message["text"]["body"].strip()
                step = session_data.get(sender, {}).get("step")

                if step == "ask_name":
                    session_data[sender]["name"] = user_input
                    session_data[sender]["step"] = "ask_phone"
                    send_text(sender, f"Thanks {user_input.title()}! May I have your phone number?")
                elif step == "ask_phone":
                    session_data[sender]["phone"] = user_input
                    session_data[sender]["step"] = "ask_time"
                    send_text(sender, "Perfect. When is a good time for our team to call you?")
                elif step == "ask_time":
                    session_data[sender]["time"] = user_input
                    session_data[sender]["step"] = "done"
                    send_text(sender, "Thank you! One of our architects will call you soon. ✨")
                    print("✅ Lead Captured:", session_data[sender])
                else:
                    if user_input.lower() in ["hi", "hello", "hey"]:
                        send_template(sender, "navoarch_welcome_01")
                    else:
                        send_text(sender, "Hi 👋 Please choose from the options above to begin.")

        except Exception as e:
            print("❌ Error:", e)

        return "EVENT_RECEIVED", 200
