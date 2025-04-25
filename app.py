import uuid
import pandas as pd
import streamlit as st
import msal
import requests
from datetime import datetime
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import sqlite3

# Microsoft Graph API Credentials (Replace with actual credentials)
CLIENT_ID = "8df1bf10-bf08-4ce9-8078-c387d17aa785"
CLIENT_SECRET = "169948a0-3581-449d-9d8c-f4f54160465d"
TENANT_ID = "f8cdef31-a31e-4b4a-93e4-5f571e91255a"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/messages"

# Admin Dashboard Setup
st.set_page_config(page_title="EscalateAI Dashboard", layout="wide")
st.title("📊 EscalateAI - Enhanced Escalation Management Dashboard")

# Initialize SQLite Database for Escalations
conn = sqlite3.connect('escalations.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS escalations (
        escalation_id TEXT PRIMARY KEY,
        customer_name TEXT,
        issue TEXT,
        urgency TEXT,
        status TEXT,
        date TEXT,
        owner TEXT,
        criticality TEXT
    )
''')
conn.commit()

# Function to Save Escalation Data to DB
def save_to_db(escalation_data):
    cursor.executemany('''
        INSERT OR REPLACE INTO escalations (escalation_id, customer_name, issue, urgency, status, date, owner, criticality)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', escalation_data)
    conn.commit()

# Function to Load Escalation Data from DB
def load_from_db():
    cursor.execute('SELECT * FROM escalations WHERE status="Escalated"')
    return cursor.fetchall()

# Sentiment Analysis for Negative Sentiment
def analyze_sentiment(issue):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_score = analyzer.polarity_scores(issue)
    return sentiment_score['compound']

# Generate Unique Escalation ID
def generate_escalation_id():
    return f"ESC-{str(uuid.uuid4())[:8].upper()}"

# Authenticate with Microsoft Graph API
def get_access_token():
    try:
        app = msal.ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
        token_response = app.acquire_token_for_client(["https://graph.microsoft.com/.default"])
        return token_response.get("access_token", None)
    except Exception as e:
        st.error(f"Error acquiring token: {e}")
        return None

# Fetch Emails from Employee Inboxes
def fetch_emails():
    access_token = get_access_token()
    if not access_token:
        st.error("Failed to retrieve authentication token.")
        return []

    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(GRAPH_API_URL, headers=headers)

    if response.status_code == 200:
        emails = response.json()["value"]
        escalation_data = []

        for email in emails:
            sender = email["sender"]["emailAddress"]["address"]
            subject = email["subject"]
            received_date = email["receivedDateTime"]

            # Analyzing sentiment of the email subject (assuming this contains the issue)
            sentiment_score = analyze_sentiment(subject)

            # If negative sentiment detected, classify as Escalated
            if sentiment_score < -0.5:
                escalation_data.append((
                    generate_escalation_id(),
                    sender.split("@")[0],  # Customer name (extracted from email)
                    subject,
                    "High",
                    "Escalated",
                    received_date,
                    "Admin",
                    "Critical"
                ))

        return escalation_data
    else:
        st.error(f"Error fetching emails: {response.status_code}")
        return []

# Sidebar Inputs for Admin: Manual Entry, Bulk Upload, and Email Parsing
with st.sidebar:
    st.header("📂 Escalation Entries")
    
    # Manual Escalation Entry
    st.subheader("Manual Escalation Entry")
    customer_name = st.text_input("Customer Name")
    issue = st.text_area("Issue")
    urgency = st.selectbox("Urgency", ["Low", "Medium", "High"])
    criticality = st.selectbox("Criticality", ["Low", "Medium", "High"])
    if st.button("Add Escalation"):
        if customer_name and issue:
            escalation_id = generate_escalation_id()
            date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            save_to_db([(escalation_id, customer_name, issue, urgency, "New", date, "Admin", criticality)])
            st.success(f"Escalation {escalation_id} added.")

    # Bulk Upload for Escalations via Excel
    st.subheader("Bulk Upload Escalations (Excel)")
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            for _, row in df.iterrows():
                escalation_id = generate_escalation_id()
                customer_name = row.get("Customer", "Unknown")
                issue = row.get("Brief Issue", "No issue description")
                urgency = row.get("Urgency", "Low")
                criticality = row.get("Criticality", "Low")
                date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_to_db([(escalation_id, customer_name, issue, urgency, "New", date, "Admin", criticality)])
            st.success("Escalations successfully uploaded.")
        except Exception as e:
            st.error(f"Error processing file: {e}")
    
    # Fetch Escalations from Emails
    if st.button("Fetch Escalations from Emails"):
        escalations = fetch_emails()
        if escalations:
            save_to_db(escalations)
            st.sidebar.success("Escalations fetched and saved!")

# Main Dashboard for Escalated Cases
st.subheader("🗂️ Escalation Dashboard")

# Load and display only Escalated cases
escalated_cases = load_from_db()
if escalated_cases:
    df = pd.DataFrame(escalated_cases, columns=["Escalation ID", "Customer Name", "Issue", "Urgency", "Status", "Date", "Owner", "Criticality"])
    st.dataframe(df)
else:
    st.info("No escalated cases available.")
