from flask import Flask, request
import requests
import json

app = Flask(__name__)

VERIFY_TOKEN = "navoarch_token"
ACCESS_TOKEN = "EAAOYazi12RkBO43CkBqkvVgCjBeghvJCYymEHMJxZBVuEzZCnRILLVLsQOQgOPfx9L97scNrU1U1Amr4fQBQkg50ixza0AfpBqXtsVSeuXHkaLjXUbagLwvKb2dQ2xyyoeNmh9IK6vZAMuib6ZAmL4RZCNxGxDzWu8QxK8dcXRqyZBFpaRZCqhK35HIR9mWei41AEMyWzm24BSQKJGpbMdjgkykTs37"  # Replace with your latest token
PHONE_NUMBER_ID = "651744254683036"

# In-memory state storage (should ideally be a database)
session_data = {}

def send_template_reply(recipient_number, template_name):
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
            "language": {"code": "en_US"}
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    print("📤 Sent template reply:", response.status_code, response.text)

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
                        from_number = messages[0]["from"]
                        text = messages[0].get("text", {}).get("body", "").strip().lower()

                        user_session = session_data.get(from_number, {"step": "start"})

                        if user_session["step"] == "start":
                            if "plan" in text:
                                send_text_message(from_number, "Great! Let’s help you plan your building project. May I know your name?")
                                session_data[from_number] = {"step": "get_name", "flow": "plan"}
                            elif "home" in text:
                                send_text_message(from_number, "Thanks for choosing home design assistance! What’s your name?")
                                session_data[from_number] = {"step": "get_name", "flow": "home"}
                            elif "talk" in text:
                                send_text_message(from_number, "Sure! May I know your name so our team can reach out?")
                                session_data[from_number] = {"step": "get_name", "flow": "talk"}
                            else:
                                send_text_message(from_number, "Hi 👋, welcome to NAVOARCH! How can we assist you today?\n\n• Plan a Building Project\n• Home Design Assistance\n• Talk to Our Team")

                        elif user_session["step"] == "get_name":
                            user_session["name"] = text
                            send_text_message(from_number, "Thanks, {0}! Could you share your email ID?".format(text.title()))
                            user_session["step"] = "get_email"
                            session_data[from_number] = user_session

                        elif user_session["step"] == "get_email":
                            user_session["email"] = text
                            send_text_message(from_number, "Got it. Can you provide your project site address?")
                            user_session["step"] = "get_address"
                            session_data[from_number] = user_session

                        elif user_session["step"] == "get_address":
                            user_session["address"] = text
                            send_text_message(from_number, "When would be a good time for our architect to call you?")
                            user_session["step"] = "get_schedule"
                            session_data[from_number] = user_session

                        elif user_session["step"] == "get_schedule":
                            user_session["schedule"] = text
                            send_text_message(from_number, "Thank you! Our team will contact you shortly. ✨")
                            print("✅ Client Info:", user_session)
                            session_data[from_number] = {"step": "start"}  # reset session

                            # TODO: Integrate Google Sheets/API

                        else:
                            send_text_message(from_number, "Sorry, I didn’t understand that. Please type your response or choose an option.")

        except Exception as e:
            print("❌ Error while processing message:", e)

        return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
