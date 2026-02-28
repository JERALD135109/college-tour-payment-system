import gspread
import os
import json
from google.oauth2.service_account import Credentials

# =============================
# GOOGLE SHEET FILE NAME
# =============================
SHEET_NAME = "CollegeTourSystem"   # <-- MUST match your Google Sheet file name exactly


# =============================
# CONNECT TO GOOGLE SHEET
# =============================
def get_sheet():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    # 🔹 1️⃣ Render Environment Mode
    creds_env = os.getenv("GOOGLE_CREDENTIALS")

    if creds_env:
        creds_dict = json.loads(creds_env)
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

    # 🔹 2️⃣ Local Development Mode (JSON File)
    else:
        creds = Credentials.from_service_account_file(
            "college-tour-credentials.json",   # <-- Must exist in project folder
            scopes=scopes
        )

    client = gspread.authorize(creds)

    # Open spreadsheet
    spreadsheet = client.open(SHEET_NAME)

    # ✅ Always use first tab (no worksheet name errors)
    worksheet = spreadsheet.sheet1

    return worksheet


# =============================
# GET ALL MEMBERS
# =============================
def get_all_members():
    sheet = get_sheet()
    records = sheet.get_all_records()
    return records


# =============================
# UPDATE FULL MEMBER ROW
# =============================
def update_member_row(index, data_dict):
    """
    index = 0-based index from get_all_members()
    data_dict = {"Column Name": value}
    """

    sheet = get_sheet()

    # Google Sheet row index (row 1 is header)
    row_number = index + 2

    headers = sheet.row_values(1)

    for key, value in data_dict.items():
        if key in headers:
            col_number = headers.index(key) + 1
            sheet.update_cell(row_number, col_number, value)


# =============================
# ADD NEW MEMBER
# =============================
def add_new_member(data_list):
    sheet = get_sheet()
    sheet.append_row(data_list)