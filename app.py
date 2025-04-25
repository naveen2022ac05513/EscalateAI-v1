import uuid
import pandas as pd
import streamlit as st
import msal
import requests
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from datetime import datetime

nltk.download('vader_lexicon', quiet=True)
analyzer = SentimentIntensityAnalyzer()

# Microsoft Graph API Credentials (dummy values – replace)
CLIENT_ID = "YOUR_CLIENT_ID"
CLIENT_SECRET = "YOUR_CLIENT_SECRET"
TENANT_ID = "YOUR_TENANT_ID"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/messages"

st.set_page_config(page_title="EscalateAI", layout="wide")
st.title("📊 EscalateAI - Smart Escalation Management")

# Load & Save Data
def load_data():
    try:
        return pd.read_csv("escalations.csv")
    except:
        return pd.DataFrame()

def save_data(df):
    df.to_csv("escalations.csv", index=False)

if "escalation_data" not in st.session_state:
    st.session_state.escalation_data = load_data()

if "monitored_emails" not in st.session_state:
    st.session_state.monitored_emails = []

# Sidebar: Email ID Management
st.sidebar.header("📧 Monitored Email IDs")
email_input = st.sidebar.text_input("Add Email ID")
if st.sidebar.button("Add"):
    if email_input and email_input not in st.session_state.monitored_emails:
        st.session_state.monitored_emails.append(email_input)
        st.sidebar.success(f"Added {email_input}")

email_file = st.sidebar.file_uploader("📂 Upload Email IDs (CSV with 'Email ID' column)", type=["csv"])
if email_file:
    try:
        df = pd.read_csv(email_file)
        if "Email ID" in df.columns:
            st.session_state.monitored_emails.extend(df["Email ID"].dropna().tolist())
            st.session_state.monitored_emails = list(set(st.session_state.monitored_emails))  # unique
            st.sidebar.success("Emails uploaded successfully.")
        else:
            st.sidebar.error("Missing 'Email ID' column.")
    except Exception as e:
        st.sidebar.error(str(e))

st.sidebar.markdown("**Monitored Emails:**")
for e in st.session_state.monitored_emails:
    st.sidebar.write("-", e)

# Generate Escalation ID
def generate_escalation_id():
    return f"ESC-{str(uuid.uuid4())[:8].upper()}"

# NLP Analysis
def analyze_issue(issue_text):
    score = analyzer.polarity_scores(str(issue_text))
    sentiment = "Negative" if score['compound'] < -0.2 else "Neutral/Positive"

    urgency_keywords = ['urgent', 'immediately', 'asap', 'critical', 'now']
    critical_keywords = ['failure', 'down', 'not working', 'crash', 'error', 'issue', 'blocker']

    urgency = "High" if any(word in str(issue_text).lower() for word in urgency_keywords) or sentiment == "Negative" else "Low"
    criticality = "High" if any(word in str(issue_text).lower() for word in critical_keywords) else "Low"

    return urgency, criticality, sentiment

# Microsoft Graph API Auth
def get_access_token():
    try:
        app = msal.ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
        token_response = app.acquire_token_for_client(["https://graph.microsoft.com/.default"])
        return token_response.get("access_token", None)
    except Exception as e:
        st.error(f"Token error: {e}")
        return None

# Fetch Emails
def fetch_emails():
    token = get_access_token()
    if not token:
        st.error("Token retrieval failed.")
        return []

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(GRAPH_API_URL, headers=headers)

    if response.status_code != 200:
        st.error(f"Graph API error {response.status_code}")
        return []

    fetched = []
    for email in response.json().get("value", []):
        sender = email.get("sender", {}).get("emailAddress", {}).get("address", "")
        subject = email.get("subject", "")
        date = email.get("receivedDateTime", "")

        if sender in st.session_state.monitored_emails:
            urgency, criticality, sentiment = analyze_issue(subject)
            if sentiment == "Negative" or urgency == "High" or criticality == "High":
                fetched.append({
                    "Escalation ID": generate_escalation_id(),
                    "Customer Name": sender.split("@")[0],
                    "Issue": subject,
                    "Urgency": urgency,
                    "Criticality": criticality,
                    "Status": "New",
                    "Date": date,
                    "Owner": "Admin",
                    "Sentiment": sentiment
                })
    return fetched

if st.sidebar.button("📥 Fetch Escalations"):
    new_escalations = fetch_emails()
    if new_escalations:
        new_df = pd.DataFrame(new_escalations)
        st.session_state.escalation_data = pd.concat([st.session_state.escalation_data, new_df], ignore_index=True)
        save_data(st.session_state.escalation_data)
        st.sidebar.success("Fetched and analyzed emails.")

# Sidebar: Manual Entry
st.sidebar.header("📝 Manual Escalation Entry")
with st.sidebar.form("manual_entry"):
    customer = st.text_input("Customer Name")
    issue = st.text_area("Issue Description")
    owner = st.text_input("Owner", value="Admin")
    submit = st.form_submit_button("Add Escalation")

    if submit:
        urgency, criticality, sentiment = analyze_issue(issue)
        new_row = {
            "Escalation ID": generate_escalation_id(),
            "Customer Name": customer,
            "Issue": issue,
            "Urgency": urgency,
            "Criticality": criticality,
            "Status": "New",
            "Date": datetime.now(),
            "Owner": owner,
            "Sentiment": sentiment
        }
        st.session_state.escalation_data = pd.concat([st.session_state.escalation_data, pd.DataFrame([new_row])], ignore_index=True)
        save_data(st.session_state.escalation_data)
        st.sidebar.success("Escalation added.")

# Sidebar: Bulk Upload
st.sidebar.header("📥 Bulk Upload Escalations")
bulk_file = st.sidebar.file_uploader("Upload Excel File", type=["xlsx"])
if bulk_file:
    try:
        df_bulk = pd.read_excel(bulk_file, engine="openpyxl")
        if "Issue" in df_bulk.columns:
            for idx, row in df_bulk.iterrows():
                urgency, criticality, sentiment = analyze_issue(row["Issue"])
                row_data = row.to_dict()
                row_data.update({
                    "Escalation ID": generate_escalation_id(),
                    "Urgency": urgency,
                    "Criticality": criticality,
                    "Status": "New",
                    "Date": datetime.now(),
                    "Sentiment": sentiment,
                    "Owner": row_data.get("Owner", "Admin")
                })
                st.session_state.escalation_data = pd.concat([st.session_state.escalation_data, pd.DataFrame([row_data])], ignore_index=True)
            save_data(st.session_state.escalation_data)
            st.sidebar.success("Bulk upload successful.")
        else:
            st.sidebar.warning("Excel file must contain an 'Issue' column.")
    except Exception as e:
        st.sidebar.error(f"Upload error: {e}")

# Dashboard
st.subheader("🗂️ Escalation Dashboard")
if not st.session_state.escalation_data.empty:
    df = st.session_state.escalation_data
    st.dataframe(df, use_container_width=True)
    
    st.download_button("📥 Download Data", data=df.to_csv(index=False), file_name="escalations.csv", mime="text/csv")

    st.metric("Total Escalations", len(df))
    st.metric("High Urgency", len(df[df["Urgency"] == "High"]))
    st.metric("Critical Issues", len(df[df["Criticality"] == "High"]))
else:
    st.info("No escalations available. Use sidebar to fetch or add.")

st.markdown("---")
st.caption("© 2025 EscalateAI – Smart Escalation Management")

