from flask import Flask, request, jsonify
import requests
import json
from datetime import datetime
import hashlib
import logging

app = Flask(__name__)

# Configuration
VERIFY_TOKEN = "navoarch_token"
ACCESS_TOKEN = "EAAOYazi12RkBO0g7aqBsWNeycB0CkuP1cmt6YXUgOFzJvim6PaQ7FrZCCNFtIradZAwjk8uKbipjgnkVQFQRWAvZBSSOSCMKopGZBj37OJsTg2VJTBt7Tp0FX3V5rGWQPam0tNdxqAaU7VrFwGegbJcKaRhGq57uvPzao2sYgpZAJVE07kqXY3WaPrtF0IS1urcxke69bdRmLZA6tGJ97I9FhvdxsZD"
PHONE_NUMBER_ID = "651744254683036"

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Persistent session storage (replace with database in production)
session_data = {}

# Button mappings for reliable matching
BUTTON_MAPPINGS = {
    "plan_a_building_project": "navoarch_welcome_01:0",
    "home_design_assistance": "navoarch_welcome_01:1",
    "talk_to_our_team": "navoarch_welcome_01:2",
    "residential": "send_project_type_buttons:0",
    "commercial": "send_project_type_buttons:1",
    "resort": "send_project_type_buttons:2",
    "farm_house": "send_project_type_buttons:3",
    "shopping_complex": "send_project_type_buttons:4",
    "others": "send_project_type_buttons:5",
    "architectural": "send_home_design_type_buttons:0",
    "interior": "send_home_design_type_buttons:1",
    "landscape": "send_home_design_type_buttons:2",
    "full_house": "send_home_design_type_buttons:3",
    "today": "send_schedule_buttons:0",
    "tomorrow": "send_schedule_buttons:1"
}

def get_button_id(button_text):
    """Convert button text to consistent ID"""
    clean_text = button_text.strip().lower().replace(" ", "_").replace("–", "").replace(":", "")
    return BUTTON_MAPPINGS.get(clean_text, None)

def send_message(recipient_number, message_type, content):
    """Generic message sender with error handling"""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "type": message_type
    }

    if message_type == "template":
        payload["template"] = {
            "name": content,
            "language": {"code": "en"}
        }
    else:  # text message
        payload["text"] = {"body": content}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        logger.info(f"Message sent to {recipient_number}: {content}")
        return True
    except Exception as e:
        logger.error(f"Failed to send message: {str(e)}")
        return False

def handle_new_session(sender):
    """Initialize or reset user session"""
    session_data[sender] = {
        "step": "main_menu",
        "data": {},
        "last_interaction": datetime.now().isoformat()
    }
    send_message(sender, "template", "navoarch_welcome_01")

def save_lead_data(sender):
    """Save collected data to your database (placeholder)"""
    data = session_data.get(sender, {})
    logger.info(f"Lead data for {sender}: {json.dumps(data, indent=2)}")
    # TODO: Implement actual database storage

def handle_button_click(sender, button_text):
    """Process button interactions with state management"""
    session = session_data.get(sender, {})
    button_id = get_button_id(button_text)

    if not button_id:
        send_message(sender, "text", "Sorry, I didn't understand that option. Please try again.")
        return

    template_name, _ = button_id.split(":")

    # Main menu handling
    if session.get("step") == "main_menu":
        if "plan_a_building_project" in button_id:
            send_message(sender, "template", "send_project_type_buttons")
            session["step"] = "project_type_selected"
        elif "home_design_assistance" in button_id:
            send_message(sender, "template", "send_home_design_type_buttons")
            session["step"] = "design_type_selected"
        elif "talk_to_our_team" in button_id:
            send_message(sender, "template", "send_schedule_buttons")
            session["step"] = "scheduling"

    # Project type selection
    elif session.get("step") == "project_type_selected":
        session["data"]["project_type"] = button_text
        send_message(sender, "template", "get_client_info_after_project_type")
        session["step"] = "collecting_details"

    # Schedule handling
    elif session.get("step") == "scheduling":
        if "today" in button_id:
            send_message(sender, "template", "confirm_today_evening")
            session["step"] = "time_selection"
            session["data"]["day"] = "today"
        elif "tomorrow" in button_id:
            send_message(sender, "template", "send_tomorrow_session_slot")
            session["step"] = "time_selection"
            session["data"]["day"] = "tomorrow"

    # Time slot selection
    elif session.get("step") == "time_selection":
        session["data"]["time_slot"] = button_text
        send_message(sender, "text", "Please share your name to proceed.")
        session["step"] = "awaiting_name"

    # Update session
    session_data[sender] = session

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode == "subscribe" and token == VERIFY_TOKEN:
            logger.info("Webhook verified successfully")
            return challenge, 200
        return "Forbidden", 403

    if request.method == "POST":
        try:
            data = request.get_json()
            logger.debug(f"Incoming webhook data: {json.dumps(data, indent=2)}")

            entry = data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            message = value.get("messages", [{}])[0]
            sender = message.get("from")

            if not sender:
                return "Invalid request", 400

            # Initialize session if new user
            if sender not in session_data:
                handle_new_session(sender)

            # Handle button clicks
            if "interactive" in message:
                button_text = message["interactive"]["button_reply"]["title"]
                logger.info(f"Button click from {sender}: {button_text}")
                handle_button_click(sender, button_text)

            # Handle text messages
            elif "text" in message:
                text = message["text"]["body"].strip()
                session = session_data.get(sender, {})
                logger.info(f"Text message from {sender} at step {session.get('step')}: {text}")

                # Conversation flow
                if session.get("step") == "awaiting_name":
                    session["data"]["name"] = text
                    session["step"] = "awaiting_email"
                    send_message(sender, "text", f"Thanks, {text.title()}! Please share your email address.")
                
                elif session.get("step") == "awaiting_email":
                    if "@" in text and "." in text:  # Basic email validation
                        session["data"]["email"] = text
                        session["step"] = "awaiting_location"
                        send_message(sender, "text", "Please share your project location (city/area).")
                    else:
                        send_message(sender, "text", "Please enter a valid email address.")
                
                elif session.get("step") == "awaiting_location":
                    session["data"]["location"] = text
                    session["step"] = "complete"
                    send_message(sender, "text", "Thank you! Our team will contact you shortly. 🏡")
                    save_lead_data(sender)
                    handle_new_session(sender)  # Reset conversation
                
                # Global commands
                elif text.lower() in ["hi", "hello", "start over"]:
                    handle_new_session(sender)
                elif text.lower() == "menu":
                    send_message(sender, "template", "navoarch_welcome_01")
                    session["step"] = "main_menu"
                else:
                    send_message(sender, "text", "Please select an option from the menu to proceed.")

                # Update session
                session_data[sender] = session

        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500

        return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
