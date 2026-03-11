"""
GRC360 — Risk Dashboard
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
#  DESIGN TOKENS  (orange/red theme)
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
FONT_CARD_N = ("Segoe UI", 26, "bold")
FONT_CARD_L = ("Segoe UI", 9)
FONT_SECT   = ("Segoe UI", 8,  "bold")
FONT_SEARCH = ("Segoe UI", 10)


# ─────────────────────────────────────────────
#  DATA FETCH
# ─────────────────────────────────────────────
def fetch_risks():
    payload = {"action": "select", "table": "risk", "columns": COLUMNS}
    response = call_lambda(payload)
    return response.get("records", [])


def severity_color(s):
    return SEVERITY_COLORS.get((s or "").lower(), C["text_dim"])

def likelihood_color(s):
    return LIKELIHOOD_COLORS.get((s or "").lower(), C["text_dim"])

def status_color(s):
    return STATUS_COLORS.get((s or "").lower(), C["text_dim"])


# ─────────────────────────────────────────────
#  WIDGETS
# ─────────────────────────────────────────────
class StatCard(tk.Frame):
    def __init__(self, parent, icon, label, value, accent, **kw):
        super().__init__(parent, bg=C["card"],
                         highlightbackground=accent, highlightthickness=1, **kw)
        tk.Frame(self, bg=accent, height=3).pack(side="bottom", fill="x")
        inner = tk.Frame(self, bg=C["card"], padx=14, pady=12)
        inner.pack(fill="both", expand=True)
        tk.Label(inner, text=icon, bg=C["card"], fg=accent,
                 font=("Segoe UI", 20)).pack(anchor="w")
        tk.Label(inner, text=str(value), bg=C["card"], fg=accent,
                 font=FONT_CARD_N).pack(anchor="w")
        tk.Label(inner, text=label.upper(), bg=C["card"],
                 fg=C["text_dim"], font=FONT_CARD_L).pack(anchor="w")


class DetailPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["sidebar"],
                         highlightbackground=C["card_border"],
                         highlightthickness=1, width=305, **kw)
        self.pack_propagate(False)
        self._build_empty()

    def _clear(self):
        for w in self.winfo_children(): w.destroy()

    def _build_empty(self):
        self._clear()
        tk.Label(self, text="⚠️\n\nSelect a row\nto view details",
                 bg=C["sidebar"], fg=C["text_tiny"],
                 font=("Segoe UI", 10), justify="center").pack(expand=True)

    def show(self, row):
        self._clear()
        sev_col = severity_color(row.get("severity", ""))
        hdr = tk.Frame(self, bg=sev_col, padx=14, pady=10)
        hdr.pack(fill="x")
        top = tk.Frame(hdr, bg=sev_col)
        top.pack(fill="x")
        tk.Label(top, text=f"RSK-{row.get('risk_id','')}",
                 bg=sev_col, fg="#FFFFFF",
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        sc = status_color(row.get("status", ""))
        pill = tk.Frame(top, bg=sc, padx=6, pady=1)
        pill.pack(side="right")
        tk.Label(pill, text=(row.get("status") or "—").capitalize(),
                 bg=sc, fg="#FFFFFF", font=("Segoe UI", 8, "bold")).pack()
        tk.Label(hdr, text=row.get("risk_name",""), bg=sev_col,
                 fg="#FFFFFF", font=("Segoe UI", 11, "bold"),
                 wraplength=270, justify="left").pack(anchor="w", pady=(4, 0))

        # Severity + Likelihood pills
        pr = tk.Frame(hdr, bg=sev_col)
        pr.pack(anchor="w", pady=(6, 0))
        lh_col = likelihood_color(row.get("likelihood",""))
        for txt, col in [
            (f"⚡ {(row.get('severity') or '—').upper()}",          sev_col),
            (f"🎲 {(row.get('likelihood') or '—').capitalize()}", lh_col),
        ]:
            p = tk.Frame(pr, bg=col, padx=7, pady=2)
            p.pack(side="left", padx=(0, 6))
            tk.Label(p, text=txt, bg=col, fg="#FFFFFF",
                     font=("Segoe UI", 8, "bold")).pack()

        body = tk.Frame(self, bg=C["sidebar"], padx=14, pady=8)
        body.pack(fill="both", expand=True)
        for lbl, key in [("👤  Owner",      "owner"),
                          ("💥  Impact",     "impact"),
                          ("🔍  Cause",      "cause")]:
            tk.Label(body, text=lbl, bg=C["sidebar"], fg=C["text_dim"],
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(7, 0))
            tk.Label(body, text=row.get(key) or "—", bg=C["sidebar"],
                     fg=C["text_main"], font=("Segoe UI", 9),
                     wraplength=270, justify="left", anchor="w").pack(fill="x")
        tk.Frame(body, bg=C["card_border"], height=1).pack(fill="x", pady=8)
        for lbl, key in [("🛡️  Mitigation",  "mitigation"),
                          ("📄  Description", "description")]:
            tk.Label(body, text=lbl, bg=C["sidebar"], fg=C["text_dim"],
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(6, 0))
            tk.Label(body, text=row.get(key) or "—", bg=C["sidebar"],
                     fg=C["text_main"], font=("Segoe UI", 9),
                     wraplength=270, justify="left", anchor="w").pack(fill="x")
        if row.get("created_at"):
            tk.Frame(body, bg=C["card_border"], height=1).pack(fill="x", pady=8)
            tk.Label(body, text=f"🕒  {row['created_at']}", bg=C["sidebar"],
                     fg=C["text_tiny"], font=("Segoe UI", 8), anchor="w").pack(fill="x")


class ChartsPanel(tk.Frame):
    def __init__(self, parent, risks, **kw):
        super().__init__(parent, bg=C["bg"], **kw)
        self._draw(risks)

    def _bar_block(self, title, data_dict, color_fn):
        f = tk.Frame(self, bg=C["card"], highlightbackground=C["card_border"],
                     highlightthickness=1, padx=14, pady=12)
        f.pack(fill="x", pady=(0, 10))
        tk.Label(f, text=title, bg=C["card"], fg=C["text_dim"],
                 font=FONT_SECT).pack(anchor="w")
        tk.Frame(f, bg=C["card_border"], height=1).pack(fill="x", pady=6)
        max_v = max(data_dict.values(), default=1)
        BAR_W = 148
        for i, (k, v) in enumerate(sorted(data_dict.items(), key=lambda x: -x[1])):
            color = color_fn(k, i)
            row = tk.Frame(f, bg=C["card"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=(k or "—")[:14], bg=C["card"], fg=C["text_main"],
                     font=("Segoe UI", 8), width=14, anchor="w").pack(side="left")
            cv = tk.Canvas(row, bg=C["card"], height=14, width=BAR_W, highlightthickness=0)
            cv.pack(side="left", padx=(4, 0))
            fw = int(BAR_W * v / max_v)
            cv.create_rectangle(0, 2, BAR_W, 12, fill=C["card_border"], outline="")
            if fw: cv.create_rectangle(0, 2, fw, 12, fill=color, outline="")
            tk.Label(row, text=str(v), bg=C["card"], fg=color,
                     font=("Segoe UI", 8, "bold"), width=3).pack(side="left", padx=4)

    def _draw(self, risks):
        # Status summary (big numbers)
        status_counts = {}
        for r in risks:
            s = (r.get("status") or "Unknown").capitalize()
            status_counts[s] = status_counts.get(s, 0) + 1
        sf = tk.Frame(self, bg=C["card"], highlightbackground=C["card_border"],
                      highlightthickness=1, padx=14, pady=12)
        sf.pack(fill="x", pady=(0, 10))
        tk.Label(sf, text="BY STATUS", bg=C["card"], fg=C["text_dim"],
                 font=FONT_SECT).pack(anchor="w")
        tk.Frame(sf, bg=C["card_border"], height=1).pack(fill="x", pady=6)
        row = tk.Frame(sf, bg=C["card"])
        row.pack(fill="x")
        for s, cnt in sorted(status_counts.items(), key=lambda x: -x[1]):
            col = status_color(s)
            cell = tk.Frame(row, bg=C["card"], padx=5)
            cell.pack(side="left")
            tk.Label(cell, text=str(cnt), bg=C["card"], fg=col,
                     font=("Segoe UI", 18, "bold")).pack()
            tk.Label(cell, text=s, bg=C["card"], fg=C["text_dim"],
                     font=("Segoe UI", 7)).pack()

        sev_counts = {}
        for r in risks:
            s = (r.get("severity") or "Unknown").capitalize()
            sev_counts[s] = sev_counts.get(s, 0) + 1
        self._bar_block("BY SEVERITY", sev_counts,
                        lambda k, i: SEVERITY_COLORS.get(k.lower(), C["text_dim"]))

        lh_counts = {}
        for r in risks:
            l = (r.get("likelihood") or "Unknown").capitalize()
            lh_counts[l] = lh_counts.get(l, 0) + 1
        self._bar_block("BY LIKELIHOOD", lh_counts,
                        lambda k, i: LIKELIHOOD_COLORS.get(k.lower(), C["text_dim"]))

        owner_counts = {}
        for r in risks:
            o = r.get("owner") or "Unassigned"
            owner_counts[o] = owner_counts.get(o, 0) + 1
        self._bar_block("BY OWNER", owner_counts,
                        lambda k, i: OWNER_COLORS[i % len(OWNER_COLORS)])


# ─────────────────────────────────────────────
#  MAIN DASHBOARD
# ─────────────────────────────────────────────
class RiskDashboard:
    def __init__(self, root):
        self.root        = root
        self.root.title("GRC360 — Risk Dashboard")
        self.root.geometry("1350x820")
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
        cv.pack(side="left", padx=(14, 6), pady=23)
        tk.Label(hdr, text="GRC360", bg=C["sidebar"], fg=C["text_main"],
                 font=("Segoe UI", 15, "bold")).pack(side="left")
        tk.Label(hdr, text="  /  Risk Dashboard", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI", 11)).pack(side="left")
        self._status_lbl = tk.Label(hdr, text="⏳  Loading…",
                                    bg=C["sidebar"], fg=C["warning"],
                                    font=("Segoe UI", 9))
        self._status_lbl.pack(side="right", padx=18)
        tk.Button(hdr, text="↺  Refresh", font=("Segoe UI", 9, "bold"),
                  bg=C["accent"], fg="#FFFFFF", relief="flat", bd=0,
                  padx=12, pady=4, cursor="hand2",
                  activebackground="#EA580C", activeforeground="#FFFFFF",
                  command=self._load_data_async).pack(side="right", pady=14, padx=(0, 8))

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=12)
        self._left = tk.Frame(body, bg=C["bg"])
        self._left.pack(side="left", fill="both", expand=True)
        self._detail = DetailPanel(body)
        self._detail.pack(side="right", fill="y", padx=(12, 0))

        self._cards_frame = tk.Frame(self._left, bg=C["bg"])
        self._cards_frame.pack(fill="x", pady=(0, 12))

        toolbar = tk.Frame(self._left, bg=C["bg"])
        toolbar.pack(fill="x", pady=(0, 8))
        sw = tk.Frame(toolbar, bg=C["input_bg"],
                      highlightbackground=C["card_border"], highlightthickness=1)
        sw.pack(side="left")
        tk.Label(sw, text="🔍", bg=C["input_bg"], fg=C["text_dim"],
                 font=("Segoe UI", 10)).pack(side="left", padx=(8, 4))
        tk.Entry(sw, textvariable=self._search_var, font=FONT_SEARCH,
                 bg=C["input_bg"], fg=C["input_fg"],
                 insertbackground=C["input_fg"], relief="flat", width=24).pack(
                     side="left", ipady=5, padx=(0, 8))
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        for var, attr in [(self._sev_var,    "_sev_menu"),
                          (self._lh_var,     "_lh_menu"),
                          (self._status_var, "_status_menu"),
                          (self._owner_var,  "_owner_menu")]:
            btn = tk.Menubutton(toolbar, textvariable=var, font=("Segoe UI", 9),
                                bg=C["input_bg"], fg=C["text_main"], relief="flat",
                                highlightbackground=C["card_border"],
                                highlightthickness=1, padx=10, pady=5,
                                cursor="hand2", indicatoron=True)
            btn.pack(side="left", padx=(8, 0))
            m = tk.Menu(btn, tearoff=0, bg=C["sidebar"], fg=C["text_main"],
                        activebackground=C["accent"], activeforeground="#FFFFFF")
            btn["menu"] = m
            setattr(self, attr, m)

        self._count_lbl = tk.Label(toolbar, text="", bg=C["bg"],
                                   fg=C["text_dim"], font=("Segoe UI", 9))
        self._count_lbl.pack(side="right")

        split = tk.Frame(self._left, bg=C["bg"])
        split.pack(fill="both", expand=True)
        self._table_frame = tk.Frame(split, bg=C["bg"])
        self._table_frame.pack(side="left", fill="both", expand=True)

        co = tk.Frame(split, bg=C["bg"], width=250)
        co.pack(side="right", fill="y", padx=(10, 0))
        co.pack_propagate(False)
        c_cv = tk.Canvas(co, bg=C["bg"], highlightthickness=0)
        c_cv.pack(side="left", fill="both", expand=True)
        c_sb = tk.Scrollbar(co, orient="vertical", command=c_cv.yview)
        c_sb.pack(side="right", fill="y")
        c_cv.configure(yscrollcommand=c_sb.set)
        self._charts_inner = tk.Frame(c_cv, bg=C["bg"])
        cwin = c_cv.create_window((0, 0), window=self._charts_inner, anchor="nw")
        self._charts_inner.bind("<Configure>",
            lambda e: c_cv.configure(scrollregion=c_cv.bbox("all")))
        c_cv.bind("<Configure>", lambda e: c_cv.itemconfig(cwin, width=e.width))
        self._c_canvas = c_cv
        self._build_table()

    def _build_table(self):
        for w in self._table_frame.winfo_children(): w.destroy()
        style = ttk.Style(); style.theme_use("clam")
        style.configure("RSK.Treeview",
                        background=C["row_even"], foreground=C["text_main"],
                        fieldbackground=C["row_even"], rowheight=28,
                        font=FONT_CELL, borderwidth=0)
        style.configure("RSK.Treeview.Heading",
                        background=C["sidebar"], foreground=C["text_dim"],
                        font=FONT_HEAD, relief="flat", borderwidth=0)
        style.map("RSK.Treeview",
                  background=[("selected", C["row_select"])],
                  foreground=[("selected", "#FFFFFF")])
        style.layout("RSK.Treeview", [("RSK.Treeview.treearea", {"sticky": "nswe"})])

        vis_cols   = ("risk_id","risk_name","severity","likelihood","status","owner")
        col_widths = {"risk_id":55,"risk_name":210,"severity":90,
                      "likelihood":95,"status":95,"owner":120}
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
        self.tree.configure(yscrollcommand=vsb.set)
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
            messagebox.showerror("Error", f"Failed to load risks:\n{error}",
                                 parent=self.root)
            return
        self._risks = rows
        self._status_lbl.config(text=f"● {len(rows)} risks loaded", fg=C["success"])

        all_sevs   = sorted({(r.get("severity")   or "Unknown").capitalize() for r in rows})
        all_lhs    = sorted({(r.get("likelihood") or "Unknown").capitalize() for r in rows})
        all_stats  = sorted({(r.get("status")     or "Unknown").capitalize() for r in rows})
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
        self._refresh_charts()

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
                side="left", fill="x", expand=True, padx=(0, 8))

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

    def _populate_table(self, rows):
        self.tree.delete(*self.tree.get_children())
        self._iid_map = {}
        for i, row in enumerate(rows):
            base    = "even" if i % 2 == 0 else "odd"
            sev_tag = f"sev_{(row.get('severity') or '').lower()}"
            vals = (row.get("risk_id") or "", row.get("risk_name") or "",
                    row.get("severity") or "", row.get("likelihood") or "",
                    row.get("status") or "", row.get("owner") or "")
            iid = self.tree.insert("", "end", values=vals, tags=(base, sev_tag))
            self._iid_map[iid] = row
        self._detail._build_empty()

    def _refresh_charts(self):
        for w in self._charts_inner.winfo_children(): w.destroy()
        ChartsPanel(self._charts_inner, self._risks).pack(fill="both", expand=True)
        self._c_canvas.update_idletasks()
        self._c_canvas.configure(scrollregion=self._c_canvas.bbox("all"))

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
    else:
        RiskDashboard(win)
