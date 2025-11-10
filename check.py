import hmac
import hashlib
import json

# Your current App Secret
app_secret = "xxxxxxxxxxxxxxxxxx"

# The dictionary representing the JSON payload
payload_dict ={"object":"page","entry":[{"id":"PAGE_ID","time":1678886400000,"messaging":[{"sender":{"id":"USER_SENDER_ID"},"recipient":{"id":"YOUR_PAGE_ID"},"timestamp":1678886400123,"message":{"mid":"m_mid.123456789","text":"This is a test message from a user."}}]}]}

# Convert the dictionary to a compact JSON string (without spaces)
request_body = json.dumps(payload_dict, separators=(',', ':'))

# Calculate the hash
expected_signature = hmac.new(
    app_secret.encode('utf-8'),
    msg=request_body.encode('utf-8'),
    digestmod=hashlib.sha256
).hexdigest()

print("--- Generated Signature ---")
print(f"sha256={expected_signature}")
