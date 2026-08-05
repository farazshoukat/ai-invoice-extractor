"""Flask API for the Invoice Extractor — upload, extract, log to Sheets + Postgres, with auth."""

import os
from functools import wraps
from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS

from extractor import extract_structured_data
from sheets import save_invoice as save_to_sheets
from db import save_invoice as save_to_db
from dashboard import dashboard
from auth import sign_up, sign_in, sign_out

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]
CORS(app)
app.register_blueprint(dashboard)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapper


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "GET":
        return render_template("signup.html")

    email = request.form["email"]
    password = request.form["password"]

    try:
        result = sign_up(email, password)
        session["user_id"] = result.user.id
        session["email"] = email
        return redirect(url_for("dashboard.view_dashboard"))
    except Exception as exc:
        return render_template("signup.html", error=str(exc))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form["email"]
    password = request.form["password"]

    try:
        result = sign_in(email, password)
        session["user_id"] = result.user.id
        session["email"] = email
        return redirect(url_for("dashboard.view_dashboard"))
    except Exception as exc:
        return render_template("login.html", error=str(exc))


@app.route("/logout")
def logout():
    sign_out()
    session.clear()
    return redirect(url_for("login"))


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "GET":
        return render_template("upload.html")

    if "file" not in request.files or request.files["file"].filename == "":
        return render_template("upload.html", error="Please choose a file")

    file = request.files["file"]
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(file_path)

    try:
        data = extract_structured_data(file_path)
    except Exception as exc:
        return render_template("upload.html", error=f"Extraction failed: {exc}")

    try:
        save_to_db(data)
    except Exception as exc:
        return render_template("upload.html", error=f"Database save failed: {exc}")

    try:
        save_to_sheets(data)
    except Exception as exc:
        print(f"Sheets write failed (non-fatal): {exc}")

    return redirect(url_for("dashboard.view_dashboard"))


@app.route("/extract", methods=["POST"])
@login_required
def extract():
    """JSON API endpoint (kept for programmatic/API use, separate from /upload form)."""
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(file_path)

    try:
        data = extract_structured_data(file_path)
    except Exception as exc:
        return jsonify({"error": f"Extraction failed: {exc}"}), 500

    try:
        save_to_db(data)
    except Exception as exc:
        return jsonify({"error": f"Extraction succeeded but saving to database failed: {exc}", "data": data}), 500

    try:
        save_to_sheets(data)
    except Exception as exc:
        print(f"Sheets write failed (non-fatal): {exc}")

    return jsonify({"status": "saved", "data": data})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard.view_dashboard"))
    return redirect(url_for("login"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)