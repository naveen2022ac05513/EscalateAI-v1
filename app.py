import streamlit as st
import pandas as pd

# Set Page Configuration
st.set_page_config(page_title="EscalateAI", layout="wide")

# ---------------------------------
# NLP-Based Issue Analysis
# ---------------------------------
def analyze_issue(text):
    text_lower = text.lower()
    sentiment = "Negative" if any(
        word in text_lower for word in ["delay", "issue", "problem", "fail", "dissatisfaction"]
    ) else "Positive"
    urgency = "High" if any(
        word in text_lower for word in ["urgent", "critical", "immediately", "business impact"]
    ) else "Low"
    escalation = sentiment == "Negative" and urgency == "High"
    return sentiment, urgency, escalation

# ---------------------------------
# Logging Escalations
# ---------------------------------
def log_case(row, sentiment, urgency, escalation):
    if "cases" not in st.session_state:
        st.session_state.cases = []
    
    st.session_state.cases.append({
        "Brief Issue": row["brief issue"],
        "Customer": row.get("customer", "N/A"),
        "Reported Date": row.get("issue reported date", "N/A"),
        "Action Taken": row.get("action taken", "N/A"),
        "Owner": row.get("owner", "N/A"),
        "Status": row.get("status", "Open"),
        "Sentiment": sentiment,
        "Urgency": urgency,
        "Escalated": escalation,
    })

def show_kanban():
    if "cases" not in st.session_state or not st.session_state.cases:
        st.info("No escalations logged yet.")
        return

    st.subheader("📌 Escalation Kanban Board")
    cols = st.columns(3)
    stages = {"Open": cols[0], "In Progress": cols[1], "Resolved": cols[2]}

    for i, case in enumerate(st.session_state.cases):
        with stages[case["Status"]]:
            st.markdown("----")
            st.markdown(f"**🧾 Issue: {case['Brief Issue']}**")
            st.write(f"🔹 Sentiment: `{case['Sentiment']}` | Urgency: `{case['Urgency']}`")
            st.write(f"📅 Reported: {case['Reported Date']} | 👤 Owner: {case.get('Owner', 'N/A')}")
            st.write(f"✅ Action Taken: {case.get('Action Taken', 'N/A')}")
            new_status = st.selectbox(
                "Update Status",
                ["Open", "In Progress", "Resolved"],
                index=["Open", "In Progress", "Resolved"].index(case["Status"]),
                key=f"{i}_status"
            )
            st.session_state.cases[i]["Status"] = new_status

# ---------------------------------
# Main App Logic
# ---------------------------------
st.title("🚨 EscalateAI - Generic Escalation Tracking")

with st.sidebar:
    st.header("📥 Upload Escalation Tracker")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])

if file:
    df = pd.read_excel(file)

    # Normalize column names: Remove extra spaces, convert to lowercase for comparison
    df.columns = df.columns.str.strip().str.lower().str.replace(" +", " ", regex=True)

    required_cols = {"brief issue"}
    missing_cols = required_cols - set(df.columns)

    if missing_cols:
        st.error("The uploaded Excel file must contain at least an 'Issue' column.")
    else:
        df["selector"] = df["brief issue"].astype(str)
        selected = st.selectbox("Select Case", df["selector"])
        row = df[df["selector"] == selected].iloc[0]

        st.subheader("📄 Issue Details")
        for col in df.columns:
            st.write(f"**{col.capitalize()}:** {row.get(col, 'N/A')}")

        if st.button("🔍 Analyze & Log Escalation"):
            sentiment, urgency, escalated = analyze_issue(row["brief issue"])
            log_case(row, sentiment, urgency, escalated)
            if escalated:
                st.warning("🚨 Escalation Triggered!")
            else:
                st.success("Logged without escalation.")

# Show Kanban board
show_kanban()
