import uuid
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import threading
import time

# Initialization
st.set_page_config(page_title="EscalateAI Dashboard", layout="wide")
st.title("📊 EscalateAI - Enhanced Escalation Management Dashboard")

# Escalation Data Storage
escalation_data = []

# Generate Unique Escalation ID
def generate_escalation_id():
    return f"ESC-{str(uuid.uuid4())[:8].upper()}"

# Function to Prevent Duplicate Issues
def is_duplicate(issue):
    return any(row["Issue"].lower() == issue.lower() for row in escalation_data)

# Simulated Email Fetching
def fetch_simulated_emails():
    # Example of simulated email fetching
    emails = [
        {"Customer Name": "Reliance Jio", "Issue": "PHE Leakage", "Urgency": "High", "Status": "New", "Owner": "Admin", "Date": datetime.now()},
        {"Customer Name": "CPPIB", "Issue": "Cooling issue - ODU fan replacement", "Urgency": "Critical", "Status": "New", "Owner": "John Doe", "Date": datetime.now()}
    ]
    return emails

# Process Incoming Emails Every 5 Minutes
def process_emails_periodically():
    while True:
        emails = fetch_simulated_emails()
        for email in emails:
            if not is_duplicate(email["Issue"]):
                escalation_id = generate_escalation_id()
                escalation_data.append({
                    "Escalation ID": escalation_id,
                    "Customer Name": email["Customer Name"],
                    "Issue": email["Issue"],
                    "Urgency": email["Urgency"],
                    "Status": email["Status"],
                    "Date": email["Date"],
                    "Owner": email["Owner"]
                })
        time.sleep(300)  # Wait for 5 minutes

# Run Background Thread for Email Fetching
if "email_thread" not in st.session_state:
    st.session_state["email_thread"] = threading.Thread(target=process_emails_periodically, daemon=True)
    st.session_state["email_thread"].start()

# Manual Entry Form
st.sidebar.header("📋 Add Escalation")
customer_name = st.sidebar.text_input("Customer Name")
issue = st.sidebar.text_area("Issue Description")
urgency = st.sidebar.selectbox("Urgency Level", ["Normal", "Urgent", "High", "Critical"])
owner = st.sidebar.text_input("Owner")
status = st.sidebar.selectbox("Status", ["New", "In Progress", "Escalated", "Resolved"])
entry_date = st.sidebar.date_input("Date", datetime.now())

if st.sidebar.button("Add Escalation"):
    if customer_name and issue and owner:
        if not is_duplicate(issue):
            escalation_id = generate_escalation_id()
            escalation_data.append({
                "Escalation ID": escalation_id,
                "Customer Name": customer_name,
                "Issue": issue,
                "Urgency": urgency,
                "Status": status,
                "Date": entry_date,
                "Owner": owner
            })
            st.sidebar.success(f"Escalation ID: {escalation_id} added successfully!")
        else:
            st.sidebar.error("Duplicate issue detected! Please verify.")
    else:
        st.sidebar.error("Please fill out all required fields.")

# Escalation Dashboard
st.subheader("🗂️ Escalation Dashboard")
if escalation_data:
    df = pd.DataFrame(escalation_data)
    
    # Download Option
    @st.cache
    def convert_to_csv(dataframe):
        return dataframe.to_csv(index=False).encode('utf-8')
    
    csv = convert_to_csv(df)
    st.download_button(
        label="Download Escalation Data",
        data=csv,
        file_name="escalations.csv",
        mime="text/csv"
    )
    
    # Display Data Table
    st.dataframe(df, width=1000, height=400)

else:
    st.info("No escalations added yet. Emails will be fetched every 5 minutes.")

# Escalation Insights and Metrics
st.markdown("### Escalation Insights")
if escalation_data:
    st.metric(label="Total Escalations", value=len(df))
    st.metric(label="High Urgency", value=len(df[df['Urgency'] == "High"]))
    st.metric(label="Critical Issues", value=len(df[df['Urgency'] == "Critical"]))
else:
    st.info("Metrics will appear once data is added.")

st.markdown("---")
st.caption("© 2025 EscalateAI - Enhanced Escalation Management Dashboard")
