# inventory.py — Angel's Store

from db_connection import get_connection

_SEL = """SELECT productID, productName, category, productQty,
                 price, supplier, low_stock_alert, date_added, date_updated
          FROM products """


def _run(sql, params=(), fetch=False):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(sql, params)
        result = cur.fetchall() if fetch else True
        if not fetch: conn.commit()
        cur.close();
        conn.close()
        return result
    except Exception as e:
        print(f"❌ DB error: {e}")
        return [] if fetch else False


# ── PRODUCTS ──────────────────────────────────────────────────────────────────

def add_product(name, category, qty, price, supplier, alert=5):
    return _run(
        "INSERT INTO products (productName,category,productQty,price,supplier,low_stock_alert) VALUES (%s,%s,%s,%s,%s,%s)",
        (name, category, qty, price, supplier, alert)
    )


def get_all_products():
    return _run(_SEL + "ORDER BY category, productName", fetch=True)


def get_by_id(pid):
    rows = _run(_SEL + "WHERE productID=%s", (pid,), fetch=True)
    return rows[0] if rows else None


def search_product(keyword):
    return _run(_SEL + "WHERE productName LIKE %s ORDER BY category, productName",
                (f"%{keyword}%",), fetch=True)


def search_by_category(cat):
    return _run(_SEL + "WHERE category=%s ORDER BY productName", (cat,), fetch=True)


def update_product(pid, name, category, qty, price, supplier, alert=5):
    return _run(
        "UPDATE products SET productName=%s,category=%s,productQty=%s,price=%s,supplier=%s,low_stock_alert=%s WHERE productID=%s",
        (name, category, qty, price, supplier, alert, pid)
    )


def delete_product(pid):
    return _run("DELETE FROM products WHERE productID=%s", (pid,))


def get_old_price(pid):
    rows = _run("SELECT price FROM products WHERE productID=%s", (pid,), fetch=True)
    return float(rows[0][0]) if rows else None


# ── SALES ─────────────────────────────────────────────────────────────────────

def record_sale(pid, name, category, qty, price):
    """Check stock → insert sale → reduce stock. Returns (True, id) or (False, msg)."""
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT productQty FROM products WHERE productID=%s", (pid,))
        row = cur.fetchone()
        if not row or row[0] < qty:
            cur.close();
            conn.close()
            return False, f"Not enough stock. Only {row[0] if row else 0} left."
        cur.execute(
            "INSERT INTO sales (productID,productName,category,qty_sold,unit_price,subtotal) VALUES (%s,%s,%s,%s,%s,%s)",
            (pid, name, category, qty, price, qty * price)
        )
        sid = cur.lastrowid
        cur.execute("UPDATE products SET productQty=productQty-%s WHERE productID=%s", (qty, pid))
        conn.commit()
        cur.close();
        conn.close()
        return True, sid
    except Exception as e:
        print(f"❌ Sale error: {e}")
        return False, str(e)


# ── REPORT ────────────────────────────────────────────────────────────────────

def get_all_sales():
    return _run(
        "SELECT saleID,date_sold,productName,category,qty_sold,unit_price,subtotal FROM sales ORDER BY date_sold DESC",
        fetch=True
    )


def get_summary():
    return _run("SELECT COUNT(*), IFNULL(SUM(subtotal),0) FROM sales", fetch=True)


def get_daily_sales(days=7):
    return _run(
        """SELECT DATE(date_sold), COUNT(*), SUM(subtotal) FROM sales
           WHERE date_sold >= DATE_SUB(CURDATE(), INTERVAL %s DAY)
           GROUP BY DATE(date_sold) ORDER BY DATE(date_sold) DESC""",
        (days,), fetch=True
    )


def get_best_sellers():
    return _run(
        "SELECT productName, category, SUM(qty_sold), SUM(subtotal) FROM sales GROUP BY productName,category ORDER BY SUM(qty_sold) DESC LIMIT 10",
        fetch=True
    )


def get_low_stock():
    return _run(
        "SELECT productName, category, productQty, low_stock_alert FROM products WHERE productQty <= low_stock_alert ORDER BY productQty",
        fetch=True
    )
