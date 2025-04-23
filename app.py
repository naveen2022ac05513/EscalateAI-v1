# EscalateAI.py
# High-level implementation outline for EscalateAI with Outlook email fetching every hour

import uuid
import smtplib
import datetime
import os
import json
from typing import List, Dict
from collections import defaultdict

from transformers import pipeline
from sklearn.externals import joblib  # for saving/loading models
from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import JSONResponse
import uvicorn

from msal import ConfidentialClientApplication
import requests
from apscheduler.schedulers.blocking import BlockingScheduler

# === Configuration === #
ESCALATION_ID_PREFIX = "SESICE-"
DATA_FILE = "escalations_db.json"
CLIENT_ID = 8df1bf10-bf08-4ce9-8078-c387d17aa785
CLIENT_SECRET = 169948a0-3581-449d-9d8c-f4f54160465d
TENANT_ID = f8cdef31-a31e-4b4a-93e4-5f571e91255a
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
SCOPE = ["https://graph.microsoft.com/.default"]
USER_LIST = [
    'user1@example.com', 'user2@example.com', # add all ~500 users
]

# === NLP Analysis === #
sentiment_classifier = pipeline("sentiment-analysis")
urgency_keywords = ["urgent", "immediately", "critical", "asap", "severely"]


def analyze_email(email_body: str):
    sentiment = sentiment_classifier(email_body)[0]
    urgency = any(word in email_body.lower() for word in urgency_keywords)
    escalation_trigger = "yes" if urgency or sentiment['label'] == "NEGATIVE" else "no"
    return {
        "sentiment": sentiment,
        "urgency": urgency,
        "trigger": escalation_trigger
    }

# === Escalation Logging === #
def generate_escalation_id():
    return ESCALATION_ID_PREFIX + str(uuid.uuid4().int)[:5]


def log_escalation(data):
    if not os.path.exists(DATA_FILE):
        db = []
    else:
        with open(DATA_FILE, "r") as f:
            db = json.load(f)
    db.append(data)
    with open(DATA_FILE, "w") as f:
        json.dump(db, f, indent=2)

# === Outlook Integration via Microsoft Graph API === #
def get_access_token():
    app = ConfidentialClientApplication(
        CLIENT_ID,
        authority=AUTHORITY,
        client_credential=CLIENT_SECRET
    )
    result = app.acquire_token_for_client(scopes=SCOPE)
    return result['access_token']


def fetch_emails_for_user(user_email, access_token):
    url = f"https://graph.microsoft.com/v1.0/users/{user_email}/mailFolders/inbox/messages?$top=10"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Accept': 'application/json'
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        emails = response.json().get('value', [])
        for mail in emails:
            body = mail.get('body', {}).get('content', '')
            analysis = analyze_email(body)
            if analysis['trigger'] == 'yes':
                escalation_id = generate_escalation_id()
                record = {
                    "id": escalation_id,
                    "subject": mail.get('subject', 'No Subject'),
                    "body": body,
                    "sender": user_email,
                    "date": mail.get('receivedDateTime', str(datetime.datetime.now())),
                    "analysis": analysis
                }
                log_escalation(record)
    else:
        print(f"Error fetching emails for {user_email}: {response.text}")


def fetch_emails_for_all_users():
    access_token = get_access_token()
    for email in USER_LIST:
        fetch_emails_for_user(email, access_token)

# Schedule email fetch every hour
scheduler = BlockingScheduler()
scheduler.add_job(fetch_emails_for_all_users, 'interval', hours=1)

# === FastAPI App === #
app = FastAPI()


class EmailInput(BaseModel):
    subject: str
    body: str
    sender: str
    date: str


@app.post("/parse_email")
def parse_email(input: EmailInput):
    analysis = analyze_email(input.body)
    if analysis['trigger'] == 'yes':
        escalation_id = generate_escalation_id()
        record = {
            "id": escalation_id,
            "subject": input.subject,
            "body": input.body,
            "sender": input.sender,
            "date": input.date,
            "analysis": analysis
        }
        log_escalation(record)
        return JSONResponse({"message": "Escalation logged", "id": escalation_id})
    else:
        return JSONResponse({"message": "No escalation detected"})

# === Run Server and Scheduler === #
if __name__ == "__main__":
    import threading

    def run_api():
        uvicorn.run("EscalateAI:app", host="0.0.0.0", port=8000, reload=True)

    t = threading.Thread(target=run_api)
    t.start()
    scheduler.start()

# === TODO / Next Features === #
# - Kanban UI with Streamlit or React frontend
# - Real-time alerts using WebSocket / email notifications
# - Predictive models for proactive escalation handling
# - Feedback loop for continuous learning
# - Multi-user access and collaboration interface
# - Integration with internal CRMs / case tracking tools
