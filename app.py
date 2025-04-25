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

# Load Escalations from CSV
def load_escalation_data():
    try:
        return pd.read_csv("escalations.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Escalation ID", "Customer Name", "Issue", "Urgency", "Status", "Date", "Owner"])

def save_escalation_data(df):
    df.to_csv("escalations.csv", index=False)

if "escalation_data" not in st.session_state:
    st.session_state["escalation_data"] = load_escalation_data()

# Monitored Email List
if "monitored_emails" not in st.session_state:
    st.session_state["monitored_emails"] = []

# Bulk Upload Email IDs
st.sidebar.header("📂 Upload Email IDs")
uploaded_file = st.sidebar.file_uploader("Upload CSV file", type=["csv"])
if uploaded_file:
    try:
        email_df = pd.read_csv(uploaded_file)
        if "Email ID" in email_df.columns:
            st.session_state["monitored_emails"] = email_df["Email ID"].tolist()
            st.sidebar.success(f"Updated monitored emails ({len(st.session_state['monitored_emails'])})")
        else:
            st.sidebar.error("CSV file must contain 'Email ID' column.")
    except Exception as e:
        st.sidebar.error(f"Error processing file: {e}")

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

            if sender in st.session_state["monitored_emails"]:  # Filter monitored users
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

# Fetch Escalations Button
if st.sidebar.button("Fetch Escalations"):
    escalations = fetch_emails()
    if escalations:
        st.session_state["escalation_data"] = escalations
        save_escalation_data(pd.DataFrame(escalations))
        st.sidebar.success("Escalations saved & retained!")

# Escalation Dashboard
st.subheader("🗂️ Escalation Dashboard")
if "escalation_data" in st.session_state:
    df = pd.DataFrame(st.session_state["escalation_data"])
    
    # Download Option
    @st.cache_data
    def convert_to_csv(dataframe):
        return dataframe.to_csv(index=False).encode('utf-8')

    csv = convert_to_csv(df)
    st.download_button(
        label="Download Escalation Data",
        data=csv,
        file_name="escalations.csv",
        mime="text/csv"
    )

    # Display Escalation Data Table
    st.dataframe(df, width=1000, height=400)

    # Metrics Insights
    st.metric(label="Total Escalations", value=len(df))
    st.metric(label="High Urgency", value=len(df[df['Urgency'] == "High"]))
else:
    st.info("No escalations added yet. Click 'Fetch Escalations' in sidebar.")

st.markdown("---")
st.caption("© 2025 EscalateAI - Enhanced Escalation Management Dashboard")
st.sidebar.header("📝 Manually Log Escalation")
with st.sidebar.form("manual_escalation_form"):
    customer_name = st.text_input("Customer Name")
    issue = st.text_area("Issue Description")
    urgency = st.selectbox("Urgency", ["High", "Medium", "Low"])
    owner = st.text_input("Owner", value="Admin")
    submitted = st.form_submit_button("Add Escalation")

    if submitted:
        new_entry = {
            "Escalation ID": generate_escalation_id(),
            "Customer Name": customer_name,
            "Issue": issue,
            "Urgency": urgency,
            "Status": "New",
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Owner": owner
        }
        st.session_state["escalation_data"].append(new_entry)
        save_escalation_data(pd.DataFrame(st.session_state["escalation_data"]))
        st.sidebar.success("Escalation added successfully!")
st.sidebar.header("📤 Upload Escalations (Excel)")
excel_file = st.sidebar.file_uploader("Upload .xlsx file", type=["xlsx"])
if excel_file:
    try:
        xls_df = pd.read_excel(excel_file)
        required_cols = {"Customer Name", "Issue", "Urgency", "Owner"}
        if required_cols.issubset(set(xls_df.columns)):
            for _, row in xls_df.iterrows():
                st.session_state["escalation_data"].append({
                    "Escalation ID": generate_escalation_id(),
                    "Customer Name": row["Customer Name"],
                    "Issue": row["Issue"],
                    "Urgency": row["Urgency"],
                    "Status": "New",
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Owner": row["Owner"]
                })
            save_escalation_data(pd.DataFrame(st.session_state["escalation_data"]))
            st.sidebar.success(f"{len(xls_df)} escalations uploaded from Excel.")
        else:
            st.sidebar.error("Excel must contain: Customer Name, Issue, Urgency, Owner")
    except Exception as e:
        st.sidebar.error(f"Error processing Excel file: {e}")
