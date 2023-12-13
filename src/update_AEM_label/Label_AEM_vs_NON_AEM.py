import time
import requests
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from urllib.parse import urlparse, urlunparse

# [Rest of your imports like pandas, sklearn, etc. as per your original code]


def remove_query_params_and_fragments(url):
    """Remove query parameters and fragments from a URL."""
    parsed = urlparse(url)
    new_url = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))
    return new_url


# Set up Google Sheets API credentials
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "../../config/tier1_2_spreadsheets_credentials.json", scope
)
client = gspread.authorize(creds)

# Open the specific Google Sheet
sheet = client.open("Tier 2 - Urls").sheet1
list_of_entries = sheet.get_all_records()

bad_rows = 0
deleted_rows = 0
updated_rows = 0

counter = 2  # Start from the second row (assuming first row is header)
updates = []  # List to store updates
row_deletions = []  # List to store rows to be deleted

# Iterate over all list_of_entries
for entry in list_of_entries:
    url = entry["URL"]
    original_url = url  # Preserve the original URL for comparison

    # Check and remove query params and fragments
    parsed_url = urlparse(url)
    if parsed_url.query or parsed_url.fragment or url.endswith("#"):
        url = remove_query_params_and_fragments(url)
        updates.append({"range": f"A{counter}", "values": [[url]]})
        print(f"{counter}, REMOVED QUERY PARAMS AND FRAGMENTS: {url}")
        updated_rows += 1

    # Send an HTTP request to the modified URL
    response = None
    try:
        response = requests.get(url, timeout=10)
    except Exception as e:
        print(f"{counter}, Exception occurred: {e}")

    # Process the response
    if response:
        aem_status = "AEM" if "adobedtm" in response.text else "non-AEM"
        updates.append({"range": f"B{counter}", "values": [[aem_status]]})

        if "gc-pg-hlpfl" in response.text or "page-feedback" in response.text:
            print(f"{counter}, GOOD: {url} contains tool gc-pg-hlpfl in the HTML IDs.")
        elif response.status_code == 404:
            print(f"{counter}, NO RESPONSE: Deleting entry with URL {url}")
            deleted_rows += 1
            row_deletions.append(counter)
        elif response.status_code == 200 and (
            "gc-pg-hlpfl" not in response.text or "page-feedback" not in response.text
        ):
            print(f"{counter}, BAD: No tool, deleting entry with URL: {url}")
            bad_rows += 1
            row_deletions.append(counter)
        else:
            print(f"{counter}, Response: {response.status_code}, URL: {url}")

    counter += 1

# Apply all updates in one batch request
if updates:
    sheet.batch_update(updates)

# Delete rows in reverse order to avoid changing the indices of remaining rows
for row_num in reversed(row_deletions):
    sheet.delete_rows(row_num)

print("Update and deletion process completed.")
print(f"Updated rows: {updated_rows}")
print(f"Deleted rows (no response): {deleted_rows}")
print(f"Bad rows (no tool): {bad_rows}")
