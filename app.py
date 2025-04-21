import streamlit as st

# Placeholder for EscalateAI interface
st.title("EscalateAI - Customer Escalation Management")
st.write("Welcome to the escalation tool. Here we track, predict, and manage customer escalations.")

# Add more functionality as needed
import streamlit as st

# -------------------------------
# Simulated Email Fetching
# -------------------------------
def fetch_emails():
    return {
        "High latency in dashboard": "Hi team, our dashboard is extremely slow. Please resolve this urgently.",
        "Login issues": "Users can't log in since morning. It's affecting operations.",
        "General feedback": "The new UI looks great. No issues so far."
    }

# -------------------------------
# NLP Analysis (Basic)
# -------------------------------
def analyze_email(content):
    sentiment = "Negative" if "slow" in content or "can't" in content else "Positive"
    urgency = "High" if "urgent" in content or "affecting" in content else "Low"
    escalation_triggered = sentiment == "Negative" and urgency == "High"

    if escalation_triggered:
        st.warning("🚨 Escalation Detected! Alerting team...")
        send_alert(content)

    return {
        "sentiment": sentiment,
        "urgency": urgency,
        "escalation": escalation_triggered
    }

# -------------------------------
# Simulated Slack-style Alert
# -------------------------------
def send_alert(message):
    st.write(f"🔔 *Slack alert sent:* {message}")  # Replace with actual Slack integration if needed

# -------------------------------
# Logging and Kanban Tracking
# -------------------------------
def log_case(subject, content, result):
    if "escalations" not in st.session_state:
        st.session_state.escalations = []

    st.session_state.escalations.append({
        "subject": subject,
        "content": content,
        "sentiment": result["sentiment"],
        "urgency": result["urgency"],
        "status": "Open"
    })

def show_kanban():
    if "escalations" not in st.session_state or not st.session_state.escalations:
        st.info("No escalations logged yet.")
        return

    cols = st.columns(3)
    status_cols = {"Open": cols[0], "In Progress": cols[1], "Resolved": cols[2]}

    for case in st.session_state.escalations:
        with status_cols[case["status"]]:
            st.markdown("----")
            st.markdown(f"**🧾 {case['subject']}**")
            st.write(f"Sentiment: `{case['sentiment']}` | Urgency: `{case['urgency']}`")
            new_status = st.selectbox("Status", ["Open", "In Progress", "Resolved"], index=["Open", "In Progress", "Resolved"].index(case["status"]), key=case["subject"])
            case["status"] = new_status

# -------------------------------
# Streamlit App Layout
# -------------------------------
st.set_page_config(page_title="EscalateAI", layout="wide")
st.title("🚨 EscalateAI - Customer Escalation Management")

emails = fetch_emails()

with st.sidebar:
    st.header("📥 Incoming Emails")
    selected_email = st.selectbox("Select an Email", emails.keys())

    if selected_email:
        content = emails[selected_email]
        st.write(content)

        if st.button("🔍 Analyze & Log Escalation"):
            result = analyze_email(content)
            log_case(selected_email, content, result)
            st.success("Escalation logged successfully!")

st.header("📌 Escalation Kanban Board")
show_kanban()
