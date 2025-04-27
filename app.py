import os
import json
import smtplib
from flask import Flask, request, jsonify, send_from_directory
from email.message import EmailMessage

# Create the Flask app without a dedicated static folder,
# so we can serve from the working directory.
app = Flask(__name__, static_folder=None)

# ——— Load SMTP settings from the environment —————————————
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "spycat111@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "")
TO_EMAIL   = os.getenv("TO_EMAIL", "spycat111@gmail.com")

# ——— Serve index.html at the root URL —————————————————————————
@app.route('/', methods=['GET'])
def index():
    # Use the current working directory to find index.html
    return send_from_directory(os.getcwd(), 'index.html')

# ——— Submission endpoint —————————————————————————————
@app.route('/submit', methods=['POST'])
def submit():
    data     = request.get_json(force=True)
    features = data.get("features")
    rating   = data.get("rating")
    ts       = data.get("timestamp")

    if features is None or rating is None or ts is None:
        return jsonify({"error": "missing fields"}), 400

    # Build the email
    msg = EmailMessage()
    msg['Subject'] = f"Pain Data Submission @ {ts}"
    msg['From']    = SMTP_USER or f"noreply@{SMTP_HOST}"
    msg['To']      = TO_EMAIL
    body = {
        "timestamp":    ts,
        "rating":       rating,
        "num_features": len(features)
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

    return jsonify({"status": "ok"}), 200

# ——— Fallback: serve any other file from the CWD —————————————————
@app.route('/<path:filename>', methods=['GET'])
def serve_file(filename):
    file_path = os.path.join(os.getcwd(), filename)
    if os.path.isfile(file_path):
        return send_from_directory(os.getcwd(), filename)
    # If the file doesn’t exist, just return index.html
    return send_from_directory(os.getcwd(), 'index.html')

# ——— Start the app ——————————————————————————————————————
if __name__ == '__main__':
    port = int(os.getenv("PORT", "8000"))
    app.run(host='0.0.0.0', port=port)
