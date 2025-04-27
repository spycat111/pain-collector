from flask import Flask, request, jsonify, send_from_directory
import os
import json
import smtplib
from email.message import EmailMessage

# Serve static files (index.html) from the repo root
app = Flask(__name__, static_folder='.', static_url_path='')

# ——— 1) Load SMTP settings from environment —————————————
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "spycat111@gmail.com")  # your Gmail address
SMTP_PASS = os.getenv("SMTP_PASS", "4kQsspEm7")                     # your App Password
TO_EMAIL   = os.getenv("TO_EMAIL", "spycat111@gmail.com")   # target recipient

# ——— 2) Serve your front-end —————————————————————————————
@app.route('/', methods=['GET'])
def index():
    # Sends index.html from project root
    return send_from_directory('.', 'index.html')

# ——— 3) Data submission endpoint —————————————————————————
@app.route('/submit', methods=['POST'])
def submit():
    data     = request.get_json(force=True)
    features = data.get("features")
    rating   = data.get("rating")
    ts       = data.get("timestamp")

    if features is None or rating is None or ts is None:
        return jsonify({"error": "missing fields"}), 400

    # Prepare email
    msg = EmailMessage()
    msg['Subject'] = f"Pain Data Submission @ {ts}"
    msg['From']    = SMTP_USER or f"noreply@{SMTP_HOST}"
    msg['To']      = TO_EMAIL

    body = {
        "timestamp":     ts,
        "rating":        rating,
        "num_features":  len(features)
        # you can include more fields here
    }
    msg.set_content(json.dumps(body, indent=2))

    # Send via SMTP
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            if SMTP_PORT == 587:
                smtp.starttls()
            if SMTP_USER and SMTP_PASS:
                smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
    except Exception as e:
        return jsonify({"error": f"SMTP send failed: {e}"}), 500

    return jsonify({"status":"ok"}), 200

# ——— 4) Run the app ——————————————————————————————————————
if __name__ == '__main__':
    # On Render.com or similar, the PORT env var will be set automatically
    port = int(os.getenv("PORT", "8000"))
    app.run(host='0.0.0.0', port=port)
