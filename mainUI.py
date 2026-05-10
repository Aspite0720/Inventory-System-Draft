# mainUI.py — Angel's Store Inventory System (Shortened)

import tkinter as tk
from tkinter import ttk, messagebox
from inventory import (add_product, get_all_products, search_product,
                       search_by_category, update_product, delete_product)

CATEGORIES = [
    "Snacks", "Beverages", "Rice & Grains", "Canned Goods",
    "Condiments", "Personal Care", "Household", "Dairy", "Frozen Goods", "Others"
]
CATEGORY_COLORS = {
    "Beverages": "#dbeafe", "Snacks": "#fef9c3", "Rice & Grains": "#dcfce7",
    "Canned Goods": "#ffe4e6", "Condiments": "#fce7f3", "Personal Care": "#ede9fe",
    "Household": "#ffedd5", "Dairy": "#cffafe", "Frozen Goods": "#e0f2fe", "Others": "#f3f4f6"
}


class InventoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🛒 Angel's Store Inventory System")
        self.root.geometry("1100x650")
        self.root.configure(bg="#f0f4f8")
        self.selected_id = None
        self.undo_stack  = []
        self.redo_stack  = []
        self.build_ui()
        self.load_products()

    # ── UI BUILDER ────────────────────────────────────────────────────────────

    def build_ui(self):
        tk.Label(self.root, text="🛒 Angel's Store Inventory",
                 font=("Arial", 18, "bold"), bg="#f0f4f8", fg="#2d3748").pack(pady=10)
        self._build_form()
        self._build_buttons()
        self._build_search()
        self._build_table()

    def _build_form(self):
        frame = tk.Frame(self.root, bg="#ffffff", relief="groove", bd=2)
        frame.pack(padx=20, pady=5, fill="x")
        self.entries = {}

        fields = ["Product Name", "Category", "Quantity", "Price (₱)", "Supplier"]
        for i, label in enumerate(fields):
            tk.Label(frame, text=label, bg="#ffffff",
                     font=("Arial", 10)).grid(row=0, column=i*2, padx=10, pady=10, sticky="e")
            if label == "Category":
                w = ttk.Combobox(frame, values=CATEGORIES, width=13,
                                 font=("Arial", 10), state="readonly")
                w.set("Snacks")
            else:
                w = tk.Entry(frame, width=15, font=("Arial", 10))
            w.grid(row=0, column=i*2+1, padx=5, pady=10)
            self.entries[label] = w

    def _build_buttons(self):
        frame = tk.Frame(self.root, bg="#f0f4f8")
        frame.pack(pady=5)

        # (label, color, handler)
        btns = [
            ("➕ Add",    "#38a169", self.handle_add),
            ("💾 Update", "#3182ce", self.handle_update),
            ("🗑️ Delete", "#e53e3e", self.handle_delete),
            ("🔄 Clear",  "#718096", self.clear_fields),
            ("↩ Undo",   "#b7791f", self.handle_undo),
            ("↪ Redo",   "#2c7a7b", self.handle_redo),
        ]
        for text, color, cmd in btns:
            tk.Button(frame, text=text, bg=color, fg="white",
                      font=("Arial", 10, "bold"), width=10,
                      command=cmd).pack(side="left", padx=5)

    def _build_search(self):
        frame = tk.Frame(self.root, bg="#f0f4f8")
        frame.pack(pady=5)

        # Name search
        tk.Label(frame, text="🔍 Name:", bg="#f0f4f8", font=("Arial", 10)).pack(side="left")
        self.search_entry = tk.Entry(frame, width=18, font=("Arial", 10))
        self.search_entry.pack(side="left", padx=4)
        tk.Button(frame, text="Search", bg="#805ad5", fg="white",
                  font=("Arial", 10), command=self.handle_search).pack(side="left", padx=3)

        # Category filter
        tk.Label(frame, text="  |  Category:", bg="#f0f4f8",
                 font=("Arial", 10)).pack(side="left")
        self.search_category = ttk.Combobox(frame, values=["All"] + CATEGORIES,
                                            width=14, font=("Arial", 10), state="readonly")
        self.search_category.set("All")
        self.search_category.pack(side="left", padx=4)
        tk.Button(frame, text="Filter", bg="#dd6b20", fg="white",
                  font=("Arial", 10), command=self.handle_category_filter).pack(side="left", padx=3)

        tk.Button(frame, text="Show All", bg="#4a5568", fg="white",
                  font=("Arial", 10), command=self.load_products).pack(side="left", padx=3)

    def _build_table(self):
        frame = tk.Frame(self.root)
        frame.pack(padx=20, pady=10, fill="both", expand=True)

        cols   = ("No.", "Name", "Category", "Qty", "Price", "Supplier", "Date Added", "Last Updated")
        widths = (40, 140, 110, 55, 80, 120, 145, 145)

        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=15)
        for col, w in zip(cols, widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=w, anchor="center")

        for cat, color in CATEGORY_COLORS.items():
            self.tree.tag_configure(cat, background=color)

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

    # ── HELPERS ───────────────────────────────────────────────────────────────

    def _populate(self, products):
        """Insert a list of DB rows into the Treeview with formatting."""
        self.clear_table()
        for n, p in enumerate(products, 1):
            da = p[6].strftime("%b %d, %Y %I:%M %p") if p[6] else "—"
            du = p[7].strftime("%b %d, %Y %I:%M %p") if p[7] else "—"
            self.tree.insert("", "end",
                             values=(n, p[1], p[2], p[3], f"₱{p[4]:,.2f}", p[5], da, du),
                             tags=(str(p[0]), p[2]))   # real productID + category in tags

    def get_form_data(self):
        """Read, validate, and return form fields as a tuple, or None on error."""
        name     = self.entries["Product Name"].get().strip()
        category = self.entries["Category"].get().strip()
        qty      = self.entries["Quantity"].get().strip()
        price    = self.entries["Price (₱)"].get().strip()
        supplier = self.entries["Supplier"].get().strip()

        if not name or not qty or not price:
            messagebox.showwarning("Incomplete", "Name, Quantity, and Price are required.")
            return None
        try:
            qty, price = int(qty), float(price)
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a whole number. Price must be a number.")
            return None
        if qty < 0 or price < 0:
            messagebox.showerror("Invalid", "Quantity and Price cannot be negative.")
            return None

        return name, category, qty, price, supplier

    def clear_table(self):
        self.tree.delete(*self.tree.get_children())

    def clear_fields(self):
        for key, w in self.entries.items():
            w.set("Snacks") if isinstance(w, ttk.Combobox) else w.delete(0, tk.END)
        self.search_entry.delete(0, tk.END)
        self.search_category.set("All")
        self.selected_id = None
        self.tree.selection_remove(self.tree.selection())

    def _get_selected_product(self):
        """Return the full DB row for the currently selected product, or None."""
        return next((p for p in get_all_products()
                     if str(p[0]) == str(self.selected_id)), None)

    # ── EVENT HANDLERS ────────────────────────────────────────────────────────

    def load_products(self):
        self._populate(get_all_products())

    def on_row_select(self, event):
        sel = self.tree.focus()
        if not sel:
            return
        tags = self.tree.item(sel, "tags")
        if tags:
            self.selected_id = tags[0]           # Real productID from tags
        vals = self.tree.item(sel, "values")
        if not vals:
            return
        for key, val in zip(
                ["Product Name", "Category", "Quantity", "Price (₱)", "Supplier"],
                [vals[1], vals[2], vals[3],
                 str(vals[4]).replace("₱", "").replace(",", ""), vals[5]]
        ):
            w = self.entries[key]
            w.set(val) if isinstance(w, ttk.Combobox) else (w.delete(0, tk.END) or w.insert(0, val))

    def handle_add(self):
        data = self.get_form_data()
        if not data:
            return
        if add_product(*data):
            self.undo_stack.append({"action": "add", "data": data})
            self.redo_stack.clear()
            self.load_products()
            self.clear_fields()
            messagebox.showinfo("Success", "Product added! ✅")
        else:
            messagebox.showerror("Error", "Failed to add product.")

    def handle_update(self):
        if not self.selected_id:
            messagebox.showwarning("Warning", "Select a product row first.")
            return
        data = self.get_form_data()
        if not data:
            return
        old = self._get_selected_product()
        if update_product(self.selected_id, *data):
            if old:
                self.undo_stack.append({
                    "action": "update", "id": self.selected_id,
                    "old": old[1:6], "new": data
                })
            self.redo_stack.clear()
            self.load_products()
            self.clear_fields()
            messagebox.showinfo("Success", "Product updated! ✅")
        else:
            messagebox.showerror("Error", "Failed to update product.")

    def handle_delete(self):
        if not self.selected_id:
            messagebox.showwarning("Warning", "Select a product row first.")
            return
        target = self._get_selected_product()
        if not messagebox.askyesno("Confirm", f"Delete '{target[1] if target else 'this product'}'?"):
            return
        if delete_product(self.selected_id):
            if target:
                self.undo_stack.append({"action": "delete", "data": target[1:6]})
            self.redo_stack.clear()
            self.load_products()
            self.clear_fields()
            messagebox.showinfo("Deleted", "Product deleted! 🗑️")
        else:
            messagebox.showerror("Error", "Failed to delete product.")

    def handle_search(self):
        kw = self.search_entry.get().strip()
        if not kw:
            messagebox.showwarning("Warning", "Enter a search keyword.")
            return
        results = search_product(kw)
        self._populate(results) if results else messagebox.showinfo("No Results", f"No products found for '{kw}'.")

    def handle_category_filter(self):
        cat = self.search_category.get()
        results = get_all_products() if cat == "All" else search_by_category(cat)
        self._populate(results) if results else messagebox.showinfo("No Results", f"No products in '{cat}'.")

    # ── UNDO / REDO ───────────────────────────────────────────────────────────

    def _apply_history(self, source, dest, label):
        """Shared logic for both undo and redo to avoid repetition."""
        if not source:
            messagebox.showinfo(label, f"Nothing to {label.lower()}.")
            return
        entry = source.pop()
        act   = entry["action"]

        if act == "add":
            # Undo add = delete last added; Redo add = re-add
            if label == "Undo":
                last = get_all_products()
                if last:
                    delete_product(last[-1][0])
            else:
                add_product(*entry["data"])
            dest.append({"action": "add", "data": entry["data"]})

        elif act == "delete":
            # Undo delete = re-add; Redo delete = delete again
            if label == "Undo":
                add_product(*entry["data"])
            else:
                p = next((x for x in get_all_products() if x[1] == entry["data"][0]), None)
                if p:
                    delete_product(p[0])
            dest.append({"action": "delete", "data": entry["data"]})

        elif act == "update":
            # Swap old and new for undo/redo
            revert = entry["old"] if label == "Undo" else entry["new"]
            update_product(entry["id"], *revert)
            dest.append({"action": "update", "id": entry["id"],
                         "old": entry["new"], "new": entry["old"]})

        self.load_products()
        self.clear_fields()
        icon = "↩" if label == "Undo" else "↪"
        messagebox.showinfo(label, f"Action {label.lower()}ne! {icon}")

    def handle_undo(self):
        self._apply_history(self.undo_stack, self.redo_stack, "Undo")

    def handle_redo(self):
        self._apply_history(self.redo_stack, self.undo_stack, "Redo")


# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    InventoryApp(root)
    root.mainloop()
