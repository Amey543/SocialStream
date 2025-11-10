import os
import hmac
import hashlib
from flask import Flask, request
from google.cloud import pubsub_v1

app = Flask(__name__)


FB_VERIFY_TOKEN = os.environ.get('FB_VERIFY_TOKEN')
FB_APP_SECRET = os.environ.get('FB_APP_SECRET')
GCP_PROJECT = os.environ.get('GCP_PROJECT')
PUBSUB_TOPIC_ID = os.environ.get('PUBSUB_TOPIC_ID') 

# Initialize the client once globally
try:
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(GCP_PROJECT, PUBSUB_TOPIC_ID)
except Exception as e:
    print(f"Error initializing Pub/Sub client: {e}")
    publisher = None
    topic_path = None

def verify_signature(req):
    """Verifies the X-Hub-Signature-256 header."""
    signature = req.headers.get("X-Hub-Signature-256")
    if not signature:
        print("Error: X-Hub-Signature-256 header not found.")
        return False
        
    if not FB_APP_SECRET:
        print("Warning: FB_APP_SECRET not configured. Signature verification skipped.")
        return True 

    body = req.get_data()
    expected_hash = hmac.new(FB_APP_SECRET.encode(), msg=body, digestmod=hashlib.sha256).hexdigest()
    expected_signature = f'sha256={expected_hash}'
    
    return hmac.compare_digest(signature, expected_signature)

@app.route('/', methods=['GET', 'POST'])
def webhook():
    
    if request.method == 'GET':
        # --- Webhook Verification ---
        if request.args.get('hub.verify_token') == FB_VERIFY_TOKEN:
            return request.args.get('hub.challenge'), 200
        return 'Invalid verification token', 403

    if request.method == 'POST':
        
        # 1. Verify Signature
        if not verify_signature(request):
            return "Signature mismatch", 403

        # 2. Check Pub/Sub Client
        if not publisher or not topic_path:
            print("Error: Pub/Sub client not initialized.")
            return "Internal Server Error", 500
            
        # 3. Get raw data and publish
        try:
            raw_data = request.get_data()
            
            if raw_data:
                # Publish the raw data directly to Pub/Sub
                future = publisher.publish(topic_path, raw_data)
                future.result() 
            
            return 'OK', 200
        
        except Exception as e:
            print(f"Error processing POST request or publishing: {e}")
            return 'Internal Server Error', 500

    return 'Method Not Allowed', 405

if __name__ == '__main__':
    # This is for local testing only.
    # When deployed to Cloud Run, Gunicorn will be used.
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))