from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "navoarch_token"
ACCESS_TOKEN = "EAAOYazi12RkBOxOnHvlvnvT1JZCbwSNBSNQ6UzTk40W0RC8g8Tlbpokk3xvfT0Cd8PyFFDsr4KgwLoWo9YDrE6Qkl1QzM2raI6dFBKoePcKRGeM4ZAV7WOIYcr1sdapjjhhjW666lYTl4TqOJLj8NPwSBJ93VUAKivdf7ejsN8ZAoND5JZCczNC3VGq4DZBw37jDJj5pCavAoqsqtPbJXfSSF4nsZD"  # Replace with your permanent access token
PHONE_NUMBER_ID = "651744254683036"

session_data = {}  # In-memory storage for conversation

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
    r = requests.post(url, headers=headers, json=payload)
    print(f"📤 Sent template `{template_name}` ->", r.status_code, r.text)

def send_text(recipient, message):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient,
        "type": "text",
        "text": {"body": message}
    }
    r = requests.post(url, headers=headers, json=payload)
    print("📤 Sent text ->", r.status_code, r.text)

def send_welcome(recipient):
    send_template(recipient, "navoarch_welcome_01")
    session_data[recipient] = {"step": "await_choice"}

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        if (request.args.get("hub.mode") == "subscribe" and
            request.args.get("hub.verify_token") == VERIFY_TOKEN):
            return request.args.get("hub.challenge"), 200
        return "Unauthorized", 403

    data = request.get_json()
    print("📥 Webhook:", json.dumps(data, indent=2))

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]

        if "interactive" in message:
            button_id = message["interactive"]["button_reply"]["id"]
            print("🔘 Button clicked:", button_id)

            match button_id:
                case "plan_project":
                    send_template(sender, "send_project_type_buttons")
                case "home_design":
                    send_template(sender, "send_home_design_type_buttons")
                case "talk_team":
                    send_template(sender, "send_schedule_buttons")
                case "today":
                    send_template(sender, "confirm_today_evening")
                case "tomorrow":
                    send_template(sender, "send_tomorrow_session_slot")
                case "start_over":
                    send_welcome(sender)
                case "share_details":
                    send_text(sender, "Great! What is your name?")
                    session_data[sender] = {"step": "get_name"}
                case _ if button_id in [
                    "residential", "commercial", "resort", "farm_house", "shopping_complex", "others",
                    "architectural_design", "interior_design", "landscape_design", "full_house_design",
                    "slot_6_6_30", "slot_6_30_7", "slot_7_7_30",
                    "slot_9_9_30", "slot_9_30_10", "slot_10_10_30"
                ]:
                    send_template(sender, "get_client_info_after_project_type")
                case _:
                    send_text(sender, "❓ Not sure what you meant. Please use the button options.")
        elif "text" in message:
            msg = message["text"]["body"].strip()
            step = session_data.get(sender, {}).get("step")

            if step == "get_name":
                session_data[sender]["name"] = msg
                session_data[sender]["step"] = "get_email"
                send_text(sender, f"Thanks, {msg}! Now, may I have your email ID?")
            elif step == "get_email":
                session_data[sender]["email"] = msg
                session_data[sender]["step"] = "get_site"
                send_text(sender, "Got it! Please share the site location/address.")
            elif step == "get_site":
                session_data[sender]["site"] = msg
                session_data[sender]["step"] = "get_time"
                send_text(sender, "Perfect. When can our architect call you?")
            elif step == "get_time":
                session_data[sender]["time"] = msg
                session_data[sender]["step"] = "done"
                send_text(sender, "✅ Thank you! We’ll connect with you soon. ✨")
            elif "hi" in msg.lower() or "hello" in msg.lower():
                send_welcome(sender)
            else:
                send_text(sender, "Hi 👋, please tap on one of the buttons to proceed.")

    except Exception as e:
        print("❌ Error in webhook:", str(e))

    return "OK", 200
