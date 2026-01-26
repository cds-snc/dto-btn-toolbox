"""
This module is designed to detect potential threats from database entries within the last N days using specified keywords in English and French.
It connects to a MongoDB database, reads entries, and searches for these keywords. If threats are detected, it formats the results and sends an email report using the Notify API client.
This system is used for monitoring and reporting potentially harmful or threatening content.

Environment variables used:
- COSMOS_MONGO_READ_URI: MongoDB connection string.
- NOTIFY_DETECT_THREATS_API: API key for Notify service.
- NOTIFY_DETECT_THREATS_TEMPLATE_ID: Template ID for email notifications.
- DTO_TEAM_INBOX: Email address of the DTO team inbox.
"""

import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from bson.regex import Regex
from notifications_python_client.notifications import NotificationsAPIClient

# Environment variables
dbConnectionString = os.getenv("COSMOS_MONGO_READ_URI", None)
NOTIFY_KEY = os.getenv("NOTIFY_DETECT_THREATS_API", None)
TEMPLATE_ID = os.getenv("NOTIFY_DETECT_THREATS_TEMPLATE_ID", None)
EMAIL_ADDRESSES = os.getenv("DTO_TEAM_INBOX", None)

# Parse email recipients from environment variable
if EMAIL_ADDRESSES:
    EMAIL_RECIPIENTS = [email.strip() for email in EMAIL_ADDRESSES.split(",")]
else:
    EMAIL_RECIPIENTS = []

# Database connection
client = MongoClient(dbConnectionString)
print("Connected to DB.")
problem = client.pagesuccess.problem
badwords = client.pagesuccess.badwords
print("Fetched the problem and badwords collections.")

# Calculate the date range for the query
N_DAYS_AGO = 1
today = datetime.now()
n_days_ago = today - timedelta(days=N_DAYS_AGO)
n_days_ago_str = n_days_ago.strftime("%Y-%m-%d")
today_formatted = today.strftime("%Y-%m-%d")
n_days_ago_day = n_days_ago.strftime("%A")
today_day = today.strftime("%A")

# Query MongoDB
past_n_days_query = {"problemDate": {"$gte": n_days_ago_str}}
problemCount = problem.count_documents(past_n_days_query)
print(f"Amount of entries in last {N_DAYS_AGO} days: {problemCount}")


# Fetch threat words from database
english_threat_words = badwords.find(
    {"type": "threat", "language": "en", "active": True}
)
french_threat_words = badwords.find(
    {"type": "threat", "language": "fr", "active": True}
)

english_threat_keywords = [f"\\b{doc['word']}\\b" for doc in english_threat_words]
french_threat_keywords = [f"\\b{doc['word']}\\b" for doc in french_threat_words]
threat_keywords = english_threat_keywords + french_threat_keywords

print(f"Loaded {len(english_threat_keywords)} English threat terms from database")
print(f"Loaded {len(french_threat_keywords)} French threat terms from database")
print(f"Total threat keywords: {len(threat_keywords)}")
pattern_threat_keywords = "|".join(threat_keywords)

# Query for threats
threats_in_past_n_days_query = {
    "$and": [
        {"problemDate": {"$gte": n_days_ago_str}},
        {"problemDetails": Regex(pattern_threat_keywords, "i")},
    ]
}
problemCount = problem.count_documents(threats_in_past_n_days_query)

# Build list of threat terms for email
english_terms_clean = [kw.replace("\\b", "") for kw in english_threat_keywords]
french_terms_clean = [kw.replace("\\b", "") for kw in french_threat_keywords]

# Prepare email content
formatted_output = f"""
[[en]]
# Threat Report

**Period:**

* **From:** {n_days_ago_day} [{n_days_ago_str}]  
* **To:** {today_day} [{today_formatted}]  

**Comments containing threat words (Last 1 day): {problemCount}**

**Monitoring {len(threat_keywords)} threat terms** ({len(english_threat_keywords)} English, {len(french_threat_keywords)} French)

---

[[/en]]
"""

# Remove additional information for each document
fields_to_omit = [
    "tags",
    "airTableSync",
    "_class",
    "autoTagProcessed",
    "topic",
    "resolution",
    "resolutionDate",
    "urlEntries",
]
for doc in problem.find(threats_in_past_n_days_query):
    formatted_output += "\n"
    for field, value in doc.items():
        if field not in fields_to_omit:
            formatted_output += f"**{field}**: {value}\n"
    formatted_output += "\n"

# Add threat terms list at the end
formatted_output += f"""
---

**Complete list of monitored threat terms:**

**English ({len(english_threat_keywords)}):**  
{', '.join(english_terms_clean)}

**French ({len(french_threat_keywords)}):**  
{', '.join(french_terms_clean)}
"""


# Notify client
def get_notify_client():
    return NotificationsAPIClient(
        NOTIFY_KEY, base_url="https://api.notification.canada.ca"
    )


# Send email
def send_report(notify_client, recipients, report_template_id, report_personalisation):
    for email in recipients:
        print(f"Sending email to: {email}")
        response = notify_client.send_email_notification(
            email_address=email,
            template_id=report_template_id,
            personalisation=report_personalisation,
        )
        print(f"✓ Email sent successfully! Notification ID: {response['id']}")


print(f"\nPreparing to send threat report...")
print(f"Total threats found: {problemCount}")
print(f"Recipients: {EMAIL_RECIPIENTS}")

send_report(
    get_notify_client(),
    EMAIL_RECIPIENTS,
    TEMPLATE_ID,
    {
        "entries": formatted_output,
        "date": f"{n_days_ago_str} to {today_formatted}",
    },
)

print("\n✓ Report sent successfully!")
