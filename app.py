from flask import Flask, render_template, request, redirect, url_for, session
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

app = Flask(__name__)
app.secret_key = "supersecretkey"

# ==============================
# CONFIG
# ==============================

ADMIN_PASSWORD = "jerald@70928"
SHEET_NAME = "CollegeTourSystem"

# ==============================
# GOOGLE SHEETS CONNECTION
# ==============================

def get_sheet():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_env = os.getenv("GOOGLE_CREDENTIALS")

    if not creds_env:
        raise Exception("GOOGLE_CREDENTIALS not set in Render")

    creds_dict = json.loads(creds_env)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

    client = gspread.authorize(creds)

    spreadsheet = client.open(SHEET_NAME)
    worksheet = spreadsheet.sheet1

    return worksheet


def get_all_members():
    sheet = get_sheet()
    records = sheet.get_all_records()
    return records


# ==============================
# HOME
# ==============================

@app.route("/")
def home():
    return render_template("login.html")


# ==============================
# MEMBER LOGIN
# ==============================

@app.route("/login", methods=["POST"])
def login():
    name = request.form["name"]
    members = get_all_members()

    for m in members:
        if m["Name"] == name:
            session["user"] = name
            return redirect(url_for("dashboard"))

    return "User not found"


# ==============================
# MEMBER DASHBOARD
# ==============================

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))

    name = session["user"]
    members = get_all_members()

    for m in members:
        if m["Name"] == name:

            total = float(m.get("Total Amount", 0) or 0)
            paid = float(m.get("Paid Amount", 0) or 0)
            balance = total - paid

            # Payment status logic
            if paid == 0:
                status = "Pending"
            elif balance > 0:
                status = "Partially Paid"
            else:
                status = "Verified"

            return render_template(
                "dashboard.html",
                user=m,
                total=total,
                paid=paid,
                balance=balance,
                status=status
            )

    return "User not found"


# ==============================
# SUBMIT PAYMENT (FIXED)
# ==============================

@app.route("/submit_payment", methods=["POST"])
def submit_payment():
    if "user" not in session:
        return redirect(url_for("home"))

    name = session["user"]
    amount = float(request.form["amount"])
    reference = request.form["reference"]

    sheet = get_sheet()
    members = sheet.get_all_records()

    for index, m in enumerate(members, start=2):
        if m["Name"] == name:

            total = float(m.get("Total Amount", 0) or 0)
            previous_paid = float(m.get("Paid Amount", 0) or 0)

            new_paid = previous_paid + amount
            balance = total - new_paid

            # ✅ FIXED UPDATE FORMAT
            sheet.update(f"D{index}", [[new_paid]])          # Paid Amount
            sheet.update(f"E{index}", [[balance]])           # Balance
            sheet.update(f"G{index}", [[reference]])         # Reference
            sheet.update(f"F{index}", [["Submitted"]])       # Status
            sheet.update(f"J{index}", [[datetime.now().strftime("%d-%m-%Y %H:%M:%S")]])

            break

    return redirect(url_for("dashboard"))


# ==============================
# ADMIN LOGIN
# ==============================

@app.route("/admin")
def admin():
    return render_template("admin_login.html")


@app.route("/admin_login", methods=["POST"])
def admin_login():
    if request.form["password"] == ADMIN_PASSWORD:
        session["admin"] = True
        return redirect(url_for("admin_dashboard"))
    return "Wrong password"


# ==============================
# ADMIN DASHBOARD
# ==============================

@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin"))

    members = get_all_members()
    return render_template("admin_dashboard.html", members=members)


# ==============================
# VERIFY PAYMENT (FIXED)
# ==============================

@app.route("/verify/<name>")
def verify(name):
    if "admin" not in session:
        return redirect(url_for("admin"))

    sheet = get_sheet()
    members = sheet.get_all_records()

    for index, m in enumerate(members, start=2):
        if m["Name"] == name:

            total = float(m.get("Total Amount", 0) or 0)
            paid = float(m.get("Paid Amount", 0) or 0)
            balance = total - paid

            verified_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

            if balance <= 0:
                status = "Verified"
            else:
                status = "Partially Paid"

            # ✅ FIXED UPDATE FORMAT
            sheet.update(f"F{index}", [[status]])
            sheet.update(f"K{index}", [[verified_time]])

            break

    return redirect(url_for("admin_dashboard"))


# ==============================
# LOGOUT
# ==============================

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


# ==============================
# RUN
# ==============================

if __name__ == "__main__":
    app.run(debug=True)