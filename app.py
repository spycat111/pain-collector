import os, json, smtplib
from flask import Flask, request, jsonify, send_from_directory
from email.message import EmailMessage

# Serve files from the project root
app = Flask(__name__, static_folder=None)

# ——— Load all SMTP settings from environment —————————————
SMTP_HOST = os.environ["SMTP_HOST"]   # e.g. smtp.gmail.com
SMTP_PORT = int(os.environ["SMTP_PORT"])   # e.g. "587"
SMTP_USER = os.environ["SMTP_USER"]   # your email address
SMTP_PASS = os.environ["SMTP_PASS"]   # your App-Password or SMTP auth token
TO_EMAIL  = os.environ["TO_EMAIL"]    # where submissions get sent

@app.route('/', methods=['GET'])
def index():
    return send_from_directory(os.getcwd(), 'index.html')

@app.route('/submit', methods=['POST'])
def submit():
    data     = request.get_json(force=True)
    features = data.get("features")
    rating   = data.get("rating")
    ts       = data.get("timestamp")

    if features is None or rating is None or ts is None:
        return jsonify({"error": "missing fields"}), 400

    # Compose email
    msg = EmailMessage()
    msg['Subject'] = f"Pain Data Submission @ {ts}"
    msg['From']    = SMTP_USER
    msg['To']      = TO_EMAIL
    msg.set_content(json.dumps({
        "timestamp":    ts,
        "rating":       rating,
        "num_features": len(features)
    }, indent=2))

    # Send via SMTP
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_PASS)
            smtp.send_message(msg)
    except Exception as e:
        return jsonify({"error": f"SMTP send failed: {e}"}), 500

    return jsonify({"status":"ok"}), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", "8000"))
    app.run(host='0.0.0.0', port=port)
