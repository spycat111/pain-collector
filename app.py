import os
import json
import logging
import smtplib
from flask import Flask, request, jsonify, send_from_directory
from email.message import EmailMessage

logging.basicConfig(level=logging.INFO)
app = Flask(__name__, static_folder=None)

SMTP_HOST = os.environ["SMTP_HOST"]      # e.g. smtp.stackmail.com
SMTP_PORT = int(os.environ["SMTP_PORT"]) # 465 or 587
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
        return jsonify(error="missing fields"), 400

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
            # SSL port
            smtp = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)
            logging.info("Using SMTP_SSL")
        else:
            # TLS port (587)
            smtp = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            logging.info("Started TLS")

        smtp.login(SMTP_USER, SMTP_PASS)
        logging.info("Logged in as %s", SMTP_USER)
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
