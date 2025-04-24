import uuid
import pandas as pd
import streamlit as st
from datetime import datetime

# Initialization
st.set_page_config(page_title="EscalateAI Dashboard", layout="wide")
st.title("📊 EscalateAI - Enhanced Escalation Management Dashboard")

# Admin Credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "password123"

# Escalation Data Storage
escalation_data = []

# Generate Unique Escalation ID
def generate_escalation_id():
    return f"ESC-{str(uuid.uuid4())[:8].upper()}"

# Function to Prevent Duplicate Issues
def is_duplicate(issue):
    return any(row["Issue"].lower() == issue.lower() for row in escalation_data)

# Admin Authentication
if "admin_authenticated" not in st.session_state:
    st.session_state["admin_authenticated"] = False

def admin_login():
    """Admin login function"""
    username = st.sidebar.text_input("Username", key="admin_username")
    password = st.sidebar.text_input("Password", type="password", key="admin_password")
    if st.sidebar.button("Login"):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.sidebar.success("Admin authenticated successfully!")
            st.session_state["admin_authenticated"] = True
        else:
            st.sidebar.error("Invalid credentials.")

# Sidebar: Admin Access for Email Configuration
if st.session_state["admin_authenticated"]:
    st.sidebar.header("📬 Configure Monitored Email Addresses")
    email_list = ["admin@example.com", "support@example.com"]  # Replace with dynamic email management.
    updated_list = st.sidebar.text_area("Enter email IDs separated by commas", ", ".join(email_list))
    if st.sidebar.button("💾 Update Email List"):
        new_emails = [e.strip() for e in updated_list.split(',') if e.strip()]
        email_list = new_emails  # Replace with code to store updated emails persistently (e.g., database).
        st.sidebar.success("Updated monitored email addresses.")
else:
    st.sidebar.header("Admin Login Required")
    admin_login()

# Sidebar: Add Escalation (Manual Entry or Excel Upload)
st.sidebar.header("📋 Add Escalation")
add_option = st.sidebar.radio("Add escalation details via:", ["Manual Entry", "Upload Excel"])

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

# File Upload for Bulk Escalation
if add_option == "Upload Excel":
    st.sidebar.subheader("Upload Escalation Data (Excel)")
    uploaded_file = st.sidebar.file_uploader("Choose an Excel file", type=["xlsx"])
    
    if uploaded_file:
        try:
            uploaded_data = pd.read_excel(uploaded_file)
            if all(col in uploaded_data.columns for col in ["Customer Name", "Issue", "Urgency", "Status", "Date", "Owner"]):
                for _, row in uploaded_data.iterrows():
                    if not is_duplicate(row["Issue"]):
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
                st.sidebar.error("The file must contain columns: 'Customer Name', 'Issue', 'Urgency', 'Status', 'Date', 'Owner'.")
        except Exception as e:
            st.sidebar.error(f"Error reading file: {e}")

# Centralized Escalation Dashboard
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
    st.info("No escalations added yet. Use the sidebar to add manual entries or upload data.")

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
