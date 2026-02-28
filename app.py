from flask import Flask, render_template, request, redirect, url_for, session, send_file
import os
from datetime import datetime
from generate_invoice import create_invoice
from sheets_db import get_all_members, update_member_row
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "static/uploads"
INVOICE_FOLDER = "invoices"
ADMIN_PASSWORD = "jerald@70928"

# =============================
# EMAIL FUNCTION
# =============================
def send_payment_email(to_email, name, amount):
    sender_email = "gjerald121@gmail.com"
    sender_password = "vdypgrbdvsbrnlur"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = to_email
    msg["Subject"] = "Payment Verified - College Tour"

    body = f"""
Hello {name},

Your payment of ₹{amount} has been successfully verified.

Thank you,
College Tour Team
"""

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print("Email Error:", e)

# =============================
# HOME
# =============================
@app.route("/")
def home():
    return render_template("login.html")

# =============================
# MEMBER LOGIN
# =============================
@app.route("/login", methods=["POST"])
def login():
    name = request.form["name"]
    members = get_all_members()

    for m in members:
        if m["Name"] == name:
            session["user"] = name
            return redirect(url_for("dashboard"))

    return "User not found."

# =============================
# MEMBER DASHBOARD
# =============================
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))

    name = session["user"]
    members = get_all_members()

    for m in members:
        if m["Name"] == name:
            total = float(m.get("Total Amount") or 0)
            paid = float(m.get("Paid Amount") or 0)
            balance = total - paid

            m["Total Amount"] = total
            m["Paid Amount"] = paid
            m["Balance"] = balance

            return render_template("dashboard.html", user=m)

    return "User not found."

# =============================
# SUBMIT PAYMENT (PARTIAL)
# =============================
@app.route("/submit_payment", methods=["POST"])
def submit_payment():
    if "user" not in session:
        return redirect(url_for("home"))

    name = session["user"]
    amount_paid = float(request.form["amount"])
    reference = request.form["reference"]
    file = request.files["screenshot"]

    if not file:
        return "Screenshot required"

    filename = f"{name}_{datetime.now().strftime('%Y%m%d%H%M%S')}.png"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    file.save(filepath)

    members = get_all_members()

    for index, m in enumerate(members):
        if m["Name"] == name:

            total = float(m.get("Total Amount") or 0)
            previous_paid = float(m.get("Paid Amount") or 0)

            new_paid = previous_paid + amount_paid
            balance = total - new_paid

            status = "Submitted"
            if balance <= 0:
                status = "Submitted"

            update_member_row(index, {
                "Paid Amount": new_paid,
                "Reference": reference,
                "Screenshot": filename,
                "Submitted At": datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
                "Status": status
            })

            break

    return redirect(url_for("dashboard"))

# =============================
# ADMIN LOGIN
# =============================
@app.route("/admin")
def admin():
    return render_template("admin_login.html")

@app.route("/admin_login", methods=["POST"])
def admin_login():
    if request.form["password"] == ADMIN_PASSWORD:
        session["admin"] = True
        return redirect(url_for("admin_dashboard"))
    return "Wrong password."

# =============================
# ADMIN DASHBOARD
# =============================
@app.route("/admin/dashboard")
def admin_dashboard():
    if "admin" not in session:
        return redirect(url_for("admin"))

    members = get_all_members()
    return render_template("admin_dashboard.html", members=members)

# =============================
# VERIFY PAYMENT
# =============================
@app.route("/verify/<name>")
def verify(name):
    if "admin" not in session:
        return redirect(url_for("admin"))

    members = get_all_members()

    for index, m in enumerate(members):
        if m["Name"] == name:

            total = float(m.get("Total Amount") or 0)
            paid = float(m.get("Paid Amount") or 0)
            balance = total - paid

            bill_no = "CT-" + datetime.now().strftime("%Y%m%d%H%M%S")
            verified_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

            status = "Verified"
            if balance > 0:
                status = "Partially Paid"

            invoice_path = create_invoice(
                name=name,
                installment=paid,
                total_paid=paid,
                total_amount=total,
                balance=balance,
                reference=m.get("Reference"),
                bill_no=bill_no,
                submitted_at=m.get("Submitted At"),
                verified_at=verified_time
            )

            update_member_row(index, {
                "Status": status,
                "Verified At": verified_time,
                "Bill No": bill_no,
                "Invoice": invoice_path
            })

            if m.get("Email"):
                send_payment_email(m["Email"], name, paid)

            break

    return redirect(url_for("admin_dashboard"))

# =============================
# DOWNLOAD INVOICE
# =============================
@app.route("/download_invoice")
def download_invoice():
    if "user" not in session:
        return redirect(url_for("home"))

    name = session["user"]
    members = get_all_members()

    for m in members:
        if m["Name"] == name:
            invoice = m.get("Invoice")
            if invoice and os.path.exists(invoice):
                return send_file(invoice, as_attachment=True)
            return "Invoice not available."

    return "User not found."

# =============================
# LOGOUT
# =============================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

# =============================
# RUN
# =============================
if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(INVOICE_FOLDER, exist_ok=True)
    app.run(debug=True)