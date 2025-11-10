# Facebook Messenger to BigQuery Data Pipeline

This project provides a scalable, serverless data pipeline to capture all incoming messages from a Facebook Page, process them in real-time, and store them in a Google BigQuery table for analysis.

## 🚀 Key Features

🛡️ Resilient & Decoupled: Uses a Pub/Sub buffer to ensure no messages are lost, even if the BigQuery ingestor is temporarily down.

⚡ Real-Time Processing: Messages are processed and inserted into BigQuery within seconds of being received by the Facebook Page.

🔄 Scalable Ingestion: The Cloud Run webhook service can automatically scale to handle massive bursts of incoming messages from Facebook.

🔒 Secure: Implements Facebook's X-Hub-Signature-256 HMAC verification to ensure all incoming webhooks are authentic.

## 🛠️ Technologies Used

Cloud Platform: Google Cloud

Webhook Service (Service 1):

Python 3.11

Flask & Gunicorn

Google Cloud Run (Serverless)

Google Cloud Pub/Sub

Processing Service (Service 2):

Python 3.11

Flask & Gunicorn

Google Cloud Run (Serverless)

Google Cloud BigQuery

## Data Source:

Meta for Developers (Facebook Page & Messenger Webhooks)

## 📐 Architecture

The data flows as follows:

The Cloud Run (Webhook) service receives the data, verifies the signature, and publishes the raw payload to a Pub/Sub topic.

A Pub/Sub Push Subscription immediately forwards the message to the Cloud Run (Subscriber) service.

The Cloud Run (Subscriber) service parses the JSON and streams the structured data into BigQuery.

Data is now available for analysis in the BigQuery Table.

## 📋 Setup & Deployment Steps

This outlines the high-level process for deploying this architecture. To get the exact deployment steps with CLI commands, copy and paste the text below into any LLM such as ChatGPT.

Step 1: Google Cloud Project Setup

Enable all necessary APIs: Cloud Run, Pub/Sub, Cloud Functions, BigQuery, Cloud Build, and IAM.

Step 2: Facebook App Setup

Create a Meta Developer App and add the Messenger and Webhooks products.

Securely note your App Secret and create a Verify Token.

Step 3: Create GCP Resources

Create a Pub/Sub Topic (e.g., facebook-messages) to act as the message buffer.

Create a BigQuery Dataset (e.g., facebook_data) to hold your data.

Create a BigQuery Table (e.g., messages) with the correct schema: sender_id, recipient_id, message_text, event_timestamp, and raw_payload.

Step 4: Deploy Service 2 (Subscriber Cloud Run)

Deploy the subscriber_service code to Cloud Run (e.g., facebook-subscriber-service).

Set the necessary environment variables (GCP_PROJECT, BQ_DATASET_ID, BQ_TABLE_ID).

Important: This service should NOT allow unauthenticated invocations (--no-allow-unauthenticated). This service should only be callable by Pub/Sub.

Note the deployed Service URL.

Step 5: Create Pub/Sub Push Subscription

Create a Pub/Sub Push Subscription that listens to the topic from Step 3.

Set the Push Endpoint to the Service 2 URL from Step 4.

You will need to create a dedicated Service Account for Pub/Sub to use and grant it the "Cloud Run Invoker" IAM role for your new facebook-subscriber-service.

Step 6: Deploy Service 1 (Webhook Cloud Run)

Deploy the webhook_service code to Cloud Run (e.g., facebook-webhook-service).

Set the necessary environment variables (FB_VERIFY_TOKEN, FB_APP_SECRET, GCP_PROJECT, PUBSUB_TOPIC_ID).

Ensure the service allows unauthenticated invocations so Facebook can reach it.

Note the deployed Service URL.

Step 7: Connect Facebook to Your Webhook

In the Meta Developer Dashboard, go to Messenger > Settings.

In the "Webhooks" section, paste the Cloud Run Service URL from Step 6 and your Verify Token from Step 2.

Verify and Save, then subscribe to the messages and messaging_postbacks feeds.

Link your app to your desired Facebook Page.
