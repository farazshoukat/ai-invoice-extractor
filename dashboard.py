from flask import Blueprint, render_template, request, session, redirect, url_for
from db import get_conn

dashboard = Blueprint("dashboard", __name__)

@dashboard.route("/dashboard")
def view_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_conn()
    cur = conn.cursor()

    search = request.args.get("q", "")
    cur.execute("""
        SELECT id, vendor, invoice_date, amount, items FROM invoices
        WHERE user_id = %s AND vendor ILIKE %s
        ORDER BY invoice_date DESC
        LIMIT 100
    """, (user_id, f"%{search}%"))
    rows = cur.fetchall()

    cur.execute("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM invoices WHERE user_id = %s", (user_id,))
    total_count, total_amount = cur.fetchone()

    cur.execute("""
        SELECT vendor, COUNT(*) FROM invoices
        WHERE user_id = %s
        GROUP BY vendor ORDER BY COUNT(*) DESC LIMIT 5
    """, (user_id,))
    top_vendors = cur.fetchall()

    cur.close()
    conn.close()
    return render_template("dashboard.html",
        invoices=rows, total_count=total_count,
        total_amount=total_amount, top_vendors=top_vendors,
        email=session.get("email"))


@dashboard.route("/invoice/<int:invoice_id>/delete", methods=["POST"])
def delete_invoice(invoice_id):
    if "user_id" not in session:
        return redirect(url_for("login"))
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM invoices WHERE id = %s AND user_id = %s", (invoice_id, session["user_id"]))
    conn.commit()
    cur.close()
    conn.close()
    return redirect(url_for("dashboard.view_dashboard"))