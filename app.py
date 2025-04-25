import uuid
import pandas as pd
import streamlit as st
import msal
import requests
from datetime import datetime
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Download VADER lexicon
nltk.download('vader_lexicon')
analyzer = SentimentIntensityAnalyzer()

# Microsoft Graph API Setup
	CLIENT_ID = "8df1bf10-bf08-4ce9-8078-c387d17aa785"
	CLIENT_SECRET = "169948a0-3581-449d-9d8c-f4f54160465d"
	TENANT_ID = "f8cdef31-a31e-4b4a-93e4-5f571e91255a"

AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/messages"

st.set_page_config(page_title="EscalateAI Dashboard", layout="wide")
st.title("📊 EscalateAI - Enhanced Escalation Management Dashboard")

# Utilities
def generate_escalation_id():
    return f"ESC-{str(uuid.uuid4())[:8].upper()}"

def save_escalation_data(df):
    df.to_csv("escalations.csv", index=False)

def load_escalation_data():
    try:
        return pd.read_csv("escalations.csv")
    except FileNotFoundError:
        return pd.DataFrame()

# Load session state
if "escalation_data" not in st.session_state:
    st.session_state["escalation_data"] = load_escalation_data()

if "monitored_emails" not in st.session_state:
    st.session_state["monitored_emails"] = []

# ---------------- Sidebar Section ----------------

st.sidebar.header("📥 Admin Panel")

# Email ID entry (manual)
st.sidebar.subheader("➕ Add Email ID to Monitor")
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

# ---------------- Dashboard Section ----------------

st.subheader("🗂️ Escalation Dashboard")
df = st.session_state["escalation_data"]
if not df.empty:
    st.metric("Total Escalations", len(df))
    st.metric("Negative Sentiments", len(df[df['Status'] == "Negative"]))
    st.download_button("Download Data", df.to_csv(index=False), "escalations.csv", "text/csv")
    st.dataframe(df, use_container_width=True)
else:
    st.info("No escalations found. Add manually or upload via sidebar.")

st.markdown("---")
st.caption("© 2025 EscalateAI")
