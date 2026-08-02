"""Google Sheets integration — saves extracted invoice data via OAuth."""

import base64
import gspread
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os

from config import GOOGLE_SHEET_ID, OAUTH_CLIENT_SECRET_FILE, OAUTH_TOKEN_FILE

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS = ["Vendor", "Date", "Total Amount", "Currency", "Item Description", "Item Amount"]


def ensure_token_file():
    """On Railway, recreate token.json from a base64 env var if it doesn't exist locally."""
    if os.path.exists(OAUTH_TOKEN_FILE):
        return

    token_b64 = os.environ.get("GOOGLE_TOKEN_B64")
    if token_b64:
        os.makedirs(os.path.dirname(OAUTH_TOKEN_FILE), exist_ok=True)
        with open(OAUTH_TOKEN_FILE, "wb") as f:
            f.write(base64.b64decode(token_b64))


def get_credentials():
    ensure_token_file()
    creds = None
    if os.path.exists(OAUTH_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(OAUTH_TOKEN_FILE, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(OAUTH_CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0)

        with open(OAUTH_TOKEN_FILE, "w") as token_file:
            token_file.write(creds.to_json())

    return creds


def get_sheet():
    creds = get_credentials()
    client = gspread.authorize(creds)
    sheet = client.open_by_key(GOOGLE_SHEET_ID).sheet1

    first_row = sheet.row_values(1)
    if first_row != HEADERS:
        sheet.update("A1:F1", [HEADERS])
        sheet.format("A1:F1", {"textFormat": {"bold": True}})

    return sheet


def save_invoice(data: dict):
    sheet = get_sheet()

    vendor = data.get("vendor") or ""
    date = data.get("date") or ""
    total = data.get("total_amount") or ""
    currency = data.get("currency") or ""
    items = data.get("items", [])

    if not items:
        sheet.append_row([vendor, date, total, currency, "", ""])
        return

    rows = []
    for item in items:
        rows.append([
            vendor,
            date,
            total,
            currency,
            item.get("description", ""),
            item.get("amount", ""),
        ])
    sheet.append_rows(rows)