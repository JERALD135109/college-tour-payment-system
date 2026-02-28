from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from generate_invoice import create_invoice

app = Flask(__name__)
app.secret_key = "supersecretkey"

# =========================
# CONFIG
# =========================
ADMIN_PASSWORD = "jerald@70928"
SHEET_NAME = "CollegeTour"
UPLOAD_FOLDER = "static/uploads"
INVOICE_FOLDER = "invoices"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(INVOICE_FOLDER, exist_ok=True)

# =========================
# GOOGLE SHEET CONNECTION
# =========================
def get_sheet():

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_env = os.getenv("GOOGLE_CREDENTIALS")

    if not creds_env:
        raise Exception("GOOGLE_CREDENTIALS environment variable not set")

    creds_dict = json.loads(creds_env)
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

    client = gspread.authorize(creds)

    spreadsheet = client.open(SHEET_NAME)
    worksheet = spreadsheet.sheet1

    return worksheet


def get_all_members():
    sheet = get_sheet()
    return sheet.get_all_records()


def update_member_row(row_number, data):
    sheet = get_sheet()
    sheet.update(f"A{row_number}:L{row_number}", [data])


def add_new_member(data):
    sheet = get_sheet()
    sheet.append_row(data)


# =========================
# EMAIL FUNCTION
# =========================
def send_payment_email(to_email, name, amount):

    sender_email = "gjerald121@gmail.com"
    sender_password = os.getenv("EMAIL_PASSWORD")

    if not sender_password:
        print("EMAIL_PASSWORD not set")
        return

    subject = "Payment Verified - College Tour"

    body = f"""
Hello {name},

Your payment of ₹{amount} has been successfully verified.

Thank you,
College Tour Team
"""

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Email Error:", e)


# =========================
# ROUTES
# =========================

@app.route("/")
def home():
    return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    name = request.form["name"]
    members = get_all_members()

    for m in members:
        if m["Name"] == name:
            session["user"] = name
            return redirect(url_for("dashboard"))

    return "User not found."


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))

    name = session["user"]
    members = get_all_members()

    for m in members:
        if m["Name"] == name:
            return render_template("dashboard.html", user=m)

    return "User not found."


@app.route("/submit_payment", methods=["POST"])
def submit_payment():
    if "user" not in session:
        return redirect(url_for("home"))

    name = session["user"]
    reference = request.form["reference"]
    amount_paid = float(request.form["amount"])
    file = request.files["screenshot"]

    members = get_all_members()

    for index, m in enumerate(members, start=2):
        if m["Name"] == name:

            total = float(m["Total Amount"] or 0)
            previous_paid = float(m["Paid Amount"] or 0)

            new_paid = previous_paid + amount_paid
            balance = total - new_paid

            filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)

            updated_row = [
                name,
                m["Email"],
                total,
                new_paid,
                balance,
                "Submitted",
                reference,
                filename,
                m.get("Invoice", ""),
                datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                m.get("Verified At", ""),
                m.get("Bill No", "")
            ]

            update_member_row(index, updated_row)
            break

    return redirect(url_for("dashboard"))


@app.route("/admin")
def admin():
    return render_template("admin_login.html")


@app.route("/admin_login", methods=["POST"])
def admin_login():
    if request.form["password"] == ADMIN_PASSWORD:
        session["admin"] = True
        return redirect(url_for("admin_dashboard"))
    return "Wrong password."


@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin"))

    members = get_all_members()
    return render_template("admin_dashboard.html", members=members)


@app.route("/verify/<name>")
def verify(name):
    if "admin" not in session:
        return redirect(url_for("admin"))

    members = get_all_members()

    for index, m in enumerate(members, start=2):
        if m["Name"] == name:

            total = float(m["Total Amount"] or 0)
            paid = float(m["Paid Amount"] or 0)
            balance = float(m["Balance"] or 0)

            verified_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
            bill_no = "CT-" + datetime.now().strftime("%Y%m%d%H%M%S")

            status = "Verified" if balance <= 0 else "Partially Paid"

            invoice_path = create_invoice(
                name=name,
                installment=paid,
                total_paid=paid,
                total_amount=total,
                balance=balance,
                reference=m["Reference"],
                bill_no=bill_no,
                submitted_at=m.get("Submitted At", ""),
                verified_at=verified_time
            )

            updated_row = [
                name,
                m["Email"],
                total,
                paid,
                balance,
                status,
                m["Reference"],
                m["Screenshot"],
                invoice_path,
                m.get("Submitted At", ""),
                verified_time,
                bill_no
            ]

            update_member_row(index, updated_row)
            send_payment_email(m["Email"], name, paid)
            break

    return redirect(url_for("admin_dashboard"))


@app.route("/download_invoice")
def download_invoice():
    if "user" not in session:
        return redirect(url_for("home"))

    name = session["user"]
    members = get_all_members()

    for m in members:
        if m["Name"] == name:
            invoice = m.get("Invoice", "")
            if invoice and os.path.exists(invoice):
                return send_file(invoice, as_attachment=True)

    return "Invoice not available."


@app.route("/add_member", methods=["POST"])
def add_member():
    if "admin" not in session:
        return redirect(url_for("admin"))

    name = request.form["name"]
    email = request.form["email"]
    total = float(request.form["amount"])

    add_new_member([
        name,
        email,
        total,
        0,
        total,
        "Pending",
        "",
        "",
        "",
        "",
        "",
        ""
    ])

    return redirect(url_for("admin_dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)