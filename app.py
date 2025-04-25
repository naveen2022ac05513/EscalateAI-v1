import uuid
import pandas as pd
import streamlit as st
import msal
import requests
from datetime import datetime
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Microsoft Graph API Credentials (Replace with actual credentials)
CLIENT_ID = "8df1bf10-bf08-4ce9-8078-c387d17aa785"
CLIENT_SECRET = "169948a0-3581-449d-9d8c-f4f54160465d"
TENANT_ID = "f8cdef31-a31e-4b4a-93e4-5f571e91255a"
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}"
GRAPH_API_URL = "https://graph.microsoft.com/v1.0/me/messages"

# Sentiment Analysis Setup (using VADER)
analyzer = SentimentIntensityAnalyzer()

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

# Sidebar for Email ID Management (Manual Entry & Bulk Upload)
st.sidebar.header("📧 Manage Monitored Email IDs")

# Manual Entry of Email ID
new_email_id = st.sidebar.text_input("Enter Email ID to Monitor")
if st.sidebar.button("Add Email ID"):
    if new_email_id:
        st.session_state["monitored_emails"].append(new_email_id)
        st.sidebar.success(f"Email ID '{new_email_id}' added to monitored list.")
        save_monitored_emails()
    else:
        st.sidebar.error("Please enter a valid email ID.")

# Bulk Upload of Email IDs (via Excel)
st.sidebar.header("📂 Upload Email IDs (Excel)")
uploaded_email_file = st.sidebar.file_uploader("Upload Excel file with Email IDs", type=["xlsx"])
if uploaded_email_file:
    try:
        email_df = pd.read_excel(uploaded_email_file)
        if "Email ID" in email_df.columns:
            email_list = email_df["Email ID"].tolist()
            st.session_state["monitored_emails"].extend(email_list)
            st.sidebar.success(f"{len(email_list)} email IDs uploaded successfully!")
            save_monitored_emails()
        else:
            st.sidebar.error("Excel file must contain 'Email ID' column.")
    except Exception as e:
        st.sidebar.error(f"Error processing file: {e}")

# Save monitored emails to a file for persistence
def save_monitored_emails():
    try:
        with open("monitored_emails.txt", "w") as f:
            for email in st.session_state["monitored_emails"]:
                f.write(f"{email}\n")
    except Exception as e:
        st.error(f"Error saving email IDs: {e}")

# Function to load monitored emails
def load_monitored_emails():
    try:
        with open("monitored_emails.txt", "r") as f:
            return [line.strip() for line in f.readlines()]
    except Exception as e:
        return []

# Load monitored emails at the start
if "monitored_emails" not in st.session_state:
    st.session_state["monitored_emails"] = load_monitored_emails()

# Sidebar for Escalation Entry
st.sidebar.header("📂 Manual Escalation Entry")
customer_name = st.sidebar.text_input("Customer Name")
issue = st.sidebar.text_area("Issue Description")
urgency = st.sidebar.selectbox("Urgency", ["Low", "Medium", "High"])
status = st.sidebar.selectbox("Status", ["New", "In Progress", "Resolved", "Closed"])
owner = st.sidebar.text_input("Owner")

if st.sidebar.button("Add Manual Escalation"):
    if customer_name and issue and owner:
        new_escalation = {
            "Escalation ID": generate_escalation_id(),
            "Customer Name": customer_name,
            "Issue": issue,
            "Urgency": urgency,
            "Status": status,
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Owner": owner,
            "Sentiment": analyze_sentiment(issue)
        }
        st.session_state["escalation_data"].append(new_escalation)
        save_escalation_data(pd.DataFrame(st.session_state["escalation_data"]))
        st.sidebar.success("Escalation added successfully!")
    else:
        st.sidebar.error("Please fill in all fields!")

# Sidebar for Bulk Upload of Escalations (via Excel)
st.sidebar.header("📂 Upload Escalations (Excel)")
uploaded_excel = st.sidebar.file_uploader("Upload Excel file", type=["xlsx"])
if uploaded_excel:
    try:
        excel_df = pd.read_excel(uploaded_excel)

        # Dynamically Detect Columns (using substring matching)
        columns_map = {
            "Customer": None,
            "Issue": None,
            "Criticalness": None,
            "Status": None,
            "Owner": None,
            "Date of Closure": None
        }

        # Detect and map columns dynamically based on keywords
        for col in excel_df.columns:
            for key in columns_map:
                if key.lower() in col.lower():
                    columns_map[key] = col
                    break

        # Check if necessary columns exist
        if None in columns_map.values():
            st.sidebar.error(f"Missing necessary columns in Excel. Ensure the following are present: {', '.join(columns_map.keys())}")
        else:
            # Process Excel data
            excel_df["Escalation ID"] = [generate_escalation_id() for _ in range(len(excel_df))]
            excel_df["Date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Map detected columns
            excel_df["Customer Name"] = excel_df[columns_map["Customer"]]
            excel_df["Issue"] = excel_df[columns_map["Issue"]]
            excel_df["Urgency"] = excel_df[columns_map["Criticalness"]]
            excel_df["Owner"] = excel_df[columns_map["Owner"]]
            excel_df["Status"] = excel_df[columns_map["Status"]]
            excel_df["Sentiment"] = excel_df[columns_map["Issue"]].apply(analyze_sentiment)

            # Add escalations to session state
            st.session_state["escalation_data"].extend(excel_df.to_dict(orient="records"))
            save_escalation_data(pd.DataFrame(st.session_state["escalation_data"]))
            st.sidebar.success(f"{len(excel_df)} escalations uploaded successfully!")
    except Exception as e:
        st.sidebar.error(f"Error processing file: {e}")

# Sentiment Analysis Function
def analyze_sentiment(text):
    sentiment_score = analyzer.polarity_scores(text)
    # If the sentiment score is negative, return negative sentiment
    if sentiment_score["compound"] <= -0.05:
        return "Negative"
    else:
        return "Neutral/Positive"

# Generate Unique Escalation ID
def generate_escalation_id():
    return f"ESC-{str(uuid.uuid4())[:8].upper()}"

# Authenticate with Microsoft Graph API
def get_access_token():
    try:
        app = msal.ConfidentialClientApplication(CLIENT_ID, authority=AUTHORITY, client_credential=CLIENT_SECRET)
        token_response = app.acquire_token_for_client(["https://graph.microsoft.com/.default"])
        
        if "access_token" in token_response:
            return token_response["access_token"]
        else:
            st.error(f"Token acquisition failed. Response: {token_response}")
            return None
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
                    "Owner": "Admin",
                    "Sentiment": analyze_sentiment(subject)
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
       
