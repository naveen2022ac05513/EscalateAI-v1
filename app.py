import uuid
import pandas as pd
import streamlit as st
import msal
import requests
from datetime import datetime

# --- Microsoft Graph API Credentials ---
CLIENT_ID = "8df1bf10-bf08-4ce9-8078-c387d17aa785"
CLIENT_SECRET = "169948a0-3581-449d-9d8c-f4f54160465d"
TENANT_ID = "f8cdef31-a31e-4b4a-93e4-5f571e91255a"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/messages"

# --- Streamlit Page Setup ---
st.set_page_config(page_title="EscalateAI Dashboard", layout="wide")
st.title("📊 EscalateAI - Enhanced Escalation Management Dashboard")

# --- Load & Save Escalation Data ---
def load_escalation_data():
    try:
        return pd.read_csv("escalations.csv")
    except FileNotFoundError:
        return pd.DataFrame(columns=["Escalation ID", "Customer Name", "Issue", "Urgency", "Status", "Date", "Owner"])

def save_escalation_data(df):
    df.to_csv("escalations.csv", index=False)

if "escalation_data" not in st.session_state:
    st.session_state["escalation_data"] = load_escalation_data()

# --- Email IDs to Monitor ---
if "monitored_emails" not in st.session_state:
    st.session_state["monitored_emails"] = []

st.sidebar.header("📬 Monitored Emails")
new_email = st.sidebar.text_input("Add Email ID Manually")
if st.sidebar.button("Add Email"):
    if new_email and "@" in new_email:
        st.session_state["monitored_emails"].append(new_email.strip())
        st.sidebar.success(f"Added: {new_email}")
    else:
        st.sidebar.warning("Enter a valid email address.")

uploaded_email_file = st.sidebar.file_uploader("📂 Upload Email IDs (CSV)", type=["csv"])
if uploaded_email_file:
    try:
        email_df = pd.read_csv(uploaded_email_file)
        if "Email ID" in email_df.columns:
            st.session_state["monitored_emails"].extend(email_df["Email ID"].dropna().tolist())
            st.sidebar.success(f"Updated monitored emails ({len(st.session_state['monitored_emails'])})")
        else:
            st.sidebar.error("CSV must contain 'Email ID' column.")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

if st.session_state["monitored_emails"]:
    st.sidebar.markdown("### ✅ Currently Monitored Emails:")
    st.sidebar.write(st.session_state["monitored_emails"])

# --- Generate Unique ID ---
def generate_escalation_id():
    return f"ESC-{str(uuid.uuid4())[:8].upper()}"

# --- Microsoft Graph Auth ---
def get_access_token():
    try:
        app = msal.ConfidentialClientApplication(
            CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET
        )
        token_response = app.acquire_token_for_client(["https://graph.microsoft.com/.default"])
        return token_response.get("access_token", None)
    except Exception as e:
        st.error(f"Token Error: {e}")
        return None

# --- Fetch Emails ---
def fetch_emails():
    access_token = get_access_token()
    if not access_token:
        st.error("Authentication token not retrieved.")
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
        st.error(f"Email fetch failed: {response.status_code}")
        return []

# --- Fetch Escalations Button ---
if st.sidebar.button("📩 Fetch Escalations from Email"):
    escalations = fetch_emails()
    if escalations:
        st.session_state["escalation_data"] = pd.concat(
            [st.session_state["escalation_data"], pd.DataFrame(escalations)],
            ignore_index=True
        )
        save_escalation_data(st.session_state["escalation_data"])
        st.sidebar.success("Fetched and saved new escalations.")

# --- Escalation Dashboard ---
st.subheader("🗂️ Escalation Dashboard")

# --- Manual Entry Form ---
st.markdown("### ✍️ Manually Log New Escalation")
with st.form("manual_escalation_form"):
    customer_name = st.text_input("Customer Name")
    issue = st.text_area("Issue Summary")
    urgency = st.selectbox("Urgency Level", ["Low", "Medium", "High"])
    owner = st.text_input("Owner", value="Admin")
    submitted = st.form_submit_button("Add Escalation")

    if submitted:
        if customer_name and issue:
            new_row = {
                "Escalation ID": generate_escalation_id(),
                "Customer Name": customer_name,
                "Issue": issue,
                "Urgency": urgency,
                "Status": "New",
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Owner": owner
            }
            st.session_state["escalation_data"] = pd.concat(
                [st.session_state["escalation_data"], pd.DataFrame([new_row])],
                ignore_index=True
            )
            save_escalation_data(st.session_state["escalation_data"])
            st.success("Escalation added successfully.")
        else:
            st.warning("Please complete all required fields.")

# --- Bulk Upload Escalations ---
st.markdown("### 📂 Bulk Upload Escalations via CSV")
upload_bulk = st.file_uploader("Upload CSV with columns: Customer Name, Issue, Urgency, Status, Owner", type=["csv"])
if upload_bulk:
    try:
        upload_df = pd.read_csv(upload_bulk)
        required_cols = {"Customer Name", "Issue", "Urgency", "Status", "Owner"}
        if not required_cols.issubset(set(upload_df.columns)):
            st.error(f"CSV must contain columns: {', '.join(required_cols)}")
        else:
            upload_df["Escalation ID"] = [generate_escalation_id() for _ in range(len(upload_df))]
            upload_df["Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            st.session_state["escalation_data"] = pd.concat(
                [st.session_state["escalation_data"], upload_df],
                ignore_index=True
            )
            save_escalation_data(st.session_state["escalation_data"])
            st.success(f"{len(upload_df)} escalations uploaded successfully.")
    except Exception as e:
        st.error(f"Upload error: {e}")

# --- Escalation Table and Metrics ---
if not st.session_state["escalation_data"].empty:
    df = st.session_state["escalation_data"]

    @st.cache_data
    def convert_to_csv(dataframe):
        return dataframe.to_csv(index=False).encode("utf-8")

    csv = convert_to_csv(df)
    st.download_button("📥 Download Escalation Data", data=csv, file_name="escalations.csv", mime="text/csv")

    st.dataframe(df, use_container_width=True)

    st.metric("Total Escalations", len(df))
    st.metric("High Urgency", len(df[df["Urgency"] == "High"]))
else:
    st.info("No escalations found. Add one manually or fetch from email.")

st.markdown("---")
st.caption("© 2025 EscalateAI - Enhanced Escalation Management Dashboard")
