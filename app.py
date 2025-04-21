import streamlit as st
import pandas as pd

# Configure Page
st.set_page_config(page_title="EscalateAI", layout="wide")

# -------------------------------
# NLP-Based Issue Analysis
# -------------------------------
def analyze_issue(text):
    text_lower = text.lower()
    sentiment = "Negative" if any(
        word in text_lower for word in ["delay", "issue", "problem", "fail", "disatisfaction"]
    ) else "Positive"
    urgency = "High" if any(
        word in text_lower for word in ["urgent", "critical", "immediately", "business impact"]
    ) else "Low"
    escalation = sentiment == "Negative" and urgency == "High"
    return sentiment, urgency, escalation

# -------------------------------
# Logging Escalations
# -------------------------------
def log_case(row, sentiment, urgency, escalation):
    if "cases" not in st.session_state:
        st.session_state.cases = []
    
    st.session_state.cases.append({
        "Customer": row["Customer"],
        "Region/Pipe": row.get("Region/Pipe", "N/A"),
        "Contact Person": row.get("Contact Person", "N/A"),
        "Criticalness": row.get("Criticalness", "N/A"),
        "Issue reported date": row.get("Issue reported date", "N/A"),
        "Brief Issue": row["Brief Issue"],
        "Involved Product": row.get("Involved Product", "N/A"),
        "Action taken": row.get("Action taken", "N/A"),
        "Owner": row.get("Owner", "N/A"),
        "Customer Facing": row.get("Customer Facing", "N/A"),
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
            st.write(f"📅 Reported: {case['Issue reported date']} | 🌐 Region: {case.get('Region/Pipe', 'N/A')}")
            st.write(f"🛠 Product: {case['Involved Product']} | 👤 Owner: {case['Owner']}")
            st.write(f"🔹 Criticalness: `{case.get('Criticalness', 'N/A')}` | 🏢 Contact: {case.get('Contact Person', 'N/A')}")
            new_status = st.selectbox(
                "Update Status",
                ["Open", "In Progress", "Resolved"],
                index=["Open", "In Progress", "Resolved"].index(case["Status"]),
                key=f"{i}_status"
            )
            st.session_state.cases[i]["Status"] = new_status

# -------------------------------
# Main App Logic
# -------------------------------
st.title("🚨 EscalateAI - Intelligent Escalation Management")

with st.sidebar:
    st.header("📥 Upload Escalation Tracker")
    file = st.file_uploader("Upload Excel File", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    available_columns = set(df.columns)

    mandatory_fields = {"Customer", "Brief Issue", "Details", "Issue reported date", "Criticalness", "Involved Product", "Owner", "Status"}
    missing_cols = mandatory_fields - available_columns

    if missing_cols:
        st.error(f"Missing required columns: {', '.join(missing_cols)}")
    else:
        df["selector"] = df["Customer"].astype(str) + " | " + df["Brief Issue"].astype(str)
        selected = st.selectbox("Select Case", df["selector"])
        row = df[df["selector"] == selected].iloc[0]

        st.subheader("📄 Issue Details")
        for col in df.columns:
            st.write(f"**{col}:** {row.get(col, 'N/A')}")

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
