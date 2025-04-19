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
    print("\U0001F4E4 Sent template with buttons:", response.status_code, response.text)

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
    print("\U0001F4E4 Sent text message:", response.status_code, response.text)

def send_schedule_buttons(recipient_number):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "When would be a good time for our architect to call you?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "call_today_evening", "title": "Today Evening"}},
                    {"type": "reply", "reply": {"id": "call_tomorrow_morning", "title": "Tomorrow Morning"}},
                    {"type": "reply", "reply": {"id": "custom_time", "title": "Choose Custom Time"}}
                ]
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("\U0001F4E4 Sent schedule button:", response.status_code, response.text)

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
                        from_number = messages[0]["from"]
                        text = messages[0].get("text", {}).get("body", "").strip().lower()
                        interactive = messages[0].get("interactive", {}).get("button_reply", {}).get("id")

                        user_session = session_data.get(from_number, {"step": "start"})

                        if user_session["step"] == "start":
                            if interactive:
                                if interactive == "plan_project":
                                    send_text_message(from_number, "Great! Let's plan your building project. What's your name?")
                                    session_data[from_number] = {"step": "get_name", "flow": "plan"}
                                elif interactive == "home_design":
                                    send_text_message(from_number, "Awesome! What’s your name so we can assist with home design?")
                                    session_data[from_number] = {"step": "get_name", "flow": "home"}
                                elif interactive == "talk_team":
                                    send_text_message(from_number, "Sure! Can I have your name so our team can reach out?")
                                    session_data[from_number] = {"step": "get_name", "flow": "talk"}
                                else:
                                    send_template_with_buttons(from_number)
                            else:
                                send_template_with_buttons(from_number)

                        elif user_session["step"] == "get_name":
                            user_session["name"] = text
                            send_text_message(from_number, f"Thanks, {text.title()}! What’s your email ID?")
                            user_session["step"] = "get_email"
                            session_data[from_number] = user_session

                        elif user_session["step"] == "get_email":
                            user_session["email"] = text
                            send_text_message(from_number, "Got it! Could you share your project site address?")
                            user_session["step"] = "get_address"
                            session_data[from_number] = user_session

                        elif user_session["step"] == "get_address":
                            user_session["address"] = text
                            send_schedule_buttons(from_number)
                            user_session["step"] = "get_schedule"
                            session_data[from_number] = user_session

                        elif user_session["step"] == "get_schedule":
                            if "today" in text:
                                now = datetime.now()
                                hour = now.hour
                                if hour < 17:
                                    send_text_message(from_number, "We can arrange a callback between 6 PM – 8 PM today. Let us know if that works.")
                                else:
                                    send_text_message(from_number, "It's a bit late today. Can we schedule for tomorrow morning instead?")
                            elif "tomorrow" in text:
                                send_text_message(from_number, "Our architect will call between 10 AM – 12 PM tomorrow.")
                            elif "other" in text or "custom" in text:
                                send_text_message(from_number, "Please type your preferred day and time (e.g., 'Monday 3 PM').")
                                user_session["step"] = "manual_schedule"
                                session_data[from_number] = user_session
                                return "EVENT_RECEIVED", 200

                            send_text_message(from_number, "Thank you! Our team will contact you shortly. ✨")
                            print("✅ Client Info:", user_session)
                            session_data[from_number] = {"step": "start"}

                        elif user_session.get("step") == "manual_schedule":
                            user_session["custom_time"] = text
                            send_text_message(from_number, f"Thank you! We've noted '{text}' as your preferred call time. ✨")
                            print("✅ Client Info:", user_session)
                            session_data[from_number] = {"step": "start"}

                        else:
                            send_text_message(
                                from_number,
                                "Sorry, I didn’t understand that. Please type your reply clearly or send 'menu' to restart."
                            )

        except Exception as e:
            print("❌ Error while processing message:", e)

        return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
