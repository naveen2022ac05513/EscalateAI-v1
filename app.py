import uuid
import pandas as pd
import streamlit as st
import msal
import requests
from datetime import datetime

# Microsoft Graph API Setup
CLIENT_ID = "8df1bf10-bf08-4ce9-8078-c387d17aa785"
CLIENT_SECRET = "169948a0-3581-449d-9d8c-f4f54160465d"
TENANT_ID = "f8cdef31-a31e-4b4a-93e4-5f571e91255a"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/messages"

# Page Config
st.set_page_config(page_title="EscalateAI Dashboard", layout="wide")
st.title("📊 EscalateAI - Enhanced Escalation Management Dashboard")

# Data Loaders
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

# --- Sidebar Layout ---
st.sidebar.header("⚙️ Admin Tools")

# Manual Email Entry
st.sidebar.markdown("#### 📬 Add Monitored Email")
new_email = st.sidebar.text_input("Enter email")
if st.sidebar.button("Add Email"):
    if "@" in new_email:
        st.session_state["monitored_emails"].append(new_email.strip())
        st.sidebar.success(f"Added: {new_email}")
    else:
        st.sidebar.error("Enter a valid email address.")

# Bulk Email Upload
st.sidebar.markdown("#### 📂 Bulk Upload Monitored Emails")
uploaded_email_file = st.sidebar.file_uploader("Upload CSV with 'Email ID' column", type=["csv"])
if uploaded_email_file:
    try:
        df = pd.read_csv(uploaded_email_file)
        if "Email ID" in df.columns:
            st.session_state["monitored_emails"].extend(df["Email ID"].dropna().tolist())
            st.sidebar.success("Emails uploaded.")
        else:
            st.sidebar.error("Missing 'Email ID' column.")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# Display Monitored Emails
if st.session_state["monitored_emails"]:
    st.sidebar.markdown("**📧 Monitored Emails:**")
    for e in st.session_state["monitored_emails"]:
        st.sidebar.markdown(f"- {e}")

# Manual Escalation Entry
st.sidebar.markdown("#### ✍️ Manual Escalation Entry")
with st.sidebar.form("manual_escalation_form"):
    customer_name = st.text_input("Customer Name")
    issue = st.text_area("Issue")
    urgency = st.selectbox("Urgency", ["Low", "Medium", "High"])
    owner = st.text_input("Owner", value="Admin")
    submitted = st.form_submit_button("Add Escalation")
    if submitted:
        if customer_name and issue:
            new_entry = {
                "Escalation ID": f"ESC-{str(uuid.uuid4())[:8].upper()}",
                "Customer Name": customer_name,
                "Issue": issue,
                "Urgency": urgency,
                "Status": "New",
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Owner": owner
            }
            st.session_state["escalation_data"] = pd.concat(
                [st.session_state["escalation_data"], pd.DataFrame([new_entry])],
                ignore_index=True
            )
            save_escalation_data(st.session_state["escalation_data"])
            st.sidebar.success("Escalation logged.")
        else:
            st.sidebar.warning("Please complete all fields.")

# Bulk Escalation Upload
st.sidebar.markdown("#### ⬆️ Upload Escalations via Excel/CSV")
upload_escalations = st.sidebar.file_uploader("CSV with: Customer Name, Issue, Urgency, Status, Owner", type=["csv"])
if upload_escalations:
    try:
        df_upload = pd.read_csv(upload_escalations)
        required = {"Customer Name", "Issue", "Urgency", "Status", "Owner"}
        if required.issubset(set(df_upload.columns)):
            df_upload["Escalation ID"] = [f"ESC-{str(uuid.uuid4())[:8].upper()}" for _ in range(len(df_upload))]
            df_upload["Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state["escalation_data"] = pd.concat(
                [st.session_state["escalation_data"], df_upload],
                ignore_index=True
            )
            save_escalation_data(st.session_state["escalation_data"])
            st.sidebar.success(f"{len(df_upload)} entries added.")
        else:
            st.sidebar.error("Missing required columns.")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

# Email Fetch
def get_access_token():
    app = msal.ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
    token_response = app.acquire_token_for_client(["https://graph.microsoft.com/.default"])
    return token_response.get("access_token", None)

def fetch_emails():
    access_token = get_access_token()
    if not access_token:
        st.error("Token failed.")
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
                    "Escalation ID": f"ESC-{str(uuid.uuid4())[:8].upper()}",
                    "Customer Name": sender.split("@")[0],
                    "Issue": subject,
                    "Urgency": "High",
                    "Status": "New",
                    "Date": received_date,
                    "Owner": "Admin"
                })
        return escalation_data
    else:
        st.error(f"Error: {response.status_code}")
        return []

if st.sidebar.button("📩 Fetch Escalations from Email"):
    new_data = fetch_emails()
    if new_data:
        st.session_state["escalation_data"] = pd.concat(
            [st.session_state["escalation_data"], pd.DataFrame(new_data)],
            ignore_index=True
        )
        save_escalation_data(st.session_state["escalation_data"])
        st.sidebar.success(f"{len(new_data)} new escalations fetched.")

# --- Main Area: Dashboard ---
st.subheader("📋 Escalation Dashboard")

if not st.session_state["escalation_data"].empty:
    df = st.session_state["escalation_data"]

    @st.cache_data
    def convert_to_csv(dataframe):
        return dataframe.to_csv(index=False).encode("utf-8")

    st.download_button("⬇️ Download Escalations", convert_to_csv(df), "escalations.csv", "text/csv")

    st.dataframe(df, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Escalations", len(df))
    col2.metric("High Urgency", len(df[df["Urgency"] == "High"]))
    col3.metric("Open Status", len(df[df["Status"].str.lower() == "new"]))
else:
    st.info("No escalations yet. Use sidebar to add manually, upload, or fetch.")

st.markdown("---")
st.caption("© 2025 EscalateAI")
