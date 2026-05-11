# mainUI.py — Angel's Store Inventory System

import tkinter as tk
from tkinter import ttk, messagebox
from inventory import (
    add_product, get_all_products, get_by_id, search_product, search_by_category,
    update_product, delete_product, get_old_price,
    record_sale, get_all_sales, get_summary, get_daily_sales, get_best_sellers, get_low_stock
)

CATEGORIES = ["Snacks","Beverages","Rice & Grains","Canned Goods","Condiments",
               "Personal Care","Household","Dairy","Frozen Goods","Others"]

CAT_COLORS = {
    "Snacks":"#fef9c3",       "Beverages":"#dbeafe",  "Rice & Grains":"#dcfce7",
    "Canned Goods":"#ffe4e6", "Condiments":"#fce7f3", "Personal Care":"#ede9fe",
    "Household":"#ffedd5",    "Dairy":"#cffafe",       "Frozen Goods":"#e0f2fe",
    "Others":"#f3f4f6"
}


class App:
    def __init__(self, root):
        self.root      = root
        self.root.title("🛒 Angel's Store")
        self.root.geometry("1100x660")
        self.root.configure(bg="#f0f4f8")
        self.sel_id    = None
        self.sel_price = 0.0
        self.undo_stk  = []
        self.redo_stk  = []
        self._build()

    # ── TABS ──────────────────────────────────────────────────────────────────

    def _build(self):
        ttk.Style().configure("TNotebook.Tab", font=("Arial",11,"bold"), padding=(14,6))
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=10, pady=10)
        self.t_inv = tk.Frame(nb, bg="#f0f4f8")
        self.t_rep = tk.Frame(nb, bg="#f0f4f8")
        nb.add(self.t_inv, text="📦  Inventory")
        nb.add(self.t_rep, text="📊  Sales Report")
        nb.bind("<<NotebookTabChanged>>",
                lambda e: self._refresh_report() if nb.index(nb.select()) == 1 else None)
        self._build_inventory()
        self._build_report()

    # ── INVENTORY TAB ─────────────────────────────────────────────────────────

    def _build_inventory(self):
        tk.Label(self.t_inv, text="📦 Angel's Store — Inventory",
                 font=("Arial",15,"bold"), bg="#f0f4f8", fg="#2d3748").pack(pady=(8,4))

        # ── Form ──
        frm = tk.Frame(self.t_inv, bg="#fff", relief="groove", bd=2)
        frm.pack(padx=20, pady=4, fill="x")
        self.ent = {}
        for i, lbl in enumerate(["Product Name","Category","Quantity","Price (₱)","Supplier","Alert Qty"]):
            tk.Label(frm, text=lbl, bg="#fff", font=("Arial",9)).grid(row=0, column=i*2, padx=8, pady=8, sticky="e")
            if lbl == "Category":
                w = ttk.Combobox(frm, values=CATEGORIES, width=12, font=("Arial",10), state="readonly")
                w.set("Snacks")
            else:
                w = tk.Entry(frm, width=11, font=("Arial",10))
                if lbl == "Alert Qty": w.insert(0,"5")
            w.grid(row=0, column=i*2+1, padx=4, pady=8)
            self.ent[lbl] = w

        # ── Action buttons ──
        bf = tk.Frame(self.t_inv, bg="#f0f4f8")
        bf.pack(pady=3)
        for txt, col, cmd in [
            ("➕ Add","#38a169",self._add), ("💾 Update","#3182ce",self._update),
            ("🗑️ Delete","#e53e3e",self._delete), ("🔄 Clear","#718096",self._clear),
            ("↩ Undo","#b7791f",self._undo), ("↪ Redo","#2c7a7b",self._redo),
        ]:
            tk.Button(bf, text=txt, bg=col, fg="white", font=("Arial",10,"bold"),
                      width=10, command=cmd).pack(side="left", padx=4)

        # ── Sale bar ──
        sb = tk.Frame(self.t_inv, bg="#fff8e1", relief="groove", bd=2)
        sb.pack(padx=20, pady=3, fill="x")
        tk.Label(sb, text="💰 Record Sale:", bg="#fff8e1",
                 font=("Arial",10,"bold"), fg="#92400e").pack(side="left", padx=10, pady=5)
        tk.Label(sb, text="Selected:", bg="#fff8e1", font=("Arial",10)).pack(side="left")
        self.lbl_sel = tk.Label(sb, text="— none —", bg="#fff8e1",
                                font=("Arial",10,"italic"), fg="#4a5568", width=20, anchor="w")
        self.lbl_sel.pack(side="left", padx=4)
        tk.Label(sb, text="Qty:", bg="#fff8e1", font=("Arial",10)).pack(side="left", padx=(10,2))
        self.sale_qty = tk.Entry(sb, width=5, font=("Arial",10))
        self.sale_qty.insert(0,"1")
        self.sale_qty.pack(side="left", padx=3)
        tk.Button(sb, text="✅ Record Sale", bg="#d97706", fg="white",
                  font=("Arial",10,"bold"), command=self._record_sale).pack(side="left", padx=10)
        self.lbl_stock = tk.Label(sb, text="", bg="#fff8e1", font=("Arial",9), fg="#718096")
        self.lbl_stock.pack(side="left", padx=4)

        # ── Search bar ──
        sf = tk.Frame(self.t_inv, bg="#f0f4f8")
        sf.pack(pady=3)
        tk.Label(sf, text="🔍 Name:", bg="#f0f4f8", font=("Arial",10)).pack(side="left")
        self.s_name = tk.Entry(sf, width=16, font=("Arial",10))
        self.s_name.pack(side="left", padx=4)
        tk.Button(sf, text="Search", bg="#805ad5", fg="white",
                  font=("Arial",10), command=self._search).pack(side="left", padx=3)
        tk.Label(sf, text="  |  Category:", bg="#f0f4f8", font=("Arial",10)).pack(side="left")
        self.s_cat = ttk.Combobox(sf, values=["All"]+CATEGORIES,
                                  width=14, font=("Arial",10), state="readonly")
        self.s_cat.set("All")
        self.s_cat.pack(side="left", padx=4)
        tk.Button(sf, text="Filter", bg="#dd6b20", fg="white",
                  font=("Arial",10), command=self._filter).pack(side="left", padx=3)
        tk.Button(sf, text="Show All", bg="#4a5568", fg="white",
                  font=("Arial",10), command=self._load).pack(side="left", padx=3)

        # ── Table ──
        tf = tk.Frame(self.t_inv)
        tf.pack(padx=20, pady=4, fill="both", expand=True)
        cols   = ("No.","Name","Category","Stock","Price","Supplier","Alert","Date Added","Last Updated")
        widths = (35, 130, 105, 55, 80, 110, 45, 130, 130)
        self.tree = ttk.Treeview(tf, columns=cols, show="headings", height=11)
        for c, w in zip(cols, widths):
            self.tree.heading(c, text=c); self.tree.column(c, width=w, anchor="center")
        for cat, color in CAT_COLORS.items():
            self.tree.tag_configure(cat, background=color)
        self.tree.tag_configure("low", foreground="#c53030")
        sb2 = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=sb2.set)
        sb2.pack(side="right", fill="y"); self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self._load()

    # ── REPORT TAB ────────────────────────────────────────────────────────────

    def _build_report(self):
        hdr = tk.Frame(self.t_rep, bg="#f0f4f8")
        hdr.pack(fill="x", padx=20, pady=8)
        tk.Label(hdr, text="📊 Sales Report", font=("Arial",15,"bold"),
                 bg="#f0f4f8", fg="#2d3748").pack(side="left")
        tk.Button(hdr, text="🔄 Refresh", bg="#3182ce", fg="white",
                  font=("Arial",10,"bold"), command=self._refresh_report).pack(side="right")

        # Summary cards
        cf = tk.Frame(self.t_rep, bg="#f0f4f8")
        cf.pack(padx=20, pady=4, fill="x")
        self.c_sales = self._card(cf, "Total Sales",    "—", "#3182ce")
        self.c_rev   = self._card(cf, "Total Revenue",  "—", "#38a169")
        self.c_low   = self._card(cf, "Low Stock Items","—", "#e53e3e")

        # Sub-tabs
        nb = ttk.Notebook(self.t_rep)
        nb.pack(padx=20, pady=6, fill="both", expand=True)
        t1 = tk.Frame(nb, bg="#f0f4f8")
        t2 = tk.Frame(nb, bg="#f0f4f8")
        t3 = tk.Frame(nb, bg="#f0f4f8")
        nb.add(t1, text="📅 Daily Sales")
        nb.add(t2, text="🏆 Best Sellers")
        nb.add(t3, text="🧾 Sales Log")
        self.t_daily = self._table(t1, ("Date","Transactions","Revenue"),             (160,130,140))
        self.t_best  = self._table(t2, ("Product","Category","Qty Sold","Revenue"),   (190,120,100,110))
        self.t_log   = self._table(t3, ("ID","Date & Time","Product","Qty","Unit Price","Total"), (45,170,170,55,95,95))
        self._refresh_report()

    # ── SHARED HELPERS ────────────────────────────────────────────────────────

    def _table(self, parent, cols, widths):
        f = tk.Frame(parent)
        f.pack(fill="both", expand=True, padx=8, pady=6)
        t = ttk.Treeview(f, columns=cols, show="headings")
        for c, w in zip(cols, widths): t.heading(c, text=c); t.column(c, width=w, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=t.yview)
        t.configure(yscroll=sb.set)
        sb.pack(side="right", fill="y"); t.pack(fill="both", expand=True)
        return t

    def _card(self, parent, title, val, color):
        c = tk.Frame(parent, bg=color, relief="raised", bd=1)
        c.pack(side="left", padx=8, pady=4, ipadx=20, ipady=8, fill="x", expand=True)
        tk.Label(c, text=title, font=("Arial",9),  bg=color, fg="white").pack()
        lbl = tk.Label(c, text=val, font=("Arial",15,"bold"), bg=color, fg="white")
        lbl.pack()
        return lbl

    def _populate(self, rows):
        self.tree.delete(*self.tree.get_children())
        for n, p in enumerate(rows, 1):
            da   = p[7].strftime("%b %d, %Y %I:%M %p") if p[7] else "—"
            du   = p[8].strftime("%b %d, %Y %I:%M %p") if p[8] else "—"
            tags = [str(p[0]), p[2]] + (["low"] if p[3] <= p[6] else [])
            self.tree.insert("", "end",
                values=(n, p[1], p[2], p[3], f"₱{p[4]:,.2f}", p[5], p[6], da, du),
                tags=tuple(tags))

    def _form_data(self):
        v = {k: w.get().strip() for k, w in self.ent.items()}
        if not v["Product Name"] or not v["Quantity"] or not v["Price (₱)"]:
            messagebox.showwarning("Incomplete", "Name, Quantity, and Price are required.")
            return None
        try:
            qty   = int(v["Quantity"])
            price = float(v["Price (₱)"])
            alert = int(v["Alert Qty"] or 5)
            if qty < 0 or price < 0 or alert < 0: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid", "Quantity and Alert = whole numbers. Price = number. No negatives.")
            return None
        return v["Product Name"], v["Category"], qty, price, v["Supplier"], alert

    def _clear(self):
        for k, w in self.ent.items():
            w.set("Snacks") if isinstance(w, ttk.Combobox) else w.delete(0, tk.END)
        self.ent["Alert Qty"].insert(0,"5")
        self.s_name.delete(0, tk.END); self.s_cat.set("All")
        self.sel_id = None; self.sel_price = 0.0
        self.lbl_sel.config(text="— none —"); self.lbl_stock.config(text="")
        self.tree.selection_remove(self.tree.selection())

    def _on_select(self, _=None):
        sel = self.tree.focus()
        if not sel: return
        tags = self.tree.item(sel, "tags")
        vals = self.tree.item(sel, "values")
        if not tags or not vals: return
        self.sel_id = tags[0]
        raw = str(vals[4]).replace("₱","").replace(",","")
        self.sel_price = float(raw)
        for key, val in zip(
            ["Product Name","Category","Quantity","Price (₱)","Supplier","Alert Qty"],
            [vals[1], vals[2], vals[3], raw, vals[5], vals[6]]
        ):
            w = self.ent[key]
            w.set(val) if isinstance(w, ttk.Combobox) else (w.delete(0,tk.END) or w.insert(0,val))
        self.lbl_sel.config(text=vals[1])
        self.lbl_stock.config(text=f"(Stock: {vals[3]})")

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def _load(self): self._populate(get_all_products())

    def _add(self):
        data = self._form_data()
        if not data: return
        if add_product(*data):
            self.undo_stk.append({"a":"add","d":data}); self.redo_stk.clear()
            self._load(); self._clear()
            messagebox.showinfo("Success","Product added! ✅")
        else:
            messagebox.showerror("Error","Failed to add product.")

    def _update(self):
        if not self.sel_id:
            messagebox.showwarning("Warning","Select a product first."); return
        data = self._form_data()
        if not data: return
        old_p = get_old_price(self.sel_id)
        if old_p and abs(data[3] - old_p) > 0.001:
            if not messagebox.askyesno("Price Changed!",
                f"Old: ₱{old_p:,.2f}  →  New: ₱{data[3]:,.2f}\n\nIs this correct?"): return
        old = get_by_id(self.sel_id)
        if update_product(self.sel_id, *data):
            if old: self.undo_stk.append({"a":"update","id":self.sel_id,"old":old[1:7],"new":data})
            self.redo_stk.clear(); self._load(); self._clear()
            messagebox.showinfo("Success","Product updated! ✅")
        else:
            messagebox.showerror("Error","Failed to update.")

    def _delete(self):
        if not self.sel_id:
            messagebox.showwarning("Warning","Select a product first."); return
        p = get_by_id(self.sel_id)
        if not messagebox.askyesno("Confirm Delete", f"Delete '{p[1] if p else ''}'?"): return
        if delete_product(self.sel_id):
            if p: self.undo_stk.append({"a":"delete","d":p[1:7]})
            self.redo_stk.clear(); self._load(); self._clear()
            messagebox.showinfo("Deleted","Product deleted! 🗑️")
        else:
            messagebox.showerror("Error","Failed to delete.")

    def _search(self):
        kw = self.s_name.get().strip()
        if not kw: messagebox.showwarning("Warning","Enter a keyword."); return
        r = search_product(kw)
        self._populate(r) if r else messagebox.showinfo("No Results", f"No products found for '{kw}'.")

    def _filter(self):
        cat = self.s_cat.get()
        r   = get_all_products() if cat == "All" else search_by_category(cat)
        self._populate(r) if r else messagebox.showinfo("No Results", f"No products in '{cat}'.")

    def _record_sale(self):
        if not self.sel_id:
            messagebox.showwarning("Warning","Select a product first."); return
        try:
            qty = int(self.sale_qty.get().strip())
            if qty <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Invalid","Enter a valid quantity (whole number, more than 0)."); return
        p = get_by_id(self.sel_id)
        if not p: return
        total = qty * self.sel_price
        if not messagebox.askyesno("Confirm Sale",
            f"Product : {p[1]}\nQty     : {qty}\nPrice   : ₱{self.sel_price:,.2f}\nTotal   : ₱{total:,.2f}\n\nProceed?"): return
        ok, res = record_sale(self.sel_id, p[1], p[2], qty, self.sel_price)
        if ok:
            self.sale_qty.delete(0,tk.END); self.sale_qty.insert(0,"1")
            self._load(); self._clear()
            messagebox.showinfo("Sale Recorded!", f"✅ {p[1]} × {qty}\nTotal: ₱{total:,.2f}")
        else:
            messagebox.showerror("Failed", res)

    # ── UNDO / REDO ───────────────────────────────────────────────────────────

    def _history(self, src, dst, label):
        if not src: messagebox.showinfo(label, "Nothing to undo/redo."); return
        e = src.pop()
        if e["a"] == "add":
            all_p = get_all_products()
            if label == "Undo" and all_p: delete_product(all_p[-1][0])
            elif label == "Redo": add_product(*e["d"])
            dst.append({"a":"add","d":e["d"]})
        elif e["a"] == "delete":
            if label == "Undo": add_product(*e["d"])
            else:
                p = next((x for x in get_all_products() if x[1]==e["d"][0]), None)
                if p: delete_product(p[0])
            dst.append({"a":"delete","d":e["d"]})
        elif e["a"] == "update":
            update_product(e["id"], *(e["old"] if label=="Undo" else e["new"]))
            dst.append({"a":"update","id":e["id"],"old":e["new"],"new":e["old"]})
        self._load(); self._clear()

    def _undo(self): self._history(self.undo_stk, self.redo_stk, "Undo")
    def _redo(self): self._history(self.redo_stk, self.undo_stk, "Redo")

    # ── REPORT ────────────────────────────────────────────────────────────────

    def _refresh_report(self):
        s = get_summary()
        if s and s[0]:
            self.c_sales.config(text=str(s[0][0]))
            self.c_rev.config(text=f"₱{s[0][1]:,.2f}")
        self.c_low.config(text=str(len(get_low_stock())))

        self.t_daily.delete(*self.t_daily.get_children())
        for r in get_daily_sales():
            self.t_daily.insert("","end", values=(str(r[0]), r[1], f"₱{r[2]:,.2f}"))

        self.t_best.delete(*self.t_best.get_children())
        for r in get_best_sellers():
            self.t_best.insert("","end", values=(r[0], r[1], r[2], f"₱{r[3]:,.2f}"))

        self.t_log.delete(*self.t_log.get_children())
        for r in get_all_sales():
            self.t_log.insert("","end", values=(
                r[0], r[1].strftime("%b %d, %Y %I:%M %p"),
                r[2], r[4], f"₱{r[5]:,.2f}", f"₱{r[6]:,.2f}"
            ))


# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
