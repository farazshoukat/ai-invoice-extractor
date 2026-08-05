"""Flask API for the Invoice Extractor — upload, extract, and log to Google Sheets + Postgres."""

import os
from flask import Flask, request, jsonify
from flask_cors import CORS

from extractor import extract_structured_data
from sheets import save_invoice as save_to_sheets
from db import save_invoice as save_to_db
from dashboard import dashboard

app = Flask(__name__)
CORS(app)
app.register_blueprint(dashboard)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.route("/extract", methods=["POST"])
def extract():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    file.save(file_path)

    try:
        data = extract_structured_data(file_path)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Extraction failed: {exc}"}), 500

    # Save to Postgres (Supabase) — primary store for dashboard
    try:
        save_to_db(data)
    except Exception as exc:  # noqa: BLE001
        return jsonify({"error": f"Extraction succeeded but saving to database failed: {exc}", "data": data}), 500

    # Save to Google Sheets — kept as secondary/backup log
    try:
        save_to_sheets(data)
    except Exception as exc:  # noqa: BLE001
        print(f"Sheets write failed (non-fatal): {exc}")

    return jsonify({"status": "saved", "data": data})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)