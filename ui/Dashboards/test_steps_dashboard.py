"""
GRC360 — Test Steps Dashboard  (Clean Edition)
Table : test_steps
Place : ui/Dashboards/test_steps_dashboard.py
Launch: open_test_steps_dashboard(tk.Toplevel())
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import threading

from connectors.lambda_mysql import call_lambda

# ── SCHEMA ────────────────────────────────────────────────────
TABLE   = "test_steps"
COLUMNS = ["test_step_id", "control_assertion", "assertion_description",
           "step_order", "control_area", "risk_type", "status", "created_date"]

# ── PALETTE ───────────────────────────────────────────────────
BG     = "#F0F4F8"
PANEL  = "#FFFFFF"
HEADER = "#1E2A3A"
BORDER = "#CBD5E1"
ACC    = "#06B6D4"
TEXT   = "#1E293B"
DIM    = "#64748B"
GREEN  = "#10B981"
ROSE   = "#F43F5E"
GOLD   = "#F59E0B"
VIOLET = "#8B5CF6"
AMBER  = "#F97316"
WHITE  = "#FFFFFF"
REVE   = "#F8FAFC"

STATUS_C = {
    "pass":        GREEN,
    "passed":      GREEN,
    "fail":        ROSE,
    "failed":      ROSE,
    "pending":     GOLD,
    "in progress": VIOLET,
    "skipped":     DIM,
    "draft":       DIM,
    "active":      ACC,
    "completed":   ACC,
    "review":      AMBER,
}

def sclr(s): return STATUS_C.get((s or "").lower(), DIM)

# ── DATA ──────────────────────────────────────────────────────
def fetch_steps():
    r = call_lambda({"action": "select", "table": TABLE, "columns": COLUMNS})
    return r.get("records", [])


# ── STAT CARD ─────────────────────────────────────────────────
class StatCard(tk.Frame):
    def __init__(self, parent, label, color, **kw):
        super().__init__(parent, bg=PANEL,
                         highlightbackground=color,
                         highlightthickness=2, **kw)
        self._val_lbl = tk.Label(self, text="0", bg=PANEL, fg=color,
                                  font=("Segoe UI", 18, "bold"))
        self._val_lbl.pack(pady=(8, 0))
        tk.Label(self, text=label, bg=PANEL, fg=DIM,
                 font=("Segoe UI", 7)).pack(pady=(0, 8))

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
        tk.Label(self, text="Select a step\nto view details",
                 bg=PANEL, fg=DIM,
                 font=("Segoe UI", 9),
                 justify="center").pack(expand=True)

    def show(self, row):
        self._clear()
        sc = sclr(row.get("status", ""))

        # Coloured header
        hdr = tk.Frame(self, bg=sc, padx=12, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"Step  #{ row.get('test_step_id', '') }  ·  Order: { row.get('step_order', '—') }",
                 bg=sc, fg=WHITE,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(hdr,
                 text=(row.get("control_assertion") or "")[:32],
                 bg=sc, fg=WHITE,
                 font=("Segoe UI", 9, "bold"),
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
        sb = tk.Scrollbar(outer, orient="vertical", command=cv.yview, width=6)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        cv.configure(yscrollcommand=sb.set)
        body = tk.Frame(cv, bg=PANEL, padx=12, pady=10)
        win  = cv.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>",
                  lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",
                lambda e: cv.itemconfig(win, width=e.width))

        # Risk type badge
        if row.get("risk_type"):
            rb = tk.Frame(body, bg=ROSE, padx=6, pady=2)
            rb.pack(anchor="w", pady=(0, 8))
            tk.Label(rb, text=f"⚡  { (row.get('risk_type') or '').upper() }",
                     bg=ROSE, fg=WHITE,
                     font=("Segoe UI", 7, "bold")).pack()

        fields = [
            ("Control Area",          row.get("control_area")         or "—"),
            ("Risk Type",             row.get("risk_type")            or "—"),
            ("Created Date",          str(row.get("created_date") or "—")[:19]),
            ("Assertion Description", row.get("assertion_description") or "—"),
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
class TestStepsDashboard:

    def __init__(self, root):
        self.root        = root
        self.root.title("GRC360 — Test Steps Dashboard")
        self.root.geometry("900x640")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self._steps      = []
        self._filtered   = []
        self._iid_map    = {}
        self._search_var = tk.StringVar()
        self._area_var   = tk.StringVar(value="All Areas")
        self._risk_var   = tk.StringVar(value="All Risks")
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
        tk.Label(hdr, text="🔬  Test Steps Dashboard",
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
                  activebackground="#0891B2",
                  command=self._load).pack(side="right", padx=(0, 8), pady=8)

        # ── STAT CARDS ──────────────────────────────────────
        cards_row = tk.Frame(self.root, bg=BG)
        cards_row.pack(fill="x", padx=12, pady=(10, 6))
        self._c_total   = StatCard(cards_row, "Total Steps",    ACC)
        self._c_passed  = StatCard(cards_row, "Passed",         GREEN)
        self._c_failed  = StatCard(cards_row, "Failed",         ROSE)
        self._c_pending = StatCard(cards_row, "Pending",        GOLD)
        self._c_areas   = StatCard(cards_row, "Control Areas",  VIOLET)
        for c in (self._c_total, self._c_passed, self._c_failed,
                  self._c_pending, self._c_areas):
            c.pack(side="left", expand=True, fill="x", padx=3)

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
                 insertbackground=TEXT, relief="flat", width=18).pack(
                     side="left", ipady=5, padx=(2, 6))
        self._search_var.trace_add("write", lambda *_: self._filter())

        for var, attr in [(self._area_var, "_area_menu"),
                          (self._risk_var, "_risk_menu"),
                          (self._stat_var, "_stat_menu")]:
            btn = tk.Menubutton(tb, textvariable=var,
                                font=("Segoe UI", 9), bg=WHITE, fg=TEXT,
                                relief="solid", bd=1,
                                padx=8, pady=5, cursor="hand2",
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
        style.configure("TS.Treeview",
                        background=WHITE, foreground=TEXT,
                        fieldbackground=WHITE, rowheight=24,
                        font=("Segoe UI", 9), borderwidth=0)
        style.configure("TS.Treeview.Heading",
                        background=HEADER, foreground=WHITE,
                        font=("Segoe UI", 9, "bold"), relief="flat")
        style.map("TS.Treeview",
                  background=[("selected", ACC)],
                  foreground=[("selected", WHITE)])

        vis    = ("test_step_id", "control_assertion", "step_order",
                  "control_area", "risk_type", "status", "created_date")
        labels = {"test_step_id": "ID", "control_assertion": "Control Assertion",
                  "step_order": "Order", "control_area": "Control Area",
                  "risk_type": "Risk Type", "status": "Status",
                  "created_date": "Created"}
        widths = {"test_step_id": 35, "control_assertion": 175,
                  "step_order": 45, "control_area": 90,
                  "risk_type": 80, "status": 70, "created_date": 100}

        wrap = tk.Frame(tframe, bg=BORDER, bd=1)
        wrap.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(wrap, columns=vis, show="headings",
                                  style="TS.Treeview", selectmode="browse")
        for c in vis:
            self.tree.heading(c, text=labels[c],
                              command=lambda col=c: self._sort(col))
            self.tree.column(c, width=widths[c], anchor="w",
                             stretch=(c == "control_assertion"))

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
            rows = fetch_steps()
            self.root.after(0, self._loaded, rows, None)
        except Exception as e:
            self.root.after(0, self._loaded, [], str(e))

    def _loaded(self, rows, err):
        if err:
            self._status_lbl.config(text=f"❌ {err}", fg=ROSE)
            messagebox.showerror("Error", err, parent=self.root)
            return

        self._steps = rows
        self._status_lbl.config(text=f"●  {len(rows)} records", fg=GREEN)

        passed  = sum(1 for s in rows if (s.get("status") or "").lower() in ("pass","passed"))
        failed  = sum(1 for s in rows if (s.get("status") or "").lower() in ("fail","failed"))
        pending = sum(1 for s in rows if (s.get("status") or "").lower() == "pending")
        areas   = len({s.get("control_area") for s in rows if s.get("control_area")})

        self._c_total.update_value(len(rows))
        self._c_passed.update_value(passed)
        self._c_failed.update_value(failed)
        self._c_pending.update_value(pending)
        self._c_areas.update_value(areas)

        all_areas = sorted({s.get("control_area") or "Unknown" for s in rows})
        all_risks = sorted({s.get("risk_type")    or "Unknown" for s in rows})
        all_stats = sorted({(s.get("status") or "Unknown").capitalize() for s in rows})

        for menu, var, label, values in [
            (self._area_menu, self._area_var, "All Areas",  all_areas),
            (self._risk_menu, self._risk_var, "All Risks",  all_risks),
            (self._stat_menu, self._stat_var, "All Status", all_stats),
        ]:
            menu.delete(0, "end")
            menu.add_command(label=label,
                             command=lambda v=var, l=label: v.set(l) or self._filter())
            for val in values:
                menu.add_command(label=val,
                                 command=lambda x=val, v=var: v.set(x) or self._filter())

        self._filter()

    def _filter(self):
        q    = self._search_var.get().lower().strip()
        area = self._area_var.get()
        risk = self._risk_var.get()
        stat = self._stat_var.get()
        self._filtered = [
            s for s in self._steps
            if (area == "All Areas"   or s.get("control_area") == area)
            and (risk == "All Risks"  or s.get("risk_type") == risk)
            and (stat == "All Status" or (s.get("status") or "").lower() == stat.lower())
            and (not q or any(q in str(v).lower() for v in s.values()))
        ]
        self._populate()
        self._count_lbl.config(
            text=f"{len(self._filtered)} / {len(self._steps)} records")

    def _populate(self):
        self.tree.delete(*self.tree.get_children())
        self._iid_map = {}
        for i, s in enumerate(self._filtered):
            base = "even" if i % 2 == 0 else "odd"
            stag = f"s_{(s.get('status') or '').lower()}"
            vals = (s.get("test_step_id")          or "",
                    s.get("control_assertion")      or "",
                    s.get("step_order")             or "",
                    s.get("control_area")           or "",
                    s.get("risk_type")              or "",
                    s.get("status")                 or "",
                    str(s.get("created_date") or "")[:19])
            iid = self.tree.insert("", "end", values=vals, tags=(base, stag))
            self._iid_map[iid] = s
        self._detail._idle()

    def _sort(self, col):
        rev = self._sort_state.get(col, False)
        try:
            self._filtered.sort(
                key=lambda r: int(r.get(col) or 0) if col == "step_order"
                else str(r.get(col) or ""),
                reverse=rev)
        except Exception:
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
def open_test_steps_dashboard(win=None):
    if win is None:
        win = tk.Tk()
        TestStepsDashboard(win)
        win.mainloop()
    else:
        TestStepsDashboard(win)


if __name__ == "__main__":
    open_test_steps_dashboard()
