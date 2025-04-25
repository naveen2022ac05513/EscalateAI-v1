import msal
import requests
import sqlite3
import smtplib
import streamlit as st
import pandas as pd
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


# 1. **Outlook Email Parsing using Microsoft Graph API**

def authenticate_graph_api(client_id, tenant_id, client_secret):
    authority = f"https://login.microsoftonline.com/{tenant_id}"
    scope = ["https://graph.microsoft.com/.default"]
    app = msal.ConfidentialClientApplication(client_id, authority=authority, client_credential=client_secret)
    result = app.acquire_token_for_client(scopes=scope)
    
    if "access_token" in result:
        return result["access_token"]
    else:
        raise Exception("Authentication failed.")

def get_emails_from_outlook(access_token):
    url = "https://graph.microsoft.com/v1.0/me/messages"
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get("value", [])
    else:
        raise Exception(f"Error fetching emails: {response.status_code}")

def parse_emails(emails):
    escalations = []
    for email in emails:
        subject = email.get("subject", "")
        body = email.get("bodyPreview", "")
        if "escalation" in subject.lower() or "urgent" in body.lower():
            escalations.append({
                "subject": subject,
                "body": body,
                "from": email.get("from", {}).get("emailAddress", {}).get("address", ""),
            })
    return escalations

# 2. **NLP Analysis for Sentiment, Urgency, and Escalation Triggers**

def analyze_sentiment(issue):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_score = analyzer.polarity_scores(issue)
    return sentiment_score['compound']

def determine_urgency(sentiment_score):
    if sentiment_score <= -0.5:
        return "High"
    elif sentiment_score <= -0.2:
        return "Medium"
    else:
        return "Low"

def analyze_escalations(escalations):
    for escalation in escalations:
        sentiment_score = analyze_sentiment(escalation["body"])
        urgency = determine_urgency(sentiment_score)
        escalation["sentiment_score"] = sentiment_score
        escalation["urgency"] = urgency
    return escalations

# 3. **Centralized Repository (SQLite)**

def create_db_connection(db_file="escalations.db"):
    return sqlite3.connect(db_file)

def create_escalations_table(conn):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS escalations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        escalation_id TEXT,
        customer_name TEXT,
        issue TEXT,
        sentiment_score REAL,
        urgency TEXT,
        status TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    conn.execute(create_table_sql)
    conn.commit()

def insert_escalation(conn, escalation):
    insert_sql = """
    INSERT INTO escalations (escalation_id, customer_name, issue, sentiment_score, urgency, status)
    VALUES (?, ?, ?, ?, ?, ?)
    """
    conn.execute(insert_sql, (escalation['escalation_id'], escalation['customer_name'], escalation['body'],
                              escalation['sentiment_score'], escalation['urgency'], "New"))
    conn.commit()

def fetch_escalations(conn):
    select_sql = "SELECT * FROM escalations"
    cursor = conn.cursor()
    cursor.execute(select_sql)
    return cursor.fetchall()

# 4. **Kanban Board and UI Enhancements using Streamlit**

def display_kanban_board(df):
    status_counts = df['Status'].value_counts()
    st.subheader("Escalation Status Overview")
    st.write(status_counts)

    fig, ax = plt.subplots()
    status_counts.plot(kind='bar', ax=ax)
    ax.set_title("Escalation Status Distribution")
    ax.set_xlabel("Status")
    ax.set_ylabel("Count")
    st.pyplot(fig)

def display_escalations_table(df):
    st.subheader("Escalations Table")
    st.write(df)

def get_example_data():
    return pd.DataFrame({
        "Escalation ID": ["SESICE-000001", "SESICE-000002", "SESICE-000003"],
        "Customer Name": ["Customer A", "Customer B", "Customer C"],
        "Issue": ["System down", "Service interruption", "High latency"],
        "Sentiment Score": [-0.6, -0.3, -0.7],
        "Urgency": ["High", "Normal", "High"],
        "Status": ["New", "In Progress", "Resolved"]
    })

# 5. **Real-time Alerts and Notifications (using SMTP)**

def send_email_notification(to_email, subject, body, smtp_server, smtp_port, smtp_user, smtp_password):
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, to_email, text)

# 6. **Excel Upload for Bulk Escalations**

uploaded_file = st.file_uploader("Upload an Excel file with Escalations", type="xlsx")

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.write("Escalation Data", df)

    # Sentiment Analysis
    analyzer = SentimentIntensityAnalyzer()

    def analyze_sentiment(issue):
        sentiment = analyzer.polarity_scores(issue)
        return sentiment['compound']  # Compound score for overall sentiment

    df['Sentiment Score'] = df['Brief Issue'].apply(analyze_sentiment)

    # Display escalations with sentiment scores
    st.subheader("Escalations with Sentiment Analysis")
    st.write(df)

# 7. **Integrating All Components**

def main():
    st.title("EscalateAI - Escalation Management Dashboard")

    # Fetch and display email escalations
    client_id = st.text_input("Enter your Microsoft client ID")
    tenant_id = st.text_input("Enter your Microsoft tenant ID")
    client_secret = st.text_input("Enter your Microsoft client secret", type="password")
    
    if client_id and tenant_id and client_secret:
        try:
            access_token = authenticate_graph_api(client_id, tenant_id, client_secret)
            emails = get_emails_from_outlook(access_token)
            escalations = parse_emails(emails)
            analyzed_escalations = analyze_escalations(escalations)
            st.subheader("Escalations from Outlook Emails")
            st.write(analyzed_escalations)
        except Exception as e:
            st.error(f"Error: {e}")

    # Database Operations
    conn = create_db_connection()
    create_escalations_table(conn)

    # Insert sample data
    if st.button("Insert Escalation to Database"):
        sample_escalation = {
            "escalation_id": "SESICE-000001",
            "customer_name": "Customer A",
            "body": "System is down",
            "sentiment_score": -0.6,
            "urgency": "High"
        }
        insert_escalation(conn, sample_escalation)
        st.success("Escalation inserted successfully!")

    # Display Database Entries
    if st.button("Fetch Escalations from Database"):
        escalations_from_db = fetch_escalations(conn)
        st.write(pd.DataFrame(escalations_from_db))

    # Visualize Escalations in Kanban board
    display_kanban_board(get_example_data())

    # Display Escalation Details Table
    display_escalations_table(get_example_data())

# Run the Streamlit App
if __name__ == "__main__":
    main()
