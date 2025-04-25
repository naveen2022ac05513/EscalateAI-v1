import uuid
import pandas as pd
import streamlit as st
import msal
import requests
from datetime import datetime

# Microsoft Graph API Credentials (Replace with actual credentials)
CLIENT_ID = "8df1bf10-bf08-4ce9-8078-c387d17aa785"
CLIENT_SECRET = "169948a0-3581-449d-9d8c-f4f54160465d"
TENANT_ID = "f8cdef31-a31e-4b4a-93e4-5f571e91255a"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/messages"

# Admin Dashboard Setup
st.set_page_config(page_title="EscalateAI Dashboard", layout="wide")
st.title("📊 EscalateAI - Enhanced Escalation Management Dashboard")

# Load and Save Escalation Data
def load_escalation_data():
    try:
        return pd.read_csv("escalations.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Escalation ID", "Customer Name", "Issue", "Urgency", "Status", "Date", "Owner"])

def save_escalation_data(df):
    df.to_csv("escalations.csv", index=False)

if "escalation_data" not in st.session_state:
    st.session_state["escalation_data"] = load_escalation_data()

if "monitored_emails" not in st.session_state:
    st.session_state["monitored_emails"] = []

# Sidebar - Email Monitoring Management
st.sidebar.header("📥 Email Monitoring Setup")

# Manual entry
with st.sidebar.form("manual_email_add"):
    new_email = st.text_input("Add Monitored Email ID")
    if st.form_submit_button("Add Email"):
        if new_email and "@" in new_email:
            if new_email not in st.session_state["monitored_emails"]:
                st.session_state["monitored_emails"].append(new_email)
                st.sidebar.success(f"{new_email} added.")
            else:
                st.sidebar.warning("Email already exists.")
        else:
            st.sidebar.error("Please enter a valid email.")

# Bulk upload
email_file = st.sidebar.file_uploader("📁 Upload CSV with 'Email ID'", type=["csv"])
if email_file:
    try:
        email_df = pd.read_csv(email_file)
        if "Email ID" in email_df.columns:
            uploaded_emails = email_df["Email ID"].dropna().tolist()
            added_count = 0
            for email in uploaded_emails:
                if email not in st.session_state["monitored_emails"]:
                    st.session_state["monitored_emails"].append(email)
                    added_count += 1
            st.sidebar.success(f"{added_count} new emails added.")
        else:
            st.sidebar.error("CSV must include 'Email ID' column.")
    except Exception as e:
        st.sidebar.error(f"Error reading file: {e}")

# Show current list
if st.session_state["monitored_emails"]:
    st.sidebar.markdown("### 👁️‍🗨️ Currently Monitored Emails")
    st.sidebar.write(pd.DataFrame(st.session_state["monitored_emails"], columns=["Email ID"]))

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

            if sender in st.session_state["monitored_emails"]:
                escalation_data.append({
                    "Escalation ID": generate_escalation_id(),
                    "Customer Name": sender.split("@")[0],
                    "Issue": subject,
                    "Urgency": "High",
                    "Status": "New",
                    "Date": received_date,
                    "Owner": "Admin"
                })
        return escalation_data
    else:
        st.error(f"Error fetching emails: {response.status_code}")
        return []

# Button to fetch and store escalations
if st.sidebar.button("📩 Fetch Escalations from Email"):
    escalations = fetch_emails()
    if escalations:
        updated_df = pd.concat([pd.DataFrame(escalations), st.session_state["escalation_data"]], ignore_index=True)
        st.session_state["escalation_data"] = updated_df
        save_escalation_data(updated_df)
        st.sidebar.success("Escalations updated successfully!")

# Escalation Dashboard
st.subheader("🗂️ Escalation Dashboard")
if not st.session_state["escalation_data"].empty:
    df = st.session_state["escalation_data"]

    @st.cache_data
    def convert_to_csv(dataframe):
        return dataframe.to_csv(index=False).encode('utf-8')

    csv = convert_to_csv(df)
    st.download_button(
        label="📤 Download Escalation Data",
        data=csv,
        file_name="escalations.csv",
        mime="text/csv"
    )

    st.dataframe(df, use_container_width=True)

    st.metric(label="Total Escalations", value=len(df))
    st.metric(label="High Urgency", value=len(df[df["Urgency"] == "High"]))
else:
    st.info("No escalations found yet. Click 'Fetch Escalations from Email' to begin.")

st.markdown("---")
st.caption("© 2025 EscalateAI - Enhanced Escalation Management Dashboard")
