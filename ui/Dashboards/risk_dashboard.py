"""
GRC360 — Risk Report Dashboard  (Enhanced Edition)
• Quantitative Analytics panel on the right (severity, likelihood, status breakdown)
• Risk matrix heat indicator in KPI cards
• Rich detail panel on left showing mitigation & linked info
Place in: ui/Dashboards/risk_dashboard.py
Call:     open_risk_dashboard(tk.Toplevel())
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import threading

from connectors.lambda_mysql import call_lambda

# ─────────────────────────────────────────────
#  COLUMNS
# ─────────────────────────────────────────────
COLUMNS = [
    "risk_id", "risk_name", "description", "cause",
    "impact", "likelihood", "mitigation",
    "status", "owner", "severity", "created_at",
]
COL_LABELS = {
    "risk_id":     "ID",
    "risk_name":   "Risk Name",
    "description": "Description",
    "cause":       "Cause",
    "impact":      "Impact",
    "likelihood":  "Likelihood",
    "mitigation":  "Mitigation",
    "status":      "Status",
    "owner":       "Owner",
    "severity":    "Severity",
    "created_at":  "Created",
}

# ─────────────────────────────────────────────
#  DESIGN TOKENS  (orange / red risk theme)
# ─────────────────────────────────────────────
C = {
    "bg":          "#1A0F0A",
    "sidebar":     "#221208",
    "card":        "#2A1510",
    "card_border": "#4A2218",
    "accent":      "#F97316",
    "accent2":     "#FB923C",
    "success":     "#10B981",
    "warning":     "#F59E0B",
    "danger":      "#EF4444",
    "purple":      "#A78BFA",
    "sky":         "#38BDF8",
    "text_main":   "#FEF3C7",
    "text_dim":    "#D97706",
    "text_tiny":   "#6B3A1F",
    "row_even":    "#160C07",
    "row_odd":     "#2A1510",
    "row_select":  "#4A1E0A",
    "input_bg":    "#221208",
    "input_fg":    "#FEF3C7",
}

SEVERITY_COLORS = {
    "critical": "#EF4444",
    "high":     "#F97316",
    "medium":   "#F59E0B",
    "low":      "#10B981",
    "info":     "#38BDF8",
}
LIKELIHOOD_COLORS = {
    "certain":  "#EF4444",
    "likely":   "#F97316",
    "possible": "#F59E0B",
    "unlikely": "#10B981",
    "rare":     "#38BDF8",
}
STATUS_COLORS = {
    "open":        "#EF4444",
    "mitigated":   "#10B981",
    "accepted":    "#F59E0B",
    "closed":      "#38BDF8",
    "in progress": "#A78BFA",
    "reviewing":   "#FB923C",
}
OWNER_COLORS = ["#FB923C","#A78BFA","#38BDF8","#10B981","#F59E0B","#EF4444"]

FONT_HEAD   = ("Segoe UI", 9,  "bold")
FONT_CELL   = ("Segoe UI", 9)
FONT_CARD_N = ("Segoe UI", 22, "bold")
FONT_CARD_L = ("Segoe UI", 8)
FONT_SECT   = ("Segoe UI", 8,  "bold")
FONT_SEARCH = ("Segoe UI", 10)

# ─────────────────────────────────────────────
#  DATA FETCH
# ─────────────────────────────────────────────
def fetch_risks():
    payload = {"action": "select", "table": "risk", "columns": COLUMNS}
    return call_lambda(payload).get("records", [])


def severity_color(s):  return SEVERITY_COLORS.get((s or "").lower(), C["text_dim"])
def likelihood_color(s):return LIKELIHOOD_COLORS.get((s or "").lower(), C["text_dim"])
def status_color(s):    return STATUS_COLORS.get((s or "").lower(), C["text_dim"])

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
#  DETAIL PANEL  (left)
# ─────────────────────────────────────────────
class DetailPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["sidebar"],
                         highlightbackground=C["card_border"],
                         highlightthickness=1, width=280, **kw)
        self.pack_propagate(False)
        self._build_empty()

    def _clear(self):
        for w in self.winfo_children(): w.destroy()

    def _build_empty(self):
        self._clear()
        tk.Label(self, text="⚠️\n\nSelect a risk\nto view full details",
                 bg=C["sidebar"], fg=C["text_tiny"],
                 font=("Segoe UI", 10), justify="center").pack(expand=True)

    def show(self, row):
        self._clear()
        sev_col = severity_color(row.get("severity",""))
        hdr     = tk.Frame(self, bg=sev_col, padx=14, pady=10)
        hdr.pack(fill="x")
        top = tk.Frame(hdr, bg=sev_col)
        top.pack(fill="x")
        tk.Label(top, text=f"RSK-{row.get('risk_id','')}",
                 bg=sev_col, fg="#FFFFFF",
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        sc = status_color(row.get("status",""))
        pill = tk.Frame(top, bg=sc, padx=6, pady=1)
        pill.pack(side="right")
        tk.Label(pill, text=(row.get("status") or "—").capitalize(),
                 bg=sc, fg="#FFFFFF", font=("Segoe UI", 8, "bold")).pack()
        tk.Label(hdr, text=row.get("risk_name",""), bg=sev_col,
                 fg="#FFFFFF", font=("Segoe UI", 11, "bold"),
                 wraplength=250, justify="left").pack(anchor="w", pady=(4,0))

        # Severity + Likelihood badges
        pr = tk.Frame(hdr, bg=sev_col)
        pr.pack(anchor="w", pady=(6,0))
        lh_col = likelihood_color(row.get("likelihood",""))
        for txt, col in [
            (f"⚡ {(row.get('severity') or '—').upper()}", sev_col),
            (f"🎲 {(row.get('likelihood') or '—').capitalize()}", lh_col),
        ]:
            p = tk.Frame(pr, bg=col, padx=7, pady=2)
            p.pack(side="left", padx=(0,6))
            tk.Label(p, text=txt, bg=col, fg="#FFFFFF",
                     font=("Segoe UI", 8, "bold")).pack()

        # Scrollable body
        outer = tk.Frame(self, bg=C["sidebar"])
        outer.pack(fill="both", expand=True)
        cv = tk.Canvas(outer, bg=C["sidebar"], highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=cv.yview, width=6)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        cv.configure(yscrollcommand=sb.set)
        body = tk.Frame(cv, bg=C["sidebar"], padx=14, pady=8)
        win  = cv.create_window((0,0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(win, width=e.width))

        for lbl, key in [("👤  Owner",      "owner"),
                          ("💥  Impact",     "impact"),
                          ("🔍  Cause",      "cause")]:
            tk.Label(body, text=lbl, bg=C["sidebar"], fg=C["text_dim"],
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(7,0))
            tk.Label(body, text=row.get(key) or "—", bg=C["sidebar"],
                     fg=C["text_main"], font=("Segoe UI", 9),
                     wraplength=250, justify="left", anchor="w").pack(fill="x")
        tk.Frame(body, bg=C["card_border"], height=1).pack(fill="x", pady=8)
        for lbl, key in [("🛡️  Mitigation",  "mitigation"),
                          ("📄  Description", "description")]:
            tk.Label(body, text=lbl, bg=C["sidebar"], fg=C["text_dim"],
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(6,0))
            tk.Label(body, text=row.get(key) or "—", bg=C["sidebar"],
                     fg=C["text_main"], font=("Segoe UI", 9),
                     wraplength=250, justify="left", anchor="w").pack(fill="x")
        if row.get("created_at"):
            tk.Frame(body, bg=C["card_border"], height=1).pack(fill="x", pady=8)
            tk.Label(body, text="🕒  Created", bg=C["sidebar"], fg=C["text_dim"],
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x")
            tk.Label(body, text=str(row.get("created_at",""))[:19],
                     bg=C["sidebar"], fg=C["text_main"],
                     font=("Segoe UI", 9), anchor="w").pack(fill="x")


# ─────────────────────────────────────────────
#  QUANT PANEL  (right)
# ─────────────────────────────────────────────
class QuantPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["bg"], width=280, **kw)
        self.pack_propagate(False)
        hdr = tk.Frame(self, bg=C["card_border"], height=32)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="📊  RISK ANALYTICS", bg=C["card_border"],
                 fg=C["text_dim"], font=FONT_SECT).pack(side="left", padx=10, pady=7)
        self._body_frame = None

    def refresh(self, risks, filtered):
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

        total     = len(risks)
        visible   = len(filtered)
        open_r    = sum(1 for r in risks if (r.get("status") or "").lower() == "open")
        critical  = sum(1 for r in risks if (r.get("severity") or "").lower() == "critical")
        high      = sum(1 for r in risks if (r.get("severity") or "").lower() == "high")
        mitigated = sum(1 for r in risks if (r.get("status") or "").lower() == "mitigated")
        owners    = len({r.get("owner") for r in risks if r.get("owner")})

        # ── KPI Card ──────────────────────────────────────
        sf = self._section(body, "KEY METRICS")
        for lbl, val, clr in [
            ("Total Risks",         total,     C["accent2"]),
            ("Showing (filtered)",  visible,   C["sky"]),
            ("Open",                open_r,    C["danger"]),
            ("Critical Severity",   critical,  "#EF4444"),
            ("High Severity",       high,      C["accent"]),
            ("Mitigated",           mitigated, C["success"]),
            ("Unique Owners",       owners,    C["purple"]),
        ]:
            r = tk.Frame(sf, bg=C["card"])
            r.pack(fill="x", pady=2)
            tk.Label(r, text=lbl, bg=C["card"], fg=C["text_dim"],
                     font=("Segoe UI", 8), anchor="w").pack(side="left")
            tk.Label(r, text=str(val), bg=C["card"], fg=clr,
                     font=("Segoe UI", 10, "bold")).pack(side="right")

        # ── Severity breakdown ────────────────────────────
        sev_c = {}
        for r in risks:
            k = (r.get("severity") or "Unknown").capitalize()
            sev_c[k] = sev_c.get(k, 0) + 1
        self._bar(body, "BY SEVERITY", sev_c, SEVERITY_COLORS, total)

        # ── Likelihood breakdown ──────────────────────────
        lh_c = {}
        for r in risks:
            k = (r.get("likelihood") or "Unknown").capitalize()
            lh_c[k] = lh_c.get(k, 0) + 1
        self._bar(body, "BY LIKELIHOOD", lh_c, LIKELIHOOD_COLORS, total)

        # ── Status breakdown ──────────────────────────────
        st_c = {}
        for r in risks:
            k = (r.get("status") or "Unknown").capitalize()
            st_c[k] = st_c.get(k, 0) + 1
        self._bar(body, "BY STATUS", st_c, STATUS_COLORS, total)

        # ── Owner workload ────────────────────────────────
        ow_c = {}
        for r in risks:
            o = r.get("owner") or "Unassigned"
            ow_c[o] = ow_c.get(o, 0) + 1
        top_ow = dict(sorted(ow_c.items(), key=lambda x: -x[1])[:7])
        self._bar(body, "OWNER WORKLOAD (TOP 7)", top_ow, OWNER_COLORS, total)

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
        BAR_W = 118
        for i, (k, v) in enumerate(sorted(data_dict.items(), key=lambda x: -x[1])):
            if isinstance(colors, dict):
                clr = colors.get(k.lower(), OWNER_COLORS[i % len(OWNER_COLORS)])
            else:
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
class RiskDashboard:
    def __init__(self, root):
        self.root        = root
        self.root.title("GRC360 — Risk Report Dashboard")
        self.root.geometry("1480x830")
        self.root.minsize(1100, 660)
        self.root.configure(bg=C["bg"])
        self._risks      = []
        self._filtered   = []
        self._search_var = tk.StringVar()
        self._sev_var    = tk.StringVar(value="All")
        self._lh_var     = tk.StringVar(value="All")
        self._status_var = tk.StringVar(value="All")
        self._owner_var  = tk.StringVar(value="All")
        self._iid_map    = {}
        self._build_ui()
        self._load_data_async()

    def _build_ui(self):
        hdr = tk.Frame(self.root, bg=C["sidebar"], height=56)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Frame(hdr, bg=C["accent"], width=4).pack(side="left", fill="y")
        cv = tk.Canvas(hdr, width=10, height=10, bg=C["sidebar"], highlightthickness=0)
        cv.create_oval(0, 0, 10, 10, fill=C["accent"], outline="")
        cv.pack(side="left", padx=(14,6), pady=23)
        tk.Label(hdr, text="GRC360", bg=C["sidebar"], fg=C["text_main"],
                 font=("Segoe UI", 15, "bold")).pack(side="left")
        tk.Label(hdr, text="  /  Risk Report", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI", 11)).pack(side="left")
        self._status_lbl = tk.Label(hdr, text="⏳  Loading…",
                                    bg=C["sidebar"], fg=C["warning"],
                                    font=("Segoe UI", 9))
        self._status_lbl.pack(side="right", padx=18)
        tk.Button(hdr, text="↺  Refresh", font=("Segoe UI", 9, "bold"),
                  bg=C["accent"], fg="#FFFFFF", relief="flat", bd=0,
                  padx=12, pady=4, cursor="hand2",
                  activebackground="#EA580C", activeforeground="#FFFFFF",
                  command=self._load_data_async).pack(side="right", pady=14, padx=(0,8))

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=14, pady=10)

        self._quant = QuantPanel(body)
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

        for var, attr in [(self._sev_var,    "_sev_menu"),
                          (self._lh_var,     "_lh_menu"),
                          (self._status_var, "_status_menu"),
                          (self._owner_var,  "_owner_menu")]:
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
        style.configure("RSK.Treeview",
                        background=C["row_even"], foreground=C["text_main"],
                        fieldbackground=C["row_even"], rowheight=30,
                        font=FONT_CELL, borderwidth=0)
        style.configure("RSK.Treeview.Heading",
                        background=C["sidebar"], foreground=C["text_dim"],
                        font=FONT_HEAD, relief="flat", borderwidth=0)
        style.map("RSK.Treeview",
                  background=[("selected", C["row_select"])],
                  foreground=[("selected", "#FFFFFF")])
        style.layout("RSK.Treeview", [("RSK.Treeview.treearea", {"sticky": "nswe"})])

        vis_cols   = ("risk_id","risk_name","severity","likelihood","status","owner","cause","impact")
        col_widths = {"risk_id":55,"risk_name":190,"severity":90,
                      "likelihood":95,"status":95,"owner":120,"cause":110,"impact":110}
        wrap = tk.Frame(self._table_frame, bg=C["bg"],
                        highlightbackground=C["card_border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(wrap, columns=vis_cols, show="headings",
                                  style="RSK.Treeview", selectmode="browse")
        for col in vis_cols:
            self.tree.heading(col, text=COL_LABELS[col],
                              command=lambda c=col: self._sort_col(c))
            self.tree.column(col, width=col_widths[col], anchor="w",
                             stretch=(col == "risk_name"))
        vsb = tk.Scrollbar(wrap, orient="vertical", command=self.tree.yview,
                           bg=C["bg"], troughcolor=C["sidebar"])
        vsb.pack(side="right", fill="y")
        hsb = tk.Scrollbar(wrap, orient="horizontal", command=self.tree.xview,
                           bg=C["bg"], troughcolor=C["sidebar"])
        hsb.pack(side="bottom", fill="x")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        for sev, col in SEVERITY_COLORS.items():
            self.tree.tag_configure(f"sev_{sev}", foreground=col)
        self.tree.tag_configure("odd",  background=C["row_odd"])
        self.tree.tag_configure("even", background=C["row_even"])
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self._sort_state = {}

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
            rows = fetch_risks()
            self.root.after(0, self._on_data_loaded, rows, None)
        except Exception as e:
            self.root.after(0, self._on_data_loaded, [], str(e))

    def _on_data_loaded(self, rows, error):
        if error:
            self._status_lbl.config(text=f"❌  {error}", fg=C["danger"])
            messagebox.showerror("Error", f"Failed to load:\n{error}", parent=self.root)
            return
        self._risks = rows
        self._status_lbl.config(text=f"● {len(rows)} risks loaded", fg=C["success"])

        all_sevs   = sorted({(r.get("severity")   or "Unknown").capitalize() for r in rows})
        all_lhs    = sorted({(r.get("likelihood")  or "Unknown").capitalize() for r in rows})
        all_stats  = sorted({(r.get("status")      or "Unknown").capitalize() for r in rows})
        all_owners = sorted({r.get("owner") or "Unassigned" for r in rows})

        for menu, var, values in [
            (self._sev_menu,    self._sev_var,    all_sevs),
            (self._lh_menu,     self._lh_var,     all_lhs),
            (self._status_menu, self._status_var, all_stats),
            (self._owner_menu,  self._owner_var,  all_owners),
        ]:
            menu.delete(0, "end")
            menu.add_command(label="All",
                             command=lambda v=var: v.set("All") or self._apply_filter())
            for val in values:
                menu.add_command(label=val,
                                 command=lambda x=val, v=var: v.set(x) or self._apply_filter())

        self._build_stat_cards()
        self._apply_filter()

    def _build_stat_cards(self):
        for w in self._cards_frame.winfo_children(): w.destroy()
        total     = len(self._risks)
        open_r    = sum(1 for r in self._risks if (r.get("status") or "").lower() == "open")
        critical  = sum(1 for r in self._risks if (r.get("severity") or "").lower() == "critical")
        high      = sum(1 for r in self._risks if (r.get("severity") or "").lower() == "high")
        mitigated = sum(1 for r in self._risks if (r.get("status") or "").lower() == "mitigated")
        owners    = len({r.get("owner") for r in self._risks if r.get("owner")})
        for icon, lbl, val, color in [
            ("⚠️",  "Total Risks",  total,     C["accent2"]),
            ("🔴",  "Open",         open_r,    C["danger"]),
            ("🔥",  "Critical",     critical,  "#EF4444"),
            ("🟠",  "High",         high,      C["accent"]),
            ("✅",  "Mitigated",    mitigated, C["success"]),
            ("👤",  "Owners",       owners,    C["purple"]),
        ]:
            StatCard(self._cards_frame, icon, lbl, val, color).pack(
                side="left", fill="x", expand=True, padx=(0,8))

    def _apply_filter(self):
        q      = self._search_var.get().lower().strip()
        sev    = self._sev_var.get()
        lh     = self._lh_var.get()
        status = self._status_var.get()
        owner  = self._owner_var.get()
        self._filtered = [
            r for r in self._risks
            if (sev    == "All" or (r.get("severity")   or "").lower() == sev.lower())
            and (lh    == "All" or (r.get("likelihood") or "").lower() == lh.lower())
            and (status == "All" or (r.get("status")    or "").lower() == status.lower())
            and (owner  == "All" or (r.get("owner") or "Unassigned")   == owner)
            and (not q  or any(q in str(v).lower() for v in r.values()))
        ]
        self._populate_table(self._filtered)
        self._count_lbl.config(
            text=f"Showing {len(self._filtered)} of {len(self._risks)}")
        self._quant.refresh(self._risks, self._filtered)

    def _populate_table(self, rows):
        self.tree.delete(*self.tree.get_children())
        self._iid_map = {}
        for i, row in enumerate(rows):
            base    = "even" if i % 2 == 0 else "odd"
            sev_tag = f"sev_{(row.get('severity') or '').lower()}"
            vals = (row.get("risk_id") or "", row.get("risk_name") or "",
                    row.get("severity") or "", row.get("likelihood") or "",
                    row.get("status") or "", row.get("owner") or "",
                    (row.get("cause") or "")[:40],
                    (row.get("impact") or "")[:40])
            iid = self.tree.insert("", "end", values=vals, tags=(base, sev_tag))
            self._iid_map[iid] = row
        self._detail._build_empty()

    def _on_select(self, _event):
        sel = self.tree.selection()
        if sel:
            row = self._iid_map.get(sel[0])
            if row: self._detail.show(row)


# ─────────────────────────────────────────────
#  PUBLIC LAUNCHER
# ─────────────────────────────────────────────
def open_risk_dashboard(win=None):
    if win is None:
        win = tk.Tk()
        RiskDashboard(win)
        win.mainloop()
    else:
        RiskDashboard(win)


if __name__ == "__main__":
    open_risk_dashboard()
