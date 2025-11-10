Facebook Messenger to BigQuery Data Pipeline

This project provides a scalable, serverless data pipeline to capture all incoming messages from a Facebook Page, process them in real-time, and store them in a Google BigQuery table for analysis.

It uses a decoupled architecture, which is highly resilient and scalable:

Cloud Run (Webhook): A lightweight Flask service receives the webhook from Facebook, verifies its signature, and immediately publishes the raw data to Pub/Sub.

Pub/Sub: Acts as a message broker, holding the messages and ensuring they are not lost.

Cloud Function (Subscriber): A function is triggered by new messages in Pub/Sub, parses the JSON, and streams the data into a BigQuery table.

Architecture

The data flows as follows:

Facebook User → Facebook Page → Meta Webhook → (Service 1) Cloud Run → Pub/Sub Topic → (Service 2) Cloud Function → BigQuery Table

Prerequisites

Before you begin, ensure you have the following:

Google Cloud SDK: The gcloud CLI installed and authenticated (gcloud auth login).

Google Cloud Project: A GCP project with billing enabled.

Facebook Page: A Facebook Page you can administrate.

Meta Developer Account: A developer account at developers.facebook.com.

Code: The webhook_service and subscriber_service directories from this project.

Step-by-Step Setup Guide

We will use the following placeholder names. You can change them, but be consistent.

Pub/Sub Topic ID: facebook-messages

BigQuery Dataset ID: facebook_data

BigQuery Table ID: messages

Step 1: GCP Project Setup

Set your active project:

gcloud config set project YOUR_PROJECT_ID


Enable necessary Google Cloud APIs:

gcloud services enable run.googleapis.com
gcloud services enable pubsub.googleapis.com
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable bigquery.googleapis.com
gcloud services enable iam.googleapis.com


Step 2: Facebook App Setup

This part is done in the Meta Developer Dashboard.

Go to developers.facebook.com and create a new App (App Type: "Business").

From your app dashboard, add the "Messenger" and "Webhooks" products.

Go to Settings > Basic in your app's sidebar.

Save your App Secret. This will be your FB_APP_SECRET.

Create a secure, random string to use as your verify token (e.g., my-strong-secret-token-123). This will be your FB_VERIFY_TOKEN. Do not share this.

Step 3: Create GCP Resources (Pub/Sub & BigQuery)

Create the Pub/Sub Topic:

gcloud pubsub topics create facebook-messages


Create the BigQuery Dataset:

bq mk --dataset YOUR_PROJECT_ID:facebook_data


Create the BigQuery Table:
This command creates the table with the schema our code expects.

bq mk -t facebook_data.messages \
sender_id:STRING,recipient_id:STRING,message_text:STRING,event_timestamp:TIMESTAMP,raw_payload:STRING


Step 4: Deploy Service 1 (Webhook Cloud Run)

This service will receive the messages from Facebook.

Navigate to the webhook_service directory:

cd webhook_service


Deploy to Cloud Run:

Replace YOUR_VERIFY_TOKEN and YOUR_APP_SECRET with the values from Step 2.

--allow-unauthenticated is required so Facebook can send you messages.

gcloud run deploy facebook-webhook-service \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars="FB_VERIFY_TOKEN=YOUR_VERIFY_TOKEN,FB_APP_SECRET=YOUR_APP_SECRET,GCP_PROJECT=YOUR_PROJECT_ID,PUBSUB_TOPIC_ID=facebook-messages" \
  --project=YOUR_PROJECT_ID


After it deploys, copy the Service URL from the output. It will look like https://facebook-webhook-service-xxxx-uc.a.run.app.

Step 5: Deploy Service 2 (Subscriber Cloud Function)

This service listens to Pub/Sub and writes to BigQuery.

Navigate to the subscriber_service directory:

cd ../subscriber_service


Deploy the Cloud Function:
This command deploys a 2nd Gen function that automatically triggers on messages to the facebook-messages topic.

gcloud functions deploy facebook-message-processor \
  --gen2 \
  --runtime python311 \
  --region us-central1 \
  --source . \
  --entry-point process_pubsub_message \
  --trigger-topic facebook-messages \
  --set-env-vars="BQ_DATASET_ID=facebook_data,BQ_TABLE_ID=messages,GCP_PROJECT=YOUR_PROJECT_ID" \
  --project=YOUR_PROJECT_ID


Grant Permissions: The function needs permission to write to BigQuery.

Find the Service Account your function uses (it's in the gcloud functions describe output, but it's usually YOUR_PROJECT_ID@appspot.gserviceaccount.com).

Grant it the BigQuery Data Editor role:

# Get your project number
PROJECT_NUMBER=$(gcloud projects describe YOUR_PROJECT_ID --format="value(projectNumber)")

# This is the default service account for Gen 2 Functions
SERVICE_ACCOUNT_EMAIL="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Add the BigQuery role
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
  --role="roles/bigquery.dataEditor"


Note: If you use a different service account, update the email accordingly.

Step 6: Connect Facebook to Your Webhook

You are now ready to link Facebook to your new Cloud Run service.

Go back to your Meta Developer Dashboard.

Go to Messenger > Settings.

Find the "Webhooks" card and click "Configure".

In "Callback URL", paste the Cloud Run Service URL from Step 4.

In "Verify Token", paste your FB_VERIFY_TOKEN from Step 2.

Click "Verify and Save". You should see a green check.

Click "Add Subscriptions" and select:

messages

messaging_postbacks

Go to the "App Pages" section, link your Facebook Page, and grant permissions.

Final Verification

Your pipeline is now live!

Send a Message: Go to Facebook and send a message to your Page.

Check Cloud Run Logs: (You should see a 200 OK)

gcloud run logs tail facebook-webhook-service --region us-central1 --project=YOUR_PROJECT_ID


Check Cloud Function Logs: (You should see "Successfully inserted... rows")

gcloud functions logs read facebook-message-processor --region us-central1 --limit 50 --project=YOUR_PROJECT_ID


Query BigQuery: (Wait a few seconds, and your data will appear!)

bq query --project_id=YOUR_PROJECT_ID "SELECT * FROM facebook_data.messages LIMIT 10"
