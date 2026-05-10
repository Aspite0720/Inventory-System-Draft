# inventory.py — Sari-Sari Store Inventory System

from db_connection import get_connection

# Shared SELECT columns reused in every read query
_SELECT = """
    SELECT productID, productName, category, productQty,
           price, supplier, date_added, date_updated
    FROM products
"""

def _run(sql, params=(), fetch=False):
    """
    Single reusable DB helper.
    - fetch=True  → returns rows (SELECT)
    - fetch=False → commits and returns True/False (INSERT/UPDATE/DELETE)
    """
    try:
        conn   = get_connection()
        cursor = conn.cursor()
        cursor.execute(sql, params)
        result = cursor.fetchall() if fetch else None
        if not fetch:
            conn.commit()
        cursor.close()
        conn.close()
        return result if fetch else True
    except Exception as e:
        print(f"❌ DB error: {e}")
        return [] if fetch else False


# ── CRUD ──────────────────────────────────────────────────────────────────────

def add_product(name, category, qty, price, supplier):
    return _run(
        "INSERT INTO products (productName, category, productQty, price, supplier) VALUES (%s,%s,%s,%s,%s)",
        (name, category, qty, price, supplier)
    )

def get_all_products():
    return _run(_SELECT + "ORDER BY category ASC, productName ASC", fetch=True)

def search_product(keyword):
    return _run(_SELECT + "WHERE productName LIKE %s ORDER BY category, productName",
                (f"%{keyword}%",), fetch=True)

def search_by_category(category):
    return _run(_SELECT + "WHERE category = %s ORDER BY productName",
                (category,), fetch=True)

def update_product(pid, name, category, qty, price, supplier):
    return _run(
        "UPDATE products SET productName=%s, category=%s, productQty=%s, price=%s, supplier=%s WHERE productID=%s",
        (name, category, qty, price, supplier, pid)
    )

def delete_product(pid):
    return _run("DELETE FROM products WHERE productID=%s", (pid,))
