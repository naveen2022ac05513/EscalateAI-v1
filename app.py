import uuid
import pandas as pd
import streamlit as st
from datetime import datetime

# Initialization
st.set_page_config(page_title="EscalateAI Dashboard", layout="wide")
st.title("📊 EscalateAI - Enhanced Escalation Management Dashboard")

# Simulated Database
escalation_data = []

# Function to Generate Unique Escalation IDs
def generate_escalation_id():
    return f"ESC-{str(uuid.uuid4())[:8].upper()}"

# Sidebar for Manual Entry and File Upload
st.sidebar.header("📋 Add Escalation")
add_option = st.sidebar.radio("How do you want to add escalation details?", ["Manual Entry", "Upload Excel"])

# Manual Entry Form
if add_option == "Manual Entry":
    st.sidebar.subheader("Manual Escalation Entry")
    customer_name = st.sidebar.text_input("Customer Name")
    issue = st.sidebar.text_area("Issue Description")
    urgency = st.sidebar.selectbox("Urgency Level", ["Normal", "Urgent", "High", "Critical"])
    owner = st.sidebar.text_input("Owner")
    status = st.sidebar.selectbox("Status", ["New", "In Progress", "Escalated", "Resolved"])
    entry_date = st.sidebar.date_input("Date", datetime.now())
    
    if st.sidebar.button("Add Escalation"):
        if customer_name and issue and owner:
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
            st.sidebar.error("Please fill out all required fields.")

# File Upload
if add_option == "Upload Excel":
    st.sidebar.subheader("Upload Escalation Data (Excel)")
    uploaded_file = st.sidebar.file_uploader("Choose an Excel file", type=["xlsx"])
    
    if uploaded_file:
        try:
            uploaded_data = pd.read_excel(uploaded_file)
            if all(col in uploaded_data.columns for col in ["Customer Name", "Issue", "Urgency", "Status", "Date", "Owner"]):
                for _, row in uploaded_data.iterrows():
                    escalation_data.append({
                        "Escalation ID": generate_escalation_id(),
                        "Customer Name": row["Customer Name"],
                        "Issue": row["Issue"],
                        "Urgency": row["Urgency"],
                        "Status": row["Status"],
                        "Date": row["Date"],
                        "Owner": row["Owner"]
                    })
                st.sidebar.success("Escalation data uploaded successfully!")
            else:
                st.sidebar.error("The file must have the required columns: 'Customer Name', 'Issue', 'Urgency', 'Status', 'Date', 'Owner'.")
        except Exception as e:
            st.sidebar.error(f"Error reading the file: {e}")

# Escalation Table
st.subheader("🗂️ Escalation Dashboard")
if escalation_data:
    df = pd.DataFrame(escalation_data)
    st.dataframe(df, width=1000, height=400)
else:
    st.info("No escalations added yet. Use the sidebar to add manual entries or upload data.")

# Escalation Metrics
st.markdown("### Escalation Insights")
if escalation_data:
    df = pd.DataFrame(escalation_data)
    st.metric(label="Total Escalations", value=len(df))
    st.metric(label="High Urgency", value=len(df[df['Urgency'] == "High"]))
    st.metric(label="Critical Issues", value=len(df[df['Urgency'] == "Critical"]))
else:
    st.info("Metrics will appear once data is added.")

st.markdown("---")
st.caption("© 2025 EscalateAI - Enhanced Escalation Management Dashboard")
