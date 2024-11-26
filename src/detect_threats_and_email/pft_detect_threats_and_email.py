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
EMAIL_ADDRESSES = os.getenv("DTO_TEAM_INBOX", None)
NOTIFY_KEY = os.getenv("NOTIFY_DETECT_THREATS_API", None)
TEMPLATE_ID = os.getenv("NOTIFY_DETECT_THREATS_TEMPLATE_ID", None)

# Parse email recipients
if EMAIL_ADDRESSES:
    EMAIL_RECIPIENTS = [email.strip() for email in EMAIL_ADDRESSES.split(",")]
else:
    EMAIL_RECIPIENTS = []

# Database connection
client = MongoClient(dbConnectionString)
print("Connected to DB.")
problem = client.pagesuccess.problem
print("Fetched the problem collection.")

# Calculate the date range for the query
N_DAYS_AGO = 1
today = datetime.now()
n_days_ago = today - timedelta(days=N_DAYS_AGO)
n_days_ago = n_days_ago.strftime("%Y-%m-%d")
today_formatted = today.strftime("%Y-%m-%d")

# Query MongoDB
past_n_days_query = {"problemDate": {"$gte": n_days_ago}}
problemCount = problem.count_documents(past_n_days_query)
print(f"Amount of entries in last {N_DAYS_AGO} days: {problemCount}")

# Function to read threat words from a file
def read_threat_words(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return [f"\\b{word.strip()}\\b" for word in file.read().split(",") if word.strip()]

# Paths to threat terms files
base_path = os.path.dirname(__file__)
english_threats_file = os.path.join(base_path, "threat_terms", "english_threats")
french_threats_file = os.path.join(base_path, "threat_terms", "french_threats")

# Read threat terms
english_threat_keywords = read_threat_words(english_threats_file)
french_threat_keywords = read_threat_words(french_threats_file)
threat_keywords = english_threat_keywords + french_threat_keywords
pattern_threat_keywords = "|".join(threat_keywords)

# Query for threats
threats_in_past_n_days_query = {
    "$and": [
        {"problemDate": {"$gte": n_days_ago}},
        {"problemDetails": Regex(pattern_threat_keywords, "i")},
    ]
}
problemCount = problem.count_documents(threats_in_past_n_days_query)

# Prepare email content
formatted_output = f"""
[[en]]
# Threat Report

**Period:**

* **From:** Wednesday [{n_days_ago}]  
* **To:** Thursday [{today_formatted}]  

**Comments containing threat words (Last 1 day): {problemCount}**

* [English threat terms](https://github.com/alpha-canada-ca/dto-btn-toolbox/blob/master/src/detect_threats_and_email/threat_terms/english_threats)  
* [French threat terms](https://github.com/alpha-canada-ca/dto-btn-toolbox/blob/master/src/detect_threats_and_email/threat_terms/french_threats)

[[/en]]
"""

# Remove additional information for each document
fields_to_omit = [
    "tags", "airTableSync", "_class", "autoTagProcessed", "topic", "resolution",
    "resolutionDate", "urlEntries",
]
for doc in problem.find(threats_in_past_n_days_query):
    formatted_output += "\n"
    for field, value in doc.items():
        if field not in fields_to_omit:
            formatted_output += f"**{field}**: {value}\n"
    formatted_output += "\n"

# Notify client
def get_notify_client():
    return NotificationsAPIClient(
        NOTIFY_KEY, base_url="https://api.notification.canada.ca"
    )

# Send email
def send_report(notify_client, recipients, report_template_id, report_personalisation):
    for email in recipients:
        notify_client.send_email_notification(
            email_address=email,
            template_id=report_template_id,
            personalisation=report_personalisation,
        )

send_report(
    get_notify_client(),
    EMAIL_RECIPIENTS,
    TEMPLATE_ID,
    {
        "entries": formatted_output,
        "date": f"{n_days_ago} to {today_formatted}",
    },
)
