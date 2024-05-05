import gspread
from oauth2client.service_account import ServiceAccountCredentials
from scraper import get_website_data
import logging
from colorlog import ColoredFormatter
import time
from dotenv import load_dotenv
import os

load_dotenv()


# Setup logging with color formatting
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define color formatter
formatter = ColoredFormatter(
    "%(log_color)s[%(levelname)s] %(message)s",
    log_colors={
        "DEBUG": "cyan",
        "INFO": "green",
        "WARNING": "yellow",
        "ERROR": "red",
        "CRITICAL": "red,bg_white",
    },
)

# Configure the handler with the formatter
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Define the scopes for accessing Google Sheets and Google Drive
scope = ["https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive"]

# Path to the service account key file
credentials_path = "credentials.json"

# Authenticate using the service account credentials
credentials = ServiceAccountCredentials.from_json_keyfile_name(credentials_path, scope)

def get_google_sheet_data(spreadsheet_id):
    """
    Fetch data from a Google Sheet.

    Args:
        spreadsheet_id (str): The ID of the Google Sheet.

    Returns:
        list of lists: Data from the specified worksheet in the Google Sheet.
    """
    client = gspread.authorize(credentials)
    sheet = client.open_by_key(spreadsheet_id)
    worksheet = sheet.get_worksheet(0)
    data = worksheet.get_all_values()
    return data, worksheet

def process_domains(data, worksheet):
    """
    Process each domain in the Google Sheet data and save the updated data back to the sheet.

    Args:
        data (list of lists): The data fetched from the Google Sheet, including the header row.
        worksheet: The worksheet object for the Google Sheet.
    """
    # Column index mappings based on your file headers
    column_indices = {
        "Owner first name": 6,
        "email 1": 7,
        "email 2": 8,
        "email 3": 9,
        "reddit": 13,
        "twitter": 14,
        "Discord": 15,
        "Pinterest": 16,
        "facebook": 17,
        "instagram": 18,
        "Linkedin": 19,
        "youtube": 23,
        "Twitch": 24,
        "phone number": 22,
        # Add more mappings as needed
    }

    # Iterate through each row in the data, starting from index 1 (skip the header row)
    for index, row in enumerate(data[1:], start=2):  # Start from 2 to skip the header row
        # Ensure the row contains at least 3 columns (index 2 for domain)
        if len(row) > 2:
            domain = row[2]

            # Add protocol if missing
            if not domain.startswith(("http://", "https://")):
                domain = "https://" + domain

            logger.info(f"Processing domain from row {index}: {domain}")

            try:
                # Get data for the domain
                website_data = get_website_data(domain)
                logger.info(f"Data for domain {domain}: {website_data}")

                # Iterate through each column that needs to be updated
                for key, col_index in column_indices.items():
                    # Get the scraped data for the column
                    scraped_data = website_data.get("social_media_links", {}).get(key, "")
                    if key.startswith("email"):
                        scraped_data = website_data.get("owner_emails", [])[col_index - column_indices["email 1"]] if len(website_data.get("owner_emails", [])) > col_index - column_indices["email 1"] else ""
                    elif key == "phone number":
                        scraped_data = website_data.get("phone_numbers", [])[0] if len(website_data.get("phone_numbers", [])) > 0 else ""
                    
                    # Check if the scraped data is empty
                    if scraped_data:  # Only update if the scraped data is not empty
                        # Update the worksheet only if scraped data is not empty
                        worksheet.update_cell(index, col_index + 1, scraped_data)

                # Sleep to avoid overwhelming the server
                time.sleep(5)

            except Exception as e:
                logger.error(f"Error processing domain {domain} in row {index}: {e}")

# Replace with your Google Sheet ID
spreadsheet_id = os.environ.get("SHEET_ID")

data, worksheet = get_google_sheet_data(spreadsheet_id)

# Process each domain in the data
process_domains(data, worksheet)
