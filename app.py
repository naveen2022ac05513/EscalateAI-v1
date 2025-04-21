import streamlit as st
import pandas as pd

# Must be first!
st.set_page_config(page_title="EscalateAI", layout="wide")

# -------------------------------
# Basic NLP Simulation
# -------------------------------
def analyze_issue(text):
    text_lower = text.lower()
    sentiment = "Negative" if any(word in text_lower for word in ["delay", "not", "issue", "problem", "fail"]) else "Positive"
    urgency = "High" if any(word in text_lower for word in ["urgent", "asap", "immediately", "critical"]) else "Low"
    escalation = sentiment == "Negative" and urgency == "High"
    return sentiment, urgency, escalation

# -------------------------------
# Logging & Kanban
# -------------------------------
def log_case(row, sentiment, urgency, escalation):
    if "cases" not in st.session_state:
        st.session_state.cases = []
    
    st.session_state.cases.append({
        "Customer": row["Customer"],
        "Brief Issue": row["Brief Issue"],
        "Details": row.get("Details", ""),
        "Criticalness": row.get("Criticalness", ""),
        "Issue reported date": row.get("Issue reported date", ""),
        "Involved Product": row.get("Involved Product", ""),
        "Owner": row.get("Owner", ""),
        "Status": "Open",
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
            st.markdown(f"**🧾 {case['Customer']} - {case['Brief Issue']}**")
            st.write(f"🔹 Sentiment: `{case['Sentiment']}` | Urgency: `{case['Urgency']}`")
            st.write(f"📅 Reported: {case['Issue reported date']}")
            st.write(f"🛠 Product: {case['Involved Product']} | 👤 Owner: {case['Owner']}")
            new_status = st.selectbox(
                "Update Status",
                ["Open", "In Progress", "Resolved"],
                index=["Open", "In Progress", "Resolved"].index(case["Status"]),
                key=f"{i}_status"
            )
            st.session_state.cases[i]["Status"] = new_status

# -------------------------------
# Main App
# -------------------------------
st.title("🚨 EscalateAI - Excel-Powered Escalation Management")

with st.sidebar:
    st.header("📥 Upload Escalation Tracker")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    required_cols = {"Customer", "Brief Issue", "Details"}
    if not required_cols.issubset(df.columns):
        st.error("Excel must include at least 'Customer', 'Brief Issue', and 'Details' columns.")
    else:
        df["selector"] = df["Customer"].astype(str) + " | " + df["Brief Issue"].astype(str)
        selected = st.selectbox("Select Case", df["selector"])
        row = df[df["selector"] == selected].iloc[0]

        st.subheader("📄 Issue Details")
        st.write(f"**Customer:** {row['Customer']}")
        st.write(f"**Issue:** {row['Brief Issue']}")
        st.write(f"**Details:** {row.get('Details', '')}")
        st.write(f"**Reported Date:** {row.get('Issue reported date', '')}")
        st.write(f"**Criticalness:** {row.get('Criticalness', '')}")

        if st.button("🔍 Analyze & Log Escalation"):
            combined_text = str(row["Brief Issue"]) + " " + str(row.get("Details", ""))
            sentiment, urgency, escalated = analyze_issue(combined_text)
            log_case(row, sentiment, urgency, escalated)
            if escalated:
                st.warning("🚨 Escalation Triggered!")
            else:
                st.success("Logged without escalation.")

# Show Kanban board
show_kanban()
