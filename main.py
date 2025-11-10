import os
import json
import hmac
import hashlib
from flask import Flask, request
from google.cloud import pubsub_v1

app = Flask(__name__)

# --- Environment Variables ---
FB_VERIFY_TOKEN = os.environ.get('FB_VERIFY_TOKEN')
FB_APP_SECRET = os.environ.get('FB_APP_SECRET')
GCP_PROJECT = os.environ.get('GCP_PROJECT')
TOPIC_ID = os.environ.get('TOPIC_ID')

# --- Global Pub/Sub Client ---
publisher = None
topic_path = None

def verify_signature(req):
    """Verifies the X-Hub-Signature-256 header."""
    signature = req.headers.get("X-Hub-Signature-256")
    if not signature or not FB_APP_SECRET:
        print("Warning: FB_APP_SECRET not configured or signature not present.")
        return False

    body = req.get_data()
    expected = 'sha256=' + hmac.new(FB_APP_SECRET.encode(), msg=body, digestmod=hashlib.sha256).hexdigest()
    return hmac.compare_digest(signature, expected)

def initialize_pubsub():
    """Initializes the Pub/Sub client."""
    global publisher, topic_path
    if publisher is None:
        if not GCP_PROJECT or not TOPIC_ID:
            raise ValueError("Server configuration error: Missing GCP_PROJECT or TOPIC_ID.")
        publisher = pubsub_v1.PublisherClient()
        topic_path = publisher.topic_path(GCP_PROJECT, TOPIC_ID)

@app.route('/', methods=['GET', 'POST'])
def webhook():
    """Handles webhook verification and publishes the raw payload to Pub/Sub."""
    if request.method == 'GET':
        if request.args.get('hub.verify_token') == FB_VERIFY_TOKEN:
            return request.args.get('hub.challenge'), 200
        return 'Invalid verification token', 403

    if request.method == 'POST':
        if not verify_signature(request):
            return "Signature mismatch", 403

        try:
            initialize_pubsub()
            # Get the raw request body as bytes
            raw_data = request.get_data()
            
            # Publish the raw data directly
            if raw_data:
                publisher.publish(topic_path, raw_data).result()

            return 'OK', 200
        except Exception as e:
            print(f"Error processing POST request: {e}")
            return 'Internal Server Error', 500

    return 'Method Not Allowed', 405