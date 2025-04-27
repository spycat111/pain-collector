import os, json, smtplib, logging
from flask import Flask, request, jsonify, send_from_directory
from email.message import EmailMessage

# ——— Setup logging to stdout —————————————————————————————
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder=None)

# Load SMTP settings from environment
SMTP_HOST = os.environ["SMTP_HOST"]
SMTP_PORT = int(os.environ["SMTP_PORT"])
SMTP_USER = os.environ["SMTP_USER"]
SMTP_PASS = os.environ["SMTP_PASS"]
TO_EMAIL  = os.environ["TO_EMAIL"]

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
        logging.error("Submit missing fields: %s", data)
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

    # Send via SMTP, with logging
    try:
        logging.info("Connecting to SMTP %s:%d", SMTP_HOST, SMTP_PORT)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
            if SMTP_PORT == 587:
                smtp.starttls()
                logging.info("Started TLS")
            smtp.login(SMTP_USER, SMTP_PASS)
            logging.info("Logged in as %s", SMTP_USER)
            smtp.send_message(msg)
        logging.info("Email sent to %s for timestamp %s", TO_EMAIL, ts)
    except Exception as e:
        logging.exception("SMTP send failed")
        return jsonify({"error": f"SMTP send failed: {e}"}), 500

    return jsonify({"status":"ok"}), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", "8000"))
    logging.info("Starting app on port %d", port)
    app.run(host='0.0.0.0', port=port)
