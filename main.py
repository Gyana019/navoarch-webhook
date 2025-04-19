from flask import Flask, request
import requests
import json
from datetime import datetime

app = Flask(__name__)

VERIFY_TOKEN = "navoarch_token"
ACCESS_TOKEN = "EAAOYazi12RkBO2tpoVJkorQXNhLJYFCxXisUL3UGVkZBSszWX1ifjsBLLcZBL6FloT3I8EZALCqg2U45HoeZB6gjEPZByRea1DSA1eFq7HhuJ0801Qj25XOVMLqmyHeZCV3SReINFgyeUyua77OO4bJGtQoZBQnQrBUrVJdLPgJs1HZBC0UZCxa67h9PbefUmJMtZACxFDMTykRAOWyXGoNMzHfB5IK0gZD"  # Replace with your permanent token
PHONE_NUMBER_ID = "651744254683036"

# In-memory state storage (should ideally be a database)
session_data = {}

def send_template_with_buttons(recipient_number):
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
            "language": {"code": "en"}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Sent template with buttons:", response.status_code, response.text)

    session_data[recipient_number] = {"step": "await_main_choice", "template_sent": True}

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

def send_project_type_buttons(recipient_number):
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
            "name": "send_project_type_buttons",
            "language": {"code": "en"}
        }
    }
    requests.post(url, headers=headers, json=payload)

def send_design_type_buttons(recipient_number):
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
            "name": "send_home_design_type_buttons",
            "language": {"code": "en"}
        }
    }
    requests.post(url, headers=headers, json=payload)

def send_schedule_buttons(recipient_number):
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
            "name": "send_schedule_buttons",
            "language": {"code": "en"}
        }
    }
    requests.post(url, headers=headers, json=payload)

def send_tomorrow_session_slot(recipient_number):
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
            "name": "send_tomorrow_session_slot",
            "language": {"code": "en"}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Sent tomorrow time slots:", response.status_code, response.text)

def send_get_client_info_template(recipient_number):
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
            "name": "get_client_info_after_project_type",
            "language": {"code": "en"}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Sent info collection message:", response.status_code, response.text)

def send_confirm_today_evening(recipient_number):
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
            "name": "confirm_today_evening",
            "language": {"code": "en"}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Sent confirm today evening slots:", response.status_code, response.text)

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
                reply_id = message["interactive"]["button_reply"]["id"]
                print("🔘 Button clicked:", reply_id)

                if reply_id == "plan_project":
                    send_project_type_buttons(sender)
                elif reply_id == "home_design":
                    send_design_type_buttons(sender)
                elif reply_id == "talk_team":
                    send_schedule_buttons(sender)
                elif reply_id == "today_evening":
                    send_confirm_today_evening(sender)
                elif reply_id == "tomorrow":
                    send_tomorrow_session_slot(sender)
                elif reply_id == "residential_project":
                    send_get_client_info_template(sender)
                elif reply_id == "share_client_info":
                    send_get_client_info_template(sender)
                else:
                    send_text_message(sender, "Sorry, I didn’t understand that. Please select an option from the buttons.")

            elif "text" in message:
                text = message["text"]["body"].lower()
                print("💬 Text received:", text)
                if "hi" in text or "hello" in text:
                    send_template_with_buttons(sender)
                else:
                    send_text_message(sender, "Hi 👋, please select one of the options from the buttons above to proceed.")

        except Exception as e:
            print("❌ Error in webhook handler:", str(e))

        return "EVENT_RECEIVED", 200
