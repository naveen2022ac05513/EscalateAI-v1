import uuid
import pandas as pd
import streamlit as st
import msal
import requests
from datetime import datetime
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Initialize VADER for sentiment analysis
nltk.download('vader_lexicon', quiet=True)
analyzer = SentimentIntensityAnalyzer()

# Microsoft Graph API Setup (replace with your credentials)
CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
TENANT_ID = "your-tenant-id"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/messages"

st.set_page_config(page_title="EscalateAI Dashboard", layout="wide")
st.title("📊 EscalateAI - Enhanced Escalation Management Dashboard")

# Load session state
def generate_escalation_id():
    return f"ESC-{str(uuid.uuid4())[:8].upper()}"

def save_escalation_data(df):
    df.to_csv("escalations.csv", index=False)

def load_escalation_data():
    try:
        return pd.read_csv("escalations.csv")
    except FileNotFoundError:
        return pd.DataFrame()

if "escalation_data" not in st.session_state:
    st.session_state["escalation_data"] = load_escalation_data()

if "monitored_emails" not in st.session_state:
    st.session_state["monitored_emails"] = []

# ---------------- Sidebar: Admin Management ----------------

st.sidebar.header("📥 Admin Panel")

# Manual entry of monitored email ID
st.sidebar.subheader("➕ Add Monitored Email ID")
new_email = st.sidebar.text_input("Enter Email ID")
if st.sidebar.button("Add Email"):
    if new_email and new_email not in st.session_state["monitored_emails"]:
        st.session_state["monitored_emails"].append(new_email)
        st.sidebar.success(f"Added: {new_email}")

# Bulk upload of email IDs
email_file = st.sidebar.file_uploader("📄 Upload Email IDs (CSV)", type=["csv"])
if email_file:
    df_emails = pd.read_csv(email_file)
    if "Email ID" in df_emails.columns:
        new_emails = df_emails["Email ID"].dropna().tolist()
        st.session_state["monitored_emails"].extend(new_emails)
        st.session_state["monitored_emails"] = list(set(st.session_state["monitored_emails"]))  # Remove duplicates
        st.sidebar.success(f"{len(new_emails)} email IDs added")
    else:
        st.sidebar.error("CSV must contain a column named 'Email ID'")

# Manual escalation entry
st.sidebar.subheader("✍️ Manual Escalation Entry")
with st.sidebar.form("manual_entry_form"):
    customer = st.text_input("Customer")
    issue = st.text_area("Brief Issue")
    owner = st.text_input("Owner")
    urgency = st.selectbox("Urgency", ["High", "Medium", "Low"])
    submitted = st.form_submit_button("Submit Escalation")
    if submitted:
        sentiment = analyzer.polarity_scores(issue)["compound"]
        status = "Negative" if sentiment < -0.05 else "Neutral/Positive"
        new_entry = {
            "Escalation ID": generate_escalation_id(),
            "Customer": customer,
            "Issue": issue,
            "Urgency": urgency,
            "Status": status,
            "Owner": owner,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        st.session_state["escalation_data"] = pd.concat([
            st.session_state["escalation_data"],
            pd.DataFrame([new_entry])
        ], ignore_index=True)
        save_escalation_data(st.session_state["escalation_data"])
        st.sidebar.success("Escalation added!")

# Bulk upload escalations
st.sidebar.subheader("📤 Bulk Upload Escalations")
uploaded_escalations = st.sidebar.file_uploader("Upload Escalation Excel", type=["xlsx", "xls"])
if uploaded_escalations:
    try:
        df_bulk = pd.read_excel(uploaded_escalations)
        issue_col = next((col for col in df_bulk.columns if "issue" in col.lower()), None)
        if not issue_col:
            st.sidebar.warning("Couldn't find an issue column for sentiment analysis.")
        else:
            df_bulk["Sentiment Score"] = df_bulk[issue_col].astype(str).apply(lambda x: analyzer.polarity_scores(x)["compound"])
            df_bulk["Status"] = df_bulk["Sentiment Score"].apply(lambda x: "Negative" if x < -0.05 else "Neutral/Positive")
        df_bulk["Escalation ID"] = [generate_escalation_id() for _ in range(len(df_bulk))]
        df_bulk["Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        st.session_state["escalation_data"] = pd.concat([st.session_state["escalation_data"], df_bulk], ignore_index=True)
        save_escalation_data(st.session_state["escalation_data"])
        st.sidebar.success("Bulk escalations added!")
    except Exception as e:
        st.sidebar.error(f"Failed to process file: {e}")

# ---------------- Dashboard ----------------

st.subheader("🗂️ Escalation Dashboard")
df = st.session_state["escalation_data"]
if not df.empty:
    st.metric("Total Escalations", len(df))
    st.metric("Negative Sentiments", len(df[df['Status'] == "Negative"]))
    st.download_button("Download Escalation Data", df.to_csv(index=False), "escalations.csv", "text/csv")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No escalations found. Add manually or upload via sidebar.")

st.markdown("---")
st.caption("© 2025 EscalateAI - Enhanced Escalation Management")
