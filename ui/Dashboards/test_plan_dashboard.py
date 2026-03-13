"""
GRC360 — Test Plan Dashboard  (Clean Edition)
Table : test_plan
Place : ui/Dashboards/test_plan_dashboard.py
Launch: open_test_plan_dashboard(tk.Toplevel())
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import threading

from connectors.lambda_mysql import call_lambda

# ── SCHEMA ────────────────────────────────────────────────────
TABLE   = "test_plan"
COLUMNS = ["test_plan_id", "test_plan_name", "description",
           "module", "created_by", "created_date", "status"]

# ── PALETTE ───────────────────────────────────────────────────
BG     = "#F0F4F8"
PANEL  = "#FFFFFF"
HEADER = "#1E2A3A"
BORDER = "#CBD5E1"
ACC    = "#7C3AED"
TEXT   = "#1E293B"
DIM    = "#64748B"
GREEN  = "#10B981"
ROSE   = "#F43F5E"
GOLD   = "#F59E0B"
TEAL   = "#06B6D4"
WHITE  = "#FFFFFF"
REVE   = "#F8FAFC"

STATUS_C = {
    "active":      GREEN,
    "inactive":    ROSE,
    "draft":       DIM,
    "completed":   TEAL,
    "in progress": ACC,
    "pending":     GOLD,
    "approved":    TEAL,
    "review":      GOLD,
}

def sclr(s): return STATUS_C.get((s or "").lower(), DIM)

# ── DATA ──────────────────────────────────────────────────────
def fetch_plans():
    r = call_lambda({"action": "select", "table": TABLE, "columns": COLUMNS})
    return r.get("records", [])


# ── STAT CARD ─────────────────────────────────────────────────
class StatCard(tk.Frame):
    def __init__(self, parent, label, color, **kw):
        super().__init__(parent, bg=PANEL,
                         highlightbackground=color,
                         highlightthickness=2, **kw)
        self._color = color
        self._val_lbl = tk.Label(self, text="0", bg=PANEL, fg=color,
                                  font=("Segoe UI", 20, "bold"))
        self._val_lbl.pack(pady=(10, 0))
        tk.Label(self, text=label, bg=PANEL, fg=DIM,
                 font=("Segoe UI", 8)).pack(pady=(0, 10))

    def update_value(self, v):
        self._val_lbl.config(text=str(v))


# ── DETAIL PANEL ──────────────────────────────────────────────
class DetailPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=PANEL,
                         highlightbackground=BORDER,
                         highlightthickness=1,
                         width=230, **kw)
        self.pack_propagate(False)
        self._idle()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _idle(self):
        self._clear()
        tk.Label(self, text="Select a plan\nto view details",
                 bg=PANEL, fg=DIM,
                 font=("Segoe UI", 9),
                 justify="center").pack(expand=True)

    def show(self, row):
        self._clear()
        sc = sclr(row.get("status", ""))

        # Coloured header
        hdr = tk.Frame(self, bg=sc, padx=12, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"Plan  #{ row.get('test_plan_id', '') }",
                 bg=sc, fg=WHITE,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(hdr,
                 text=(row.get("test_plan_name") or "")[:30],
                 bg=sc, fg=WHITE,
                 font=("Segoe UI", 10, "bold"),
                 wraplength=206, justify="left").pack(anchor="w", pady=(4, 0))
        pill = tk.Frame(hdr, bg=WHITE, padx=6, pady=2)
        pill.pack(anchor="w", pady=(6, 0))
        tk.Label(pill, text=(row.get("status") or "—").upper(),
                 bg=WHITE, fg=sc,
                 font=("Segoe UI", 7, "bold")).pack()

        # Scrollable body
        outer = tk.Frame(self, bg=PANEL)
        outer.pack(fill="both", expand=True)
        cv = tk.Canvas(outer, bg=PANEL, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=cv.yview,
                          width=6)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        cv.configure(yscrollcommand=sb.set)
        body = tk.Frame(cv, bg=PANEL, padx=12, pady=10)
        win  = cv.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>",
                  lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",
                lambda e: cv.itemconfig(win, width=e.width))

        fields = [
            ("Module",       row.get("module")       or "—"),
            ("Created By",   row.get("created_by")   or "—"),
            ("Created Date", str(row.get("created_date") or "—")[:19]),
            ("Description",  row.get("description")  or "—"),
        ]
        for lbl, val in fields:
            tk.Label(body, text=lbl, bg=PANEL, fg=DIM,
                     font=("Segoe UI", 7, "bold"),
                     anchor="w").pack(fill="x", pady=(8, 1))
            tk.Label(body, text=val, bg=PANEL, fg=TEXT,
                     font=("Segoe UI", 9),
                     wraplength=200, justify="left",
                     anchor="w").pack(fill="x")
            tk.Frame(body, bg=BORDER, height=1).pack(fill="x", pady=(6, 0))


# ── MAIN DASHBOARD ────────────────────────────────────────────
class TestPlanDashboard:

    def __init__(self, root):
        self.root        = root
        self.root.title("GRC360 — Test Plan Dashboard")
        self.root.geometry("900x640")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self._plans      = []
        self._filtered   = []
        self._iid_map    = {}
        self._search_var = tk.StringVar()
        self._mod_var    = tk.StringVar(value="All Modules")
        self._stat_var   = tk.StringVar(value="All Status")
        self._sort_state = {}

        self._build_ui()
        self._load()

    def _build_ui(self):
        # ── HEADER ──────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=HEADER, height=46)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=ACC, width=4).pack(side="left", fill="y")
        tk.Label(hdr, text="📋  Test Plan Dashboard",
                 bg=HEADER, fg=WHITE,
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=12)
        self._status_lbl = tk.Label(hdr, text="⏳  Loading…",
                                    bg=HEADER, fg=GOLD,
                                    font=("Segoe UI", 9))
        self._status_lbl.pack(side="right", padx=10)
        tk.Button(hdr, text="↺  Refresh",
                  font=("Segoe UI", 9),
                  bg=ACC, fg=WHITE, relief="flat", bd=0,
                  padx=10, pady=3, cursor="hand2",
                  activebackground="#5B21B6",
                  command=self._load).pack(side="right", padx=(0, 8), pady=8)

        # ── STAT CARDS ──────────────────────────────────────
        cards_row = tk.Frame(self.root, bg=BG)
        cards_row.pack(fill="x", padx=12, pady=(10, 6))
        self._c_total   = StatCard(cards_row, "Total Plans",  ACC)
        self._c_active  = StatCard(cards_row, "Active",       GREEN)
        self._c_modules = StatCard(cards_row, "Modules",      TEAL)
        self._c_authors = StatCard(cards_row, "Authors",      GOLD)
        for c in (self._c_total, self._c_active, self._c_modules, self._c_authors):
            c.pack(side="left", expand=True, fill="x", padx=4)

        # ── TOOLBAR ─────────────────────────────────────────
        tb = tk.Frame(self.root, bg=BG)
        tb.pack(fill="x", padx=12, pady=(0, 6))

        sf = tk.Frame(tb, bg=WHITE,
                      highlightbackground=BORDER, highlightthickness=1)
        sf.pack(side="left")
        tk.Label(sf, text=" 🔍", bg=WHITE, fg=DIM,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Entry(sf, textvariable=self._search_var,
                 font=("Segoe UI", 9), bg=WHITE, fg=TEXT,
                 insertbackground=TEXT, relief="flat", width=22).pack(
                     side="left", ipady=5, padx=(2, 6))
        self._search_var.trace_add("write", lambda *_: self._filter())

        for var, attr in [(self._mod_var,  "_mod_menu"),
                          (self._stat_var, "_stat_menu")]:
            btn = tk.Menubutton(tb, textvariable=var,
                                font=("Segoe UI", 9), bg=WHITE, fg=TEXT,
                                relief="solid", bd=1,
                                padx=10, pady=5, cursor="hand2",
                                indicatoron=True)
            btn.pack(side="left", padx=(6, 0))
            m = tk.Menu(btn, tearoff=0, bg=WHITE, fg=TEXT,
                        activebackground=ACC,
                        activeforeground=WHITE)
            btn["menu"] = m
            setattr(self, attr, m)

        self._count_lbl = tk.Label(tb, text="", bg=BG, fg=DIM,
                                   font=("Segoe UI", 8))
        self._count_lbl.pack(side="right")

        # ── MAIN AREA ───────────────────────────────────────
        main = tk.Frame(self.root, bg=BG)
        main.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Table
        tframe = tk.Frame(main, bg=BG)
        tframe.pack(side="left", fill="both", expand=True)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TP.Treeview",
                        background=WHITE, foreground=TEXT,
                        fieldbackground=WHITE, rowheight=24,
                        font=("Segoe UI", 9), borderwidth=0)
        style.configure("TP.Treeview.Heading",
                        background=HEADER, foreground=WHITE,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("TP.Treeview",
                  background=[("selected", ACC)],
                  foreground=[("selected", WHITE)])

        vis    = ("test_plan_id", "test_plan_name", "module",
                  "created_by", "created_date", "status")
        labels = {"test_plan_id": "ID", "test_plan_name": "Plan Name",
                  "module": "Module", "created_by": "Author",
                  "created_date": "Created Date", "status": "Status"}
        widths = {"test_plan_id": 40, "test_plan_name": 185,
                  "module": 90, "created_by": 90,
                  "created_date": 115, "status": 75}

        wrap = tk.Frame(tframe, bg=BORDER, bd=1)
        wrap.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(wrap, columns=vis, show="headings",
                                  style="TP.Treeview", selectmode="browse")
        for c in vis:
            self.tree.heading(c, text=labels[c],
                              command=lambda col=c: self._sort(col))
            self.tree.column(c, width=widths[c], anchor="w",
                             stretch=(c == "test_plan_name"))

        vsb = ttk.Scrollbar(wrap, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(wrap, orient="horizontal",  command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        wrap.grid_rowconfigure(0, weight=1)
        wrap.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure("even", background=REVE)
        self.tree.tag_configure("odd",  background=WHITE)
        for sk, clr in STATUS_C.items():
            self.tree.tag_configure(f"s_{sk}", foreground=clr)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # Detail panel
        self._detail = DetailPanel(main)
        self._detail.pack(side="right", fill="y", padx=(8, 0))

    # ── DATA FLOW ────────────────────────────────────────────
    def _load(self):
        self._status_lbl.config(text="⏳  Loading…", fg=GOLD)
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            rows = fetch_plans()
            self.root.after(0, self._loaded, rows, None)
        except Exception as e:
            self.root.after(0, self._loaded, [], str(e))

    def _loaded(self, rows, err):
        if err:
            self._status_lbl.config(text=f"❌ {err}", fg=ROSE)
            messagebox.showerror("Error", err, parent=self.root)
            return

        self._plans = rows
        self._status_lbl.config(text=f"●  {len(rows)} records", fg=GREEN)

        active  = sum(1 for p in rows if (p.get("status") or "").lower() == "active")
        modules = len({p.get("module") for p in rows if p.get("module")})
        authors = len({p.get("created_by") for p in rows if p.get("created_by")})

        self._c_total.update_value(len(rows))
        self._c_active.update_value(active)
        self._c_modules.update_value(modules)
        self._c_authors.update_value(authors)

        all_mods  = sorted({p.get("module") or "Unknown" for p in rows})
        all_stats = sorted({(p.get("status") or "Unknown").capitalize() for p in rows})

        self._mod_menu.delete(0, "end")
        self._mod_menu.add_command(label="All Modules",
            command=lambda: self._mod_var.set("All Modules") or self._filter())
        for m in all_mods:
            self._mod_menu.add_command(label=m,
                command=lambda x=m: self._mod_var.set(x) or self._filter())

        self._stat_menu.delete(0, "end")
        self._stat_menu.add_command(label="All Status",
            command=lambda: self._stat_var.set("All Status") or self._filter())
        for s in all_stats:
            self._stat_menu.add_command(label=s,
                command=lambda x=s: self._stat_var.set(x) or self._filter())

        self._filter()

    def _filter(self):
        q   = self._search_var.get().lower().strip()
        mod = self._mod_var.get()
        st  = self._stat_var.get()
        self._filtered = [
            p for p in self._plans
            if (mod == "All Modules" or p.get("module") == mod)
            and (st  == "All Status" or (p.get("status") or "").lower() == st.lower())
            and (not q or any(q in str(v).lower() for v in p.values()))
        ]
        self._populate()
        self._count_lbl.config(
            text=f"{len(self._filtered)} / {len(self._plans)} records")

    def _populate(self):
        self.tree.delete(*self.tree.get_children())
        self._iid_map = {}
        for i, p in enumerate(self._filtered):
            base = "even" if i % 2 == 0 else "odd"
            stag = f"s_{(p.get('status') or '').lower()}"
            vals = (p.get("test_plan_id")  or "",
                    p.get("test_plan_name") or "",
                    p.get("module")         or "",
                    p.get("created_by")     or "",
                    str(p.get("created_date") or "")[:19],
                    p.get("status")         or "")
            iid = self.tree.insert("", "end", values=vals, tags=(base, stag))
            self._iid_map[iid] = p
        self._detail._idle()

    def _sort(self, col):
        rev = self._sort_state.get(col, False)
        self._filtered.sort(key=lambda r: str(r.get(col) or ""), reverse=rev)
        self._sort_state[col] = not rev
        self._populate()

    def _on_select(self, _):
        sel = self.tree.selection()
        if sel:
            row = self._iid_map.get(sel[0])
            if row:
                self._detail.show(row)


# ── LAUNCHER ─────────────────────────────────────────────────
def open_test_plan_dashboard(win=None):
    if win is None:
        win = tk.Tk()
        TestPlanDashboard(win)
        win.mainloop()
    else:
        TestPlanDashboard(win)


if __name__ == "__main__":
    open_test_plan_dashboard()
