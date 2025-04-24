import uuid
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import random
import time
import threading
import streamlit as st
import json
import os

# Simulated Email Parsing
class OutlookParser:
    def __init__(self):
        self.email_list_file = "monitored_emails.json"
        if not os.path.exists(self.email_list_file):
            with open(self.email_list_file, 'w') as f:
                json.dump([f"user{i}@example.com" for i in range(1, 501)], f)

    def get_monitored_emails(self):
        with open(self.email_list_file, 'r') as f:
            return json.load(f)

    def update_monitored_emails(self, new_list):
        with open(self.email_list_file, 'w') as f:
            json.dump(new_list, f)

    def fetch_unread_emails(self):
        monitored = self.get_monitored_emails()
        emails = []
        for email_id in monitored:
            emails.append({
                'id': str(uuid.uuid4()),
                'from': email_id,
                'subject': 'Issue reported - please check',
                'body': f'This is a simulated issue report from {email_id}. Immediate attention is required.',
                'received_time': datetime.now().isoformat()
            })
        return emails

# NLP Analysis
class NLPAnalyzer:
    NEGATIVE_KEYWORDS = [
        'issue', 'error', 'problem', 'failure', 'broken', 'down', 'outage', 'bug', 'crash', 'defect',
        'malfunction', 'glitch', 'degradation', 'discharging', 'tripped', 'damaged', 'blank', 'leaking',
        'negative pressure', 'burnt', 'corrosion', 'isolated', 'trip', 'fuse degrade', 'delay', 'rejection',
        'mismatch', 'non-compliance', 'frustrated', 'dissatisfaction'
    ]
    URGENCY_VERBATIMS = [
        'urgent', 'critical', 'immediately', 'as soon as possible', 'high priority', 'emergency',
        'needs immediate attention', 'blocking', 'cannot wait'
    ]
    ESCALATION_VERBATIMS = [
        'disappointed', 'frustrated', 'unacceptable', 'not satisfied', 'very unhappy', 'worst experience',
        'escalation', 'raise this', 'need to escalate', "won't tolerate", 'switching provider',
        'no response', 'lack of action', 'unresolved issues', 'risk facing NC'
    ]

    def analyze_email(self, text):
        lower_text = text.lower()
        sentiment = 'negative' if any(word in lower_text for word in self.NEGATIVE_KEYWORDS + self.ESCALATION_VERBATIMS) else 'neutral'
        urgency = 'high' if any(phrase in lower_text for phrase in self.URGENCY_VERBATIMS) else 'normal'
        is_escalation = any(word in lower_text for word in self.NEGATIVE_KEYWORDS + self.ESCALATION_VERBATIMS)
        triggers = [word for word in self.NEGATIVE_KEYWORDS + self.ESCALATION_VERBATIMS if word in lower_text]
        return {
            'sentiment': sentiment,
            'urgency': urgency,
            'is_escalation': is_escalation,
            'triggers': triggers
        }

# Case Logger
class CaseLogger:
    def __init__(self):
        self.db = {}

    def generate_case_id(self):
        return f"SESICE-{str(random.randint(10000, 99999))}"

    def log_case(self, email, analysis):
        case_id = self.generate_case_id()
        self.db[case_id] = {
            'email': email,
            'analysis': analysis,
            'created_at': datetime.now(),
            'status': 'New'
        }
        return case_id

# Kanban Board
class KanbanManager:
    def __init__(self):
        self.board = {}

    def add_to_board(self, case_id, analysis):
        self.board[case_id] = {
            'status': 'New',
            'priority': analysis['urgency'],
            'details': analysis
        }

# Alert System
class AlertManager:
    def send_alert(self, case_id, analysis):
        print(f"[ALERT] 🚨 Escalation detected! Case ID: {case_id} | Urgency: {analysis['urgency']} | Sentiment: {analysis['sentiment']}")

# Collaboration
class CollaborationHub:
    def share_case_with_team(self, case_id):
        print(f"[SHARE] Case {case_id} shared with Engineering and Customer Success teams.")

# Predictive Insights
class EscalationPredictor:
    def update_model_with_case(self, case_id, analysis):
        print(f"[AI] Model updated with case {case_id} for future prediction enhancement.")

# EscalateAI Controller
class EscalateAI:
    def __init__(self):
        self.email_parser = OutlookParser()
        self.analyzer = NLPAnalyzer()
        self.logger = CaseLogger()
        self.kanban = KanbanManager()
        self.alerts = AlertManager()
        self.collab = CollaborationHub()
        self.predictor = EscalationPredictor()

    def process_incoming_emails(self):
        new_cases = []
        emails = self.email_parser.fetch_unread_emails()
        for email in emails:
            analysis_result = self.analyzer.analyze_email(email['body'])
            if analysis_result['is_escalation']:
                escalation_id = self.logger.log_case(email, analysis_result)
                self.kanban.add_to_board(escalation_id, analysis_result)
                self.alerts.send_alert(escalation_id, analysis_result)
                self.collab.share_case_with_team(escalation_id)
                self.predictor.update_model_with_case(escalation_id, analysis_result)
                new_cases.append((escalation_id, email['from'], analysis_result))
        return new_cases

# Streamlit UI
st.set_page_config(page_title="EscalateAI Dashboard", layout="wide")
st.title("📊 EscalateAI - Escalation Management Dashboard")

ai = EscalateAI()

st.sidebar.header("📬 Configure Monitored Email Addresses")
email_list = ai.email_parser.get_monitored_emails()
updated_list = st.sidebar.text_area("Enter email IDs separated by commas", ", ".join(email_list))
if st.sidebar.button("💾 Update Email List"):
    new_emails = [e.strip() for e in updated_list.split(',') if e.strip()]
    ai.email_parser.update_monitored_emails(new_emails)
    st.sidebar.success("Updated monitored email addresses.")

if st.button("🔄 Fetch New Emails"):
    new_cases = ai.process_incoming_emails()
    st.success(f"Processed {len(new_cases)} new escalation(s).")

st.subheader("🗂️ Active Escalation Kanban Board")
kanban_data = ai.kanban.board

columns = {'New': [], 'In Progress': [], 'Resolved': []}
for case_id, case_data in kanban_data.items():
    status = case_data['status']
    card = f"**{case_id}**\n- Priority: {case_data['priority']}\n- Sentiment: {case_data['details']['sentiment']}"
    columns[status].append(card)

cols = st.columns(3)
for i, status in enumerate(['New', 'In Progress', 'Resolved']):
    with cols[i]:
        st.markdown(f"### {status}")
        for card in columns[status]:
            st.markdown(f"📝 {card}", unsafe_allow_html=True)

st.markdown("---")
st.caption("© 2025 EscalateAI - Built for smarter customer escalation management")
