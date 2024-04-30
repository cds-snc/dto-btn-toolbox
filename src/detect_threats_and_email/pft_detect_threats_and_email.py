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

dbConnectionString = os.getenv("COSMOS_MONGO_READ_URI", None)
EMAIL_ADDRESS = os.getenv("DTO_TEAM_INBOX", None)
NOTIFY_KEY = os.getenv("NOTIFY_DETECT_THREATS_API", None)
TEMPLATE_ID = os.getenv("NOTIFY_DETECT_THREATS_TEMPLATE_ID", None)
client = MongoClient(dbConnectionString)
print("Connected to DB.")
problem = client.pagesuccess.problem

print("Fetched the problem collection.")

N_DAYS_AGO = 1
#
today = datetime.now()
n_days_ago = today - timedelta(days=N_DAYS_AGO)
n_days_ago = n_days_ago.strftime("%Y-%m-%d")

past_n_days_query = {"problemDate": {"$gte": n_days_ago}}
problemCount = problem.count_documents(past_n_days_query)
print(f"Amount of entries in last {N_DAYS_AGO} days:")
print(problemCount)


# Function to read threat words from a file
def read_threat_words(file_path):
    """
    Read threat keywords from a specified file.

    This function opens a file from the given file path, reads its content, and returns a list of words. 
    Each word is expected to be separated by a comma. The function ensures that words are treated as whole words using regex boundaries.

    Args:
        file_path (str): The path to the file containing threat keywords.

    Returns:
        list of str: A list containing the formatted regex strings for each keyword.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return [
            f"\\b{word.strip()}\\b" for word in file.read().split(",") if word.strip()
        ]


# Construct paths to the threat words files
base_path = os.path.dirname(__file__)
english_threats_file = os.path.join(base_path, "threat_terms", "english_threats")
french_threats_file = os.path.join(base_path, "threat_terms", "french_threats")

# Read threat words from the files
english_threat_keywords = read_threat_words(english_threats_file)
french_threat_keywords = read_threat_words(french_threats_file)

# Combine both lists
threat_keywords = english_threat_keywords + french_threat_keywords

# Joining the keywords into a pattern
pattern_threat_keywords = "|".join(threat_keywords)


threats_in_past_n_days_query = {
    "$and": [
        {"problemDate": {"$gte": n_days_ago}},
        {"problemDetails": Regex(pattern_threat_keywords, "i")},
    ]
}
# List of fields to omit
fields_to_omit = [
    "tags",
    "airTableSync",
    "_class",
    "autoTagProcessed",
    "airTableSync",
    "topic",
    "resolution",
    "resolutionDate",
    "urlEntries",
]

problemCount = problem.count_documents(threats_in_past_n_days_query)

# Initialize an empty string to store the formatted output
today_formatted = today.strftime("%Y-%m-%d")

formatted_output = f"\n # Comments containing threat words from {n_days_ago} to {today_formatted} ({N_DAYS_AGO} days): {problemCount}\n\n"

formatted_output += "* [English threat terms](https://github.com/alpha-canada-ca/dto-btn-toolbox/blob/master/src/detect_threats_and_email/threat_terms/english_threats)\n"
formatted_output += "* [French threat terms](https://github.com/alpha-canada-ca/dto-btn-toolbox/blob/master/src/detect_threats_and_email/threat_terms/french_threats)\n"

for doc in problem.find(threats_in_past_n_days_query):
    formatted_output += "\n"  # Ensure a clear line break before each document
    for field, value in doc.items():
        if field not in fields_to_omit:
            formatted_output += f"**{field}**: {value}\n"
    formatted_output += "\n"  # Adds an extra newline for separation between documents

def get_notify_client():
    """
    Get the Notify client.
    """
    return NotificationsAPIClient(
        NOTIFY_KEY, base_url="https://api.notification.canada.ca"
    )


def send_report(notify_client, recipients, report_template_id, report_personalisation):
    """
    Send the report to the recipients via Notify.
    """
    for email in recipients:
        notify_client.send_email_notification(
            email_address=email,
            template_id=report_template_id,
            personalisation=report_personalisation,
        )


send_report(
    get_notify_client(),
    [EMAIL_ADDRESS],
    TEMPLATE_ID,
    {
        "entries": formatted_output,
        "date": f"{n_days_ago} to {today_formatted}",
    },
)
