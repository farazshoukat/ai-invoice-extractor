import psycopg2
import os
from datetime import datetime

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def format_items(items: list) -> str:
    if not items:
        return ""
    lines = []
    for item in items:
        desc = item.get("description", "").strip()
        amount = item.get("amount")
        if amount is not None:
            lines.append(f"{desc} - ${amount}")
        else:
            lines.append(desc)
    return "; ".join(lines)

def parse_date(date_str):
    """Try common date formats; return None if unparseable."""
    if not date_str:
        return None
    formats = ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y", "%B %d, %Y", "%d %B %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None

def save_invoice(data: dict, company_id: str = None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO invoices (vendor, invoice_date, amount, items, raw_text, file_url, company_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """, (
        data.get("vendor"),
        parse_date(data.get("date")),
        data.get("total_amount"),
        format_items(data.get("items", [])),
        data.get("ocr_text_preview"),
        None,
        company_id
    ))
    conn.commit()
    cur.close()
    conn.close()