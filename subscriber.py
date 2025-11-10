import os
import json
import base64
from google.cloud import bigquery

# --- Environment Variables ---
# GCP_PROJECT is provided by the Cloud Functions environment
GCP_PROJECT = os.environ.get('GCP_PROJECT') 
BQ_DATASET_ID = os.environ.get('BQ_DATASET_ID')
BQ_TABLE_ID = os.environ.get('BQ_TABLE_ID')

# --- Global BigQuery Client ---
# Initialize the client once globally
try:
    bq_client = bigquery.Client()
except Exception as e:
    print(f"Error initializing BigQuery client: {e}")
    bq_client = None

def parse_webhook_data(data):
    """Parses the Facebook webhook payload and extracts message data."""
    rows_to_insert = []
    
    # Facebook webhook data is nested.
    if data.get("object") == "page":
        for entry in data.get("entry", []):
            for message_event in entry.get("messaging", []):
                
                # We only care about text messages for this example
                if "message" in message_event and "text" in message_event["message"]:
                    
                    sender_id = message_event["sender"]["id"]
                    recipient_id = message_event["recipient"]["id"]
                    message_text = message_event["message"]["text"]
                    
                    # Convert Facebook's millisecond timestamp to a BQ-compatible
                    # floating-point number (seconds)
                    event_timestamp = message_event["timestamp"] / 1000.0

                    # Create a dictionary (row) for BigQuery
                    rows_to_insert.append({
                        "sender_id": sender_id,
                        "recipient_id": recipient_id,
                        "message_text": message_text,
                        "event_timestamp": event_timestamp,
                        "raw_payload": json.dumps(message_event) # Store the raw event just in case
                    })
                    
    return rows_to_insert

def process_pubsub_message(event, context):
    
    if not bq_client:
        print("Error: BigQuery client not initialized. Cannot process message.")
        return 

    try:
        # Pub/Sub data is base64 encoded.
        raw_data = base64.b64decode(event['data']).decode('utf-8')
        data = json.loads(raw_data)

        # 1. Parse data to find messages
        rows_to_insert = parse_webhook_data(data)

        if not rows_to_insert:
            print("No insertable text messages found in this payload.")
            return 

        # 2. Insert into BigQuery
        table_id = f"{GCP_PROJECT}.{BQ_DATASET_ID}.{BQ_TABLE_ID}"
        
        errors = bq_client.insert_rows_json(table_id, rows_to_insert)
        
        if not errors:
            print(f"Successfully inserted {len(rows_to_insert)} rows.")
        else:
            print(f"Encountered errors while inserting rows: {errors}")
        
            raise Exception(f"BigQuery insert errors: {errors}")

    except Exception as e:
        print(f"Error processing message: {e}")
        # Raise the exception to force Pub/Sub to retry
        raise