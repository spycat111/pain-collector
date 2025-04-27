import os
import json
import logging
import smtplib
import base64
from flask import Flask, request, jsonify, send_from_directory
from email.message import EmailMessage

logging.basicConfig(level=logging.INFO)
app = Flask(__name__, static_folder=None)

# Load SMTP settings from env
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
    if None in (features, rating, ts):
        logging.error("Missing fields in submission: %s", data)
        return jsonify(error="missing fields"), 400

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

    try:
        logging.info("Connecting to SMTP %s:%d", SMTP_HOST, SMTP_PORT)
        if SMTP_PORT == 465:
            smtp = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
            logging.info("Using SMTP_SSL")
        else:
            smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            logging.info("Started TLS")

        # Explicit AUTH PLAIN (bypasses CRAM-MD5)
        auth_str = "\0" + SMTP_USER + "\0" + SMTP_PASS
        auth_b64 = base64.b64encode(auth_str.encode('utf-8')).decode('ascii')
        code, resp = smtp.docmd("AUTH PLAIN " + auth_b64)
        logging.info("AUTH PLAIN response: %s %s", code, resp)

        smtp.send_message(msg)
        smtp.quit()
        logging.info("Email sent to %s for timestamp %s", TO_EMAIL, ts)

    except Exception:
        logging.exception("SMTP send failed")
        return jsonify(error="SMTP send failed"), 500

    return jsonify(status="ok"), 200

if __name__ == '__main__':
    port = int(os.getenv("PORT", "8000"))
    logging.info("Starting on port %d", port)
    app.run(host='0.0.0.0', port=port)
