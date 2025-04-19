from flask import Flask, request
import json

app = Flask(__name__)

# Your verification token (must match what's set in Meta Webhook Verify Token)
VERIFY_TOKEN = "navoarch_token"

@app.route("/webhook", methods=["GET", "POST"])
def webhook():
    if request.method == "GET":
        # Handle the webhook verification from Meta
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")
        
        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook verified successfully!")
            return challenge, 200
        else:
            print("❌ Webhook verification failed.")
            return "Forbidden", 403

    if request.method == "POST":
        # Handle incoming webhook notification
        data = request.get_json()
        print("📥 Webhook Received:\n", json.dumps(data, indent=2))
        
        # Optional: Save to log file (disabled on Render free tier but useful in dev)
        # with open("webhook_events.log", "a") as f:
        #     f.write(json.dumps(data) + "\n")
        
        return "EVENT_RECEIVED", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
