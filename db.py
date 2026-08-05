import psycopg2
import os

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def format_items(items: list) -> str:
    """Convert items list into a readable, comma-separated string."""
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

def save_invoice(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO invoices (vendor, invoice_date, amount, items, raw_text, file_url)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (
        data.get("vendor"),
        data.get("date"),
        data.get("total_amount"),
        format_items(data.get("items", [])),
        data.get("ocr_text_preview"),
        None
    ))
    conn.commit()
    cur.close()
    conn.close()