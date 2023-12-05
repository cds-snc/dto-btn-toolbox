from configparser import ConfigParser
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime, timedelta
from bson.regex import Regex
import os

from notifications_python_client.notifications import NotificationsAPIClient

# get api key from config file and get data from AirTabe
config = ConfigParser()
config.read("../../config/config.ini")
dbConnectionString = config.get("default", "mongo_db")
email_address = config.get("default", "email_address")
NOTIFY_KEY = config.get("default", "detect_threats_API")
TEMPLATE_ID = config.get("default", "template_ID")
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

# Now formatted_output contains the entire formatted string
print(formatted_output)


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
    [email_address],
    TEMPLATE_ID,
    {
        "entries": formatted_output,
        "date": f"{n_days_ago} to {today_formatted}",
    },
)
