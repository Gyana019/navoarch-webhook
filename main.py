from flask import Flask, request
import requests
import json
from datetime import datetime

app = Flask(__name__)

VERIFY_TOKEN = "navoarch_token"
ACCESS_TOKEN = "EAAOYazi12RkBOxOnHvlvnvT1JZCbwSNBSNQ6UzTk40W0RC8g8Tlbpokk3xvfT0Cd8PyFFDsr4KgwLoWo9YDrE6Qkl1QzM2raI6dFBKoePcKRGeM4ZAV7WOIYcr1sdapjjhhjW666lYTl4TqOJLj8NPwSBJ93VUAKivdf7ejsN8ZAoND5JZCczNC3VGq4DZBw37jDJj5pCavAoqsqtPbJXfSSF4nsZD"  # Replace with your permanent token
PHONE_NUMBER_ID = "651744254683036"

# In-memory state storage (should ideally be a database)
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
    print(f"📤 Sent template {template_name}:", response.status_code, response.text)

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
    print("📤 Sent text message:", response.status_code, response.text)

def send_template_with_buttons(recipient_number):
    send_template(recipient_number, "navoarch_welcome_01")
    session_data[recipient_number] = {"step": "await_main_choice"}

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
            changes = data.get("entry", [])[0].get("changes", [])[0]
            value = changes.get("value", {})
            message = value.get("messages", [{}])[0]
            sender = message.get("from")

            if "interactive" in message:
                button_text = message["interactive"]["button_reply"]["title"].strip().lower()
                print("🔘 Button clicked:", button_text)

                if "plan a building project" in button_text:
                    send_template(sender, "send_project_type_buttons")
                elif "home design assistance" in button_text:
                    send_template(sender, "send_home_design_type_buttons")
                elif "talk to our team" in button_text:
                    send_template(sender, "send_schedule_buttons")
                elif "today" in button_text:
                    send_template(sender, "confirm_today_evening")
                elif "tomorrow" in button_text:
                    send_template(sender, "send_tomorrow_session_slot")
                elif button_text in ["residential", "commercial", "resort", "farm house", "shopping complex", "others",
                                     "architectural design", "interior design", "landscape design", "full house design",
                                     "6:00 pm – 6:30 pm", "6:30 pm – 7:00 pm", "7:00 pm – 7:30 pm",
                                     "9:00 am – 9:30 am", "9:30 am – 10:00 am", "10:00 am – 10:30 am"]:
                    send_template(sender, "get_client_info_after_project_type")
                elif "share my details" in button_text:
                    send_text_message(sender, "Great! Please share your name.")
                    session_data[sender] = {"step": "awaiting_name"}
                elif "start over" in button_text:
                    send_template_with_buttons(sender)
                else:
                    send_text_message(sender, "Sorry, I didn’t understand that. Please select an option from the buttons.")

            elif "text" in message:
                text = message["text"]["body"].strip().lower()
                print("💬 Text received:", text)
                step = session_data.get(sender, {}).get("step")

                if step == "awaiting_name":
                    session_data[sender]["name"] = text
                    session_data[sender]["step"] = "awaiting_email"
                    send_text_message(sender, "Thanks, {0}! Could you please share your email ID?".format(text.title()))

                elif step == "awaiting_email":
                    session_data[sender]["email"] = text
                    session_data[sender]["step"] = "awaiting_location"
                    send_text_message(sender, "Got it. Now please share the project site address.")

                elif step == "awaiting_location":
                    session_data[sender]["location"] = text
                    session_data[sender]["step"] = "awaiting_call_time"
                    send_text_message(sender, "When would be a good time for our architect to call you?")

                elif step == "awaiting_call_time":
                    session_data[sender]["call_time"] = text
                    send_text_message(sender, "Thank you! Our team will contact you shortly. ✨")
                    session_data[sender]["step"] = "done"

                elif "hi" in text or "hello" in text:
                    send_template_with_buttons(sender)
                else:
                    send_text_message(sender, "Hi 👋, please select one of the options from the buttons above to proceed.")

        except Exception as e:
            print("❌ Error in webhook handler:", str(e))

        return "EVENT_RECEIVED", 200
