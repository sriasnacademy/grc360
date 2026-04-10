"""
GRC360 — Control Report Dashboard  (Fixed + Enhanced Edition)

Tables used:
  control                  — all control records
  risk                     — to get linked risk name/severity  (via risk_id on control)
  test_plan_control_map    — links test_plan_id → control_id
  test_plan                — to get test plan name for each control

Two queries are run:
  1. Controls LEFT JOIN risk        → gives risk name + severity per control
  2. test_plan_control_map JOIN test_plan → gives test plan names per control_id

Place in: ui/Dashboards/control_dashboard.py
Call:     open_control_dashboard(tk.Toplevel())
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from collections import defaultdict

from connectors.lambda_mysql import call_lambda

# ─────────────────────────────────────────────
#  SQL QUERIES
# ─────────────────────────────────────────────

# 1. All controls with their linked risk (if any)
CONTROLS_SQL = """
    SELECT
        c.control_id,
        c.control_name,
        c.control_type,
        c.control_category,
        c.description,
        c.status,
        c.risk_id,
        r.risk_name,
        r.severity   AS risk_severity
    FROM control c
    LEFT JOIN risk r ON r.risk_id = c.risk_id
"""

# 2. Map control_id → list of test plans (via test_plan_control_map)
TEST_PLANS_SQL = """
    SELECT
        m.control_id,
        tp.test_plan_id,
        tp.test_plan_name
    FROM test_plan_control_map m
    JOIN test_plan tp ON tp.test_plan_id = m.test_plan_id
"""

# ─────────────────────────────────────────────
#  DESIGN TOKENS  (emerald-green)
# ─────────────────────────────────────────────
C = {
    "bg":          "#0A1F1C",
    "sidebar":     "#0D2820",
    "card":        "#0F2E28",
    "card_border": "#1A4A40",
    "accent":      "#10B981",
    "accent2":     "#34D399",
    "success":     "#10B981",
    "warning":     "#F59E0B",
    "danger":      "#EF4444",
    "purple":      "#A78BFA",
    "sky":         "#38BDF8",
    "text_main":   "#D1FAE5",
    "text_dim":    "#6EE7B7",
    "text_tiny":   "#2D6A5A",
    "row_even":    "#081A17",
    "row_odd":     "#0F2E28",
    "row_select":  "#0D3D2F",
    "input_bg":    "#0D2820",
    "input_fg":    "#D1FAE5",
}

STATUS_COLORS = {
    "active":    "#10B981",
    "inactive":  "#EF4444",
    "pending":   "#F59E0B",
    "draft":     "#6EE7B7",
    "approved":  "#38BDF8",
    "review":    "#A78BFA",
    "completed": "#34D399",
}
SEV_COLORS = {
    "critical": "#EF4444",
    "high":     "#F97316",
    "medium":   "#F59E0B",
    "low":      "#10B981",
    "info":     "#38BDF8",
}
TYPE_COLORS = ["#10B981","#38BDF8","#A78BFA","#F59E0B","#EF4444","#F97316"]
CAT_COLORS  = ["#34D399","#7DD3FC","#C4B5FD","#FCD34D","#FCA5A5","#86EFAC"]

FONT_HEAD   = ("Segoe UI", 9,  "bold")
FONT_CELL   = ("Segoe UI", 9)
FONT_CARD_N = ("Segoe UI", 22, "bold")
FONT_CARD_L = ("Segoe UI", 8)
FONT_SECT   = ("Segoe UI", 8,  "bold")
FONT_SEARCH = ("Segoe UI", 10)


# ─────────────────────────────────────────────
#  DATA FETCH
# ─────────────────────────────────────────────
def fetch_controls_with_risks():
    """Returns list of control dicts, each with risk_name & risk_severity."""
    payload  = {"action": "raw_sql", "sql": CONTROLS_SQL}
    response = call_lambda(payload)
    return response.get("records", [])


def fetch_test_plan_map():
    """Returns {control_id: [test_plan_name, ...]}"""
    payload  = {"action": "raw_sql", "sql": TEST_PLANS_SQL}
    response = call_lambda(payload)
    rows     = response.get("records", [])
    mapping  = defaultdict(list)
    for r in rows:
        cid   = r.get("control_id")
        tname = r.get("test_plan_name","")
        if cid and tname:
            mapping[cid].append(tname)
    return dict(mapping)


def status_color(s):
    return STATUS_COLORS.get((s or "").lower(), C["text_dim"])


# ─────────────────────────────────────────────
#  STAT CARD
# ─────────────────────────────────────────────
class StatCard(tk.Frame):
    def __init__(self, parent, icon, label, value, accent, **kw):
        super().__init__(parent, bg=C["card"],
                         highlightbackground=accent, highlightthickness=1, **kw)
        tk.Frame(self, bg=accent, height=3).pack(side="bottom", fill="x")
        inner = tk.Frame(self, bg=C["card"], padx=12, pady=10)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=icon, bg=C["card"], fg=accent,
                 font=("Segoe UI", 18)).pack(anchor="w")
        tk.Label(inner, text=str(value), bg=C["card"], fg=accent,
                 font=FONT_CARD_N).pack(anchor="w")
        tk.Label(inner, text=label.upper(), bg=C["card"],
                 fg=C["text_dim"], font=FONT_CARD_L).pack(anchor="w")


# ─────────────────────────────────────────────
#  DETAIL PANEL  (left side)
# ─────────────────────────────────────────────
class DetailPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["sidebar"],
                         highlightbackground=C["card_border"],
                         highlightthickness=1, width=275, **kw)
        self.pack_propagate(False)
        self._build_empty()

    def _clear(self):
        for w in self.winfo_children(): w.destroy()

    def _build_empty(self):
        self._clear()
        tk.Label(self, text="🛡️\n\nSelect a control\nto view full details",
                 bg=C["sidebar"], fg=C["text_tiny"],
                 font=("Segoe UI", 10), justify="center").pack(expand=True)

    def show(self, row, tp_map):
        self._clear()
        sc  = status_color(row.get("status",""))

        # ── Header ────────────────────────────────────────
        hdr = tk.Frame(self, bg=C["accent"], padx=14, pady=10)
        hdr.pack(fill="x")
        top = tk.Frame(hdr, bg=C["accent"])
        top.pack(fill="x")
        tk.Label(top, text=f"CTL-{row.get('control_id','')}",
                 bg=C["accent"], fg="#FFFFFF",
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        pill = tk.Frame(top, bg=sc, padx=6, pady=1)
        pill.pack(side="right")
        tk.Label(pill, text=(row.get("status") or "—").capitalize(),
                 bg=sc, fg="#FFFFFF", font=("Segoe UI", 8, "bold")).pack()
        tk.Label(hdr, text=row.get("control_name",""), bg=C["accent"],
                 fg="#FFFFFF", font=("Segoe UI", 11, "bold"),
                 wraplength=245, justify="left").pack(anchor="w", pady=(4,0))

        # Type / Category badges
        badges = tk.Frame(hdr, bg=C["accent"])
        badges.pack(anchor="w", pady=(6,0))
        for txt, bg_c in [(row.get("control_type",""),     "#065F46"),
                           (row.get("control_category",""), "#064E3B")]:
            if txt:
                b = tk.Frame(badges, bg=bg_c, padx=7, pady=2)
                b.pack(side="left", padx=(0,6))
                tk.Label(b, text=txt.upper(), bg=bg_c, fg="#D1FAE5",
                         font=("Segoe UI", 7, "bold")).pack()

        # ── Linked Risk badge ─────────────────────────────
        rname = row.get("risk_name","") or ""
        rsev  = (row.get("risk_severity","") or "").lower()
        if rname:
            rbg = SEV_COLORS.get(rsev, "#374151")
            rb  = tk.Frame(hdr, bg=rbg, padx=8, pady=3)
            rb.pack(anchor="w", pady=(8,0))
            tk.Label(rb, text=f"⚠️  Risk [{rsev.upper() or '?'}]: {rname[:35]}",
                     bg=rbg, fg="#FFFFFF",
                     font=("Segoe UI", 8, "bold"),
                     wraplength=240, justify="left").pack(anchor="w")
        else:
            nb = tk.Frame(hdr, bg="#1A4A3A", padx=8, pady=3)
            nb.pack(anchor="w", pady=(8,0))
            tk.Label(nb, text="⚠️  No risk linked",
                     bg="#1A4A3A", fg="#6EE7B7",
                     font=("Segoe UI", 8)).pack(anchor="w")

        # ── Scrollable body ───────────────────────────────
        outer = tk.Frame(self, bg=C["sidebar"])
        outer.pack(fill="both", expand=True)
        cv = tk.Canvas(outer, bg=C["sidebar"], highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=cv.yview, width=6)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        cv.configure(yscrollcommand=sb.set)
        body = tk.Frame(cv, bg=C["sidebar"], padx=14, pady=10)
        win  = cv.create_window((0,0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(win, width=e.width))

        # Linked Test Plans
        cid    = row.get("control_id")
        tnames = tp_map.get(cid, [])
        tk.Label(body, text="📋  Test Plans Using This Control",
                 bg=C["sidebar"], fg=C["text_dim"],
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(4,0))
        if tnames:
            for tname in tnames:
                f = tk.Frame(body, bg="#0D3D2F", padx=6, pady=2)
                f.pack(fill="x", pady=2)
                tk.Label(f, text=f"📋  {tname}", bg="#0D3D2F", fg="#34D399",
                         font=("Segoe UI", 8), anchor="w",
                         wraplength=230).pack(anchor="w")
        else:
            tk.Label(body, text="None", bg=C["sidebar"], fg="#4A7A6A",
                     font=("Segoe UI", 9), anchor="w").pack(fill="x")

        tk.Frame(body, bg=C["card_border"], height=1).pack(fill="x", pady=10)
        for lbl, key in [("🔧  Control Type",  "control_type"),
                          ("🗂️  Category",      "control_category"),
                          ("📄  Description",   "description")]:
            tk.Label(body, text=lbl, bg=C["sidebar"], fg=C["text_dim"],
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(8,0))
            tk.Label(body, text=row.get(key) or "—", bg=C["sidebar"],
                     fg=C["text_main"], font=("Segoe UI", 9),
                     wraplength=245, justify="left", anchor="w").pack(fill="x")


# ─────────────────────────────────────────────
#  QUANT PANEL  (right side)
# ─────────────────────────────────────────────
class QuantPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["bg"], width=275, **kw)
        self.pack_propagate(False)
        hdr = tk.Frame(self, bg=C["card_border"], height=32)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="📊  CONTROL ANALYTICS", bg=C["card_border"],
                 fg=C["text_dim"], font=FONT_SECT).pack(side="left", padx=10, pady=7)
        self._body_frame = None

    def refresh(self, controls, filtered, tp_map):
        if self._body_frame:
            self._body_frame.destroy()

        outer = tk.Frame(self, bg=C["bg"])
        outer.pack(fill="both", expand=True)
        cv = tk.Canvas(outer, bg=C["bg"], highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=cv.yview, width=6)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        cv.configure(yscrollcommand=sb.set)
        body = tk.Frame(cv, bg=C["bg"])
        win  = cv.create_window((0,0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(win, width=e.width))
        self._body_frame = outer

        total     = len(controls)
        visible   = len(filtered)
        active    = sum(1 for r in controls if (r.get("status") or "").lower() == "active")
        inactive  = sum(1 for r in controls if (r.get("status") or "").lower() == "inactive")
        linked_r  = sum(1 for r in controls if r.get("risk_name"))
        linked_tp = sum(1 for r in controls if tp_map.get(r.get("control_id")))
        types_n   = len({r.get("control_type") for r in controls if r.get("control_type")})
        cats_n    = len({r.get("control_category") for r in controls if r.get("control_category")})

        # ── KPI ───────────────────────────────────────────
        sf = self._section(body, "KEY METRICS")
        for lbl, val, clr in [
            ("Total Controls",         total,     C["accent2"]),
            ("Showing (filtered)",     visible,   C["sky"]),
            ("Active",                 active,    C["success"]),
            ("Inactive",               inactive,  C["danger"]),
            ("Linked to a Risk",       linked_r,  C["warning"]),
            ("Used in Test Plans",     linked_tp, C["purple"]),
            ("Control Types",          types_n,   C["teal"]),
            ("Categories",             cats_n,    C["sky"]),
        ]:
            r = tk.Frame(sf, bg=C["card"])
            r.pack(fill="x", pady=2)
            tk.Label(r, text=lbl, bg=C["card"], fg=C["text_dim"],
                     font=("Segoe UI", 8), anchor="w").pack(side="left")
            tk.Label(r, text=str(val), bg=C["card"], fg=clr,
                     font=("Segoe UI", 10, "bold")).pack(side="right")

        # ── Status ────────────────────────────────────────
        sc_c = {}
        for r in controls:
            k = (r.get("status") or "Unknown").capitalize()
            sc_c[k] = sc_c.get(k, 0) + 1
        self._bar(body, "BY STATUS", sc_c, list(STATUS_COLORS.values()), total)

        # ── Control Type ──────────────────────────────────
        ty_c = {}
        for r in controls:
            k = r.get("control_type") or "Unknown"
            ty_c[k] = ty_c.get(k, 0) + 1
        self._bar(body, "BY TYPE", ty_c, TYPE_COLORS, total)

        # ── Category ──────────────────────────────────────
        cat_c = {}
        for r in controls:
            k = r.get("control_category") or "Unknown"
            cat_c[k] = cat_c.get(k, 0) + 1
        self._bar(body, "BY CATEGORY", cat_c, CAT_COLORS, total)

        # ── Linked risk severity breakdown ────────────────
        rs_c = {"Unlinked": 0}
        for ctrl in controls:
            sev = (ctrl.get("risk_severity") or "").lower()
            if sev:
                k = sev.capitalize()
                rs_c[k] = rs_c.get(k, 0) + 1
            else:
                rs_c["Unlinked"] += 1
        self._bar(body, "LINKED RISK SEVERITY", rs_c,
                  list(SEV_COLORS.values()) + ["#94A3B8"], total)

    # ── helpers ───────────────────────────────────────────
    def _section(self, parent, title):
        f = tk.Frame(parent, bg=C["card"],
                     highlightbackground=C["card_border"], highlightthickness=1,
                     padx=10, pady=8)
        f.pack(fill="x", padx=6, pady=(0,8))
        tk.Label(f, text=title, bg=C["card"], fg=C["text_dim"],
                 font=FONT_SECT).pack(anchor="w")
        tk.Frame(f, bg=C["card_border"], height=1).pack(fill="x", pady=(4,6))
        return f

    def _bar(self, parent, title, data_dict, colors, grand_total):
        if not data_dict: return
        f = self._section(parent, title)
        max_v = max(data_dict.values(), default=1)
        BAR_W = 115
        for i, (k, v) in enumerate(sorted(data_dict.items(), key=lambda x: -x[1])):
            clr = colors[i % len(colors)]
            pct = round(100 * v / max(grand_total, 1), 1)
            row = tk.Frame(f, bg=C["card"])
            row.pack(fill="x", pady=2)
            txt = (k[:12] + "…") if len(k) > 13 else k
            tk.Label(row, text=txt, bg=C["card"], fg=C["text_main"],
                     font=("Segoe UI", 7), width=12, anchor="w").pack(side="left")
            cv2 = tk.Canvas(row, bg=C["card"], height=14, width=BAR_W, highlightthickness=0)
            cv2.pack(side="left", padx=(2,0))
            fw = int(BAR_W * v / max_v)
            cv2.create_rectangle(0, 2, BAR_W, 12, fill=C["card_border"], outline="")
            if fw: cv2.create_rectangle(0, 2, fw, 12, fill=clr, outline="")
            tk.Label(row, text=f"{v} · {pct}%", bg=C["card"], fg=clr,
                     font=("Segoe UI", 7, "bold"), width=9).pack(side="left", padx=2)


# ─────────────────────────────────────────────
#  MAIN DASHBOARD
# ─────────────────────────────────────────────
class ControlDashboard:
    def __init__(self, root):
        self.root        = root
        self.root.title("GRC360 — Control Report Dashboard")
        self.root.geometry("1480x830")
        self.root.minsize(1100, 660)
        self.root.configure(bg=C["bg"])
        self._controls   = []
        self._tp_map     = {}     # {control_id: [test_plan_name,...]}
        self._filtered   = []
        self._search_var = tk.StringVar()
        self._type_var   = tk.StringVar(value="All Types")
        self._cat_var    = tk.StringVar(value="All Categories")
        self._status_var = tk.StringVar(value="All Status")
        self._iid_map    = {}
        self._build_ui()
        self._load_data_async()

    # ── UI ────────────────────────────────────────────────
    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=C["sidebar"], height=56)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Frame(hdr, bg=C["accent"], width=4).pack(side="left", fill="y")
        dot = tk.Canvas(hdr, width=10, height=10, bg=C["sidebar"], highlightthickness=0)
        dot.create_oval(0, 0, 10, 10, fill=C["accent"], outline="")
        dot.pack(side="left", padx=(14,6), pady=23)
        tk.Label(hdr, text="GRC360", bg=C["sidebar"], fg=C["text_main"],
                 font=("Segoe UI", 15, "bold")).pack(side="left")
        tk.Label(hdr, text="  /  Control Report", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI", 11)).pack(side="left")
        self._status_lbl = tk.Label(hdr, text="⏳  Loading…",
                                    bg=C["sidebar"], fg=C["warning"],
                                    font=("Segoe UI", 9))
        self._status_lbl.pack(side="right", padx=18)
        tk.Button(hdr, text="↺  Refresh", font=("Segoe UI", 9, "bold"),
                  bg=C["accent"], fg="#FFFFFF", relief="flat", bd=0,
                  padx=12, pady=4, cursor="hand2",
                  activebackground="#059669", activeforeground="#FFFFFF",
                  command=self._load_data_async).pack(side="right", pady=14, padx=(0,8))

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=14, pady=10)

        self._quant  = QuantPanel(body)
        self._quant.pack(side="right", fill="y", padx=(10,0))

        self._detail = DetailPanel(body)
        self._detail.pack(side="left", fill="y", padx=(0,10))

        centre = tk.Frame(body, bg=C["bg"])
        centre.pack(side="left", fill="both", expand=True)

        self._cards_frame = tk.Frame(centre, bg=C["bg"])
        self._cards_frame.pack(fill="x", pady=(0,10))

        toolbar = tk.Frame(centre, bg=C["bg"])
        toolbar.pack(fill="x", pady=(0,6))
        sw = tk.Frame(toolbar, bg=C["input_bg"],
                      highlightbackground=C["card_border"], highlightthickness=1)
        sw.pack(side="left")
        tk.Label(sw, text="🔍", bg=C["input_bg"], fg=C["text_dim"],
                 font=("Segoe UI",10)).pack(side="left", padx=(8,4))
        tk.Entry(sw, textvariable=self._search_var, font=FONT_SEARCH,
                 bg=C["input_bg"], fg=C["input_fg"],
                 insertbackground=C["input_fg"], relief="flat", width=20).pack(
                     side="left", ipady=5, padx=(0,8))
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        for var, attr in [(self._type_var,   "_type_menu"),
                          (self._cat_var,    "_cat_menu"),
                          (self._status_var, "_status_menu")]:
            btn = tk.Menubutton(toolbar, textvariable=var, font=("Segoe UI",9),
                                bg=C["input_bg"], fg=C["text_main"], relief="flat",
                                highlightbackground=C["card_border"],
                                highlightthickness=1, padx=10, pady=5,
                                cursor="hand2", indicatoron=True)
            btn.pack(side="left", padx=(8,0))
            m = tk.Menu(btn, tearoff=0, bg=C["sidebar"], fg=C["text_main"],
                        activebackground=C["accent"], activeforeground="#FFFFFF")
            btn["menu"] = m
            setattr(self, attr, m)

        self._count_lbl = tk.Label(toolbar, text="", bg=C["bg"],
                                   fg=C["text_dim"], font=("Segoe UI",9))
        self._count_lbl.pack(side="right")

        self._table_frame = tk.Frame(centre, bg=C["bg"])
        self._table_frame.pack(fill="both", expand=True)
        self._build_table()

    def _build_table(self):
        for w in self._table_frame.winfo_children(): w.destroy()
        style = ttk.Style(); style.theme_use("clam")
        style.configure("CTL.Treeview",
                        background=C["row_even"], foreground=C["text_main"],
                        fieldbackground=C["row_even"], rowheight=30,
                        font=FONT_CELL, borderwidth=0)
        style.configure("CTL.Treeview.Heading",
                        background=C["sidebar"], foreground=C["text_dim"],
                        font=FONT_HEAD, relief="flat", borderwidth=0)
        style.map("CTL.Treeview",
                  background=[("selected", C["row_select"])],
                  foreground=[("selected", "#FFFFFF")])
        style.layout("CTL.Treeview", [("CTL.Treeview.treearea", {"sticky": "nswe"})])

        vis_cols   = ("control_id","control_name","linked_risk","risk_severity",
                      "control_type","control_category","status")
        col_widths = {
            "control_id":       50,
            "control_name":    175,
            "linked_risk":     175,
            "risk_severity":    90,
            "control_type":    100,
            "control_category":110,
            "status":           80,
        }
        col_labels = {
            "control_id":       "ID",
            "control_name":     "Control Name",
            "linked_risk":      "⚠️ Linked Risk",
            "risk_severity":    "Risk Severity",
            "control_type":     "Type",
            "control_category": "Category",
            "status":           "Status",
        }
        wrap = tk.Frame(self._table_frame, bg=C["bg"],
                        highlightbackground=C["card_border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(wrap, columns=vis_cols, show="headings",
                                  style="CTL.Treeview", selectmode="browse")
        for col in vis_cols:
            self.tree.heading(col, text=col_labels[col],
                              command=lambda c=col: self._sort_col(c))
            self.tree.column(col, width=col_widths[col], anchor="w",
                             stretch=(col == "control_name"))
        vsb = tk.Scrollbar(wrap, orient="vertical",   command=self.tree.yview,
                           bg=C["bg"], troughcolor=C["sidebar"])
        vsb.pack(side="right", fill="y")
        hsb = tk.Scrollbar(wrap, orient="horizontal", command=self.tree.xview,
                           bg=C["bg"], troughcolor=C["sidebar"])
        hsb.pack(side="bottom", fill="x")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.tag_configure("odd",  background=C["row_odd"])
        self.tree.tag_configure("even", background=C["row_even"])
        # colour-code severity in risk_severity column is textual — no tag trick needed
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self._sort_state = {}

    # ── Data flow ─────────────────────────────────────────
    def _sort_col(self, col):
        rev = self._sort_state.get(col, False)
        self._filtered.sort(key=lambda r: str(r.get(col) or ""), reverse=rev)
        self._sort_state[col] = not rev
        self._populate_table(self._filtered)

    def _load_data_async(self):
        self._status_lbl.config(text="⏳  Loading…", fg=C["warning"])
        threading.Thread(target=self._fetch_thread, daemon=True).start()

    def _fetch_thread(self):
        try:
            controls = fetch_controls_with_risks()
            tp_map   = fetch_test_plan_map()
            self.root.after(0, self._on_data_loaded, controls, tp_map, None)
        except Exception as e:
            self.root.after(0, self._on_data_loaded, [], {}, str(e))

    def _on_data_loaded(self, controls, tp_map, error):
        if error:
            self._status_lbl.config(text=f"❌  {error}", fg=C["danger"])
            messagebox.showerror("Error", f"Failed to load controls:\n{error}",
                                 parent=self.root)
            return

        self._controls = controls
        self._tp_map   = tp_map
        self._status_lbl.config(text=f"● {len(controls)} controls loaded",
                                fg=C["success"])

        all_types = sorted({r.get("control_type")     or "Unknown" for r in controls})
        all_cats  = sorted({r.get("control_category") or "Unknown" for r in controls})
        all_stats = sorted({(r.get("status") or "Unknown").capitalize() for r in controls})

        def _rebuild(menu, var, default, values, setter):
            menu.delete(0, "end")
            menu.add_command(label=default,
                             command=lambda d=default: var.set(d) or self._apply_filter())
            for v in values:
                menu.add_command(label=v, command=lambda x=v: setter(x))

        _rebuild(self._type_menu,   self._type_var,   "All Types",
                 all_types,   lambda x: self._type_var.set(x)   or self._apply_filter())
        _rebuild(self._cat_menu,    self._cat_var,     "All Categories",
                 all_cats,    lambda x: self._cat_var.set(x)    or self._apply_filter())
        _rebuild(self._status_menu, self._status_var, "All Status",
                 all_stats,   lambda x: self._status_var.set(x) or self._apply_filter())

        self._build_stat_cards()
        self._apply_filter()

    def _build_stat_cards(self):
        for w in self._cards_frame.winfo_children(): w.destroy()
        rows     = self._controls
        total    = len(rows)
        active   = sum(1 for r in rows if (r.get("status") or "").lower() == "active")
        inactive = sum(1 for r in rows if (r.get("status") or "").lower() == "inactive")
        linked_r = sum(1 for r in rows if r.get("risk_name"))
        linked_tp= sum(1 for r in rows if self._tp_map.get(r.get("control_id")))
        types_n  = len({r.get("control_type") for r in rows if r.get("control_type")})
        cats_n   = len({r.get("control_category") for r in rows if r.get("control_category")})
        for icon, lbl, val, color in [
            ("🛡️", "Total Controls",   total,     C["accent2"]),
            ("✅", "Active",            active,    C["success"]),
            ("🔴", "Inactive",          inactive,  C["danger"]),
            ("⚠️", "Linked to Risk",    linked_r,  C["warning"]),
            ("📋", "In Test Plans",     linked_tp, C["purple"]),
            ("🔧", "Control Types",     types_n,   C["sky"]),
            ("🗂️", "Categories",        cats_n,    C["teal"]),
        ]:
            StatCard(self._cards_frame, icon, lbl, val, color).pack(
                side="left", fill="x", expand=True, padx=(0,6))

    def _apply_filter(self):
        q      = self._search_var.get().lower().strip()
        ctype  = self._type_var.get()
        ccat   = self._cat_var.get()
        status = self._status_var.get()

        self._filtered = [
            r for r in self._controls
            if (ctype  in ("All", "All Types")
                or r.get("control_type") == ctype)
            and (ccat  in ("All", "All Categories")
                 or r.get("control_category") == ccat)
            and (status in ("All", "All Status")
                 or (r.get("status") or "").lower() == status.lower())
            and (not q
                 or any(q in str(v).lower() for v in r.values() if v))
        ]
        self._populate_table(self._filtered)
        self._count_lbl.config(
            text=f"Showing {len(self._filtered)} of {len(self._controls)}")
        self._quant.refresh(self._controls, self._filtered, self._tp_map)

    def _populate_table(self, rows):
        self.tree.delete(*self.tree.get_children())
        self._iid_map = {}
        for i, row in enumerate(rows):
            tag  = "even" if i % 2 == 0 else "odd"
            rname = row.get("risk_name") or "—"
            rsev  = (row.get("risk_severity") or "").capitalize()
            vals = (
                row.get("control_id")       or "",
                row.get("control_name")     or "",
                rname,
                rsev,
                row.get("control_type")     or "",
                row.get("control_category") or "",
                row.get("status")           or "",
            )
            iid = self.tree.insert("", "end", values=vals, tags=(tag,))
            self._iid_map[iid] = row
        self._detail._build_empty()

    def _on_select(self, _event):
        sel = self.tree.selection()
        if sel:
            row = self._iid_map.get(sel[0])
            if row:
                self._detail.show(row, self._tp_map)


# ─────────────────────────────────────────────
#  PUBLIC LAUNCHER
# ─────────────────────────────────────────────
def open_control_dashboard(win=None):
    if win is None:
        win = tk.Tk()
        ControlDashboard(win)
        win.mainloop()
    else:
        ControlDashboard(win)


if __name__ == "__main__":
    open_control_dashboard()
