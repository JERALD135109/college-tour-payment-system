import os
import json
import gspread
from google.oauth2.service_account import Credentials

# ===============================
# CONFIG
# ===============================
SHEET_NAME = "CollegeTourSystem"   # Must match your Google Sheet name exactly

# ===============================
# CONNECT TO GOOGLE SHEET
# ===============================
def get_sheet():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # Get credentials from Render Environment Variable
    creds_env = os.getenv("GOOGLE_CREDENTIALS")

    if not creds_env:
        raise Exception("GOOGLE_CREDENTIALS environment variable not set")

    # Convert string → dict
    creds_dict = json.loads(creds_env)

    # Create credentials object
    creds = Credentials.from_service_account_info(
        creds_dict,
        scopes=scopes
    )

    # Authorize client
    client = gspread.authorize(creds)

    # Open sheet by name
    spreadsheet = client.open(SHEET_NAME)

    # Use first worksheet
    worksheet = spreadsheet.sheet1

    return worksheet


# ===============================
# GET ALL MEMBERS
# ===============================
def get_all_members():
    sheet = get_sheet()
    records = sheet.get_all_records()
    return records


# ===============================
# UPDATE SINGLE CELL
# row_number → actual sheet row
# col_number → column index (1 based)
# ===============================
def update_member_cell(row_number, col_number, value):
    sheet = get_sheet()
    sheet.update_cell(row_number, col_number, value)


# ===============================
# UPDATE ENTIRE MEMBER ROW
# row_number → actual row index
# row_data → list of values
# ===============================
def update_member_row(row_number, row_data):
    sheet = get_sheet()
    sheet.update(f"A{row_number}:L{row_number}", [row_data])


# ===============================
# ADD NEW MEMBER
# ===============================
def add_new_member(row_data):
    sheet = get_sheet()
    sheet.append_row(row_data)