"""
GRC360 — Process Report Dashboard  (Enhanced Edition)
• Quantitative Analytics panel on the right
• Rich detail panel on left when a row is selected
• Department / Frequency / Owner breakdown with %
Place in: ui/Dashboards/process_dashboard.py
Call:     open_process_dashboard(tk.Toplevel())
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
    "process_id", "process_name", "description",
    "department", "process_owner", "frequency",
    "triggers", "outcomes",
]
COL_LABELS = {
    "process_id":    "ID",
    "process_name":  "Process Name",
    "description":   "Description",
    "department":    "Department",
    "process_owner": "Owner",
    "frequency":     "Frequency",
    "triggers":      "Triggers",
    "outcomes":      "Outcomes",
}

# ─────────────────────────────────────────────
#  DESIGN TOKENS  (cobalt-blue)
# ─────────────────────────────────────────────
C = {
    "bg":          "#0F1923",
    "sidebar":     "#1E2A3A",
    "card":        "#1A2535",
    "card_border": "#2A3F58",
    "accent":      "#2563EB",
    "accent2":     "#3B82F6",
    "success":     "#10B981",
    "warning":     "#F59E0B",
    "danger":      "#EF4444",
    "purple":      "#8B5CF6",
    "teal":        "#2DD4BF",
    "text_main":   "#E2E8F0",
    "text_dim":    "#94A3B8",
    "text_tiny":   "#4A5568",
    "row_even":    "#131E2B",
    "row_odd":     "#1A2535",
    "row_select":  "#1D3461",
    "input_bg":    "#1E2A3A",
    "input_fg":    "#E2E8F0",
}

DEPT_COLORS = ["#3B82F6","#8B5CF6","#10B981","#F59E0B",
               "#EF4444","#2DD4BF","#F97316","#84CC16"]

FONT_HEAD   = ("Segoe UI", 9,  "bold")
FONT_CELL   = ("Segoe UI", 9)
FONT_CARD_N = ("Segoe UI", 22, "bold")
FONT_CARD_L = ("Segoe UI", 8)
FONT_SECT   = ("Segoe UI", 8,  "bold")
FONT_SEARCH = ("Segoe UI", 10)

# ─────────────────────────────────────────────
#  DATA FETCH
# ─────────────────────────────────────────────
def fetch_processes():
    payload = {"action": "select", "table": "processes", "columns": COLUMNS}
    return call_lambda(payload).get("records", [])


def _safe_total(d):
    return max(sum(d.values()), 1)

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
                         highlightthickness=1, width=265, **kw)
        self.pack_propagate(False)
        self._build_empty()

    def _clear(self):
        for w in self.winfo_children(): w.destroy()

    def _build_empty(self):
        self._clear()
        tk.Label(self, text="🧩\n\nSelect a process\nto view full details",
                 bg=C["sidebar"], fg=C["text_tiny"],
                 font=("Segoe UI", 10), justify="center").pack(expand=True)

    def show(self, row, all_depts):
        self._clear()
        idx   = all_depts.index(row.get("department","")) \
                if row.get("department","") in all_depts else 0
        color = DEPT_COLORS[idx % len(DEPT_COLORS)]

        hdr = tk.Frame(self, bg=color, padx=14, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"PRC-{row.get('process_id','')}",
                 bg=color, fg="#FFFFFF", font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(hdr, text=row.get("process_name",""), bg=color, fg="#FFFFFF",
                 font=("Segoe UI", 11, "bold"), wraplength=240,
                 justify="left").pack(anchor="w", pady=(4,0))

        # Scrollable body
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

        for lbl, key in [("🏢  Department",  "department"),
                          ("👤  Owner",       "process_owner"),
                          ("🔁  Frequency",   "frequency"),
                          ("⚡  Triggers",    "triggers"),
                          ("✅  Outcomes",    "outcomes")]:
            tk.Label(body, text=lbl, bg=C["sidebar"], fg=C["text_dim"],
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(8,0))
            tk.Label(body, text=row.get(key) or "—", bg=C["sidebar"],
                     fg=C["text_main"], font=("Segoe UI", 9),
                     wraplength=235, justify="left", anchor="w").pack(fill="x")
        tk.Frame(body, bg=C["card_border"], height=1).pack(fill="x", pady=10)
        tk.Label(body, text="📄  Description", bg=C["sidebar"], fg=C["text_dim"],
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, text=row.get("description") or "—", bg=C["sidebar"],
                 fg=C["text_main"], font=("Segoe UI", 9),
                 wraplength=235, justify="left", anchor="w").pack(fill="x", pady=(4,0))


# ─────────────────────────────────────────────
#  QUANT PANEL  (right)
# ─────────────────────────────────────────────
class QuantPanel(tk.Frame):
    """Right-side quantitative analytics panel with charts and KPIs."""
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["bg"], width=270, **kw)
        self.pack_propagate(False)
        # Title bar
        hdr = tk.Frame(self, bg=C["card_border"], height=32)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="📊  ANALYTICS", bg=C["card_border"],
                 fg=C["text_dim"], font=FONT_SECT).pack(side="left", padx=10, pady=7)
        self._body = None

    def refresh(self, processes, filtered):
        if self._body:
            self._body.destroy()

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
        self._body = outer

        total   = len(processes)
        visible = len(filtered)
        depts   = len({r.get("department") for r in processes if r.get("department")})
        owners  = len({r.get("process_owner") for r in processes if r.get("process_owner")})
        freqs   = len({r.get("frequency") for r in processes if r.get("frequency")})

        # ── KPI Summary Card ──────────────────────────────
        # sf = self._section(body, "KEY METRICS")
        # for lbl, val, clr in [
        #     ("Total Processes",   total,   C["accent2"]),
        #     ("Showing (filtered)",visible, C["teal"]),
        #     ("Departments",       depts,   C["purple"]),
        #     ("Unique Owners",     owners,  C["success"]),
        #     ("Frequency Types",   freqs,   C["warning"]),
        # ]:
        #     r = tk.Frame(sf, bg=C["card"])
        #     r.pack(fill="x", pady=2)
        #     tk.Label(r, text=lbl, bg=C["card"], fg=C["text_dim"],
        #              font=("Segoe UI", 8), anchor="w").pack(side="left")
        #     tk.Label(r, text=str(val), bg=C["card"], fg=clr,
        #              font=("Segoe UI", 10, "bold")).pack(side="right")

        # ── Dept chart ────────────────────────────────────
        dept_count = {}
        for p in processes:
            d = p.get("department") or "Unknown"
            dept_count[d] = dept_count.get(d, 0) + 1
        self._bar(body, "BY DEPARTMENT", dept_count, DEPT_COLORS, total)

        # ── Frequency chart ───────────────────────────────
        freq_count = {}
        for p in processes:
            f = p.get("frequency") or "Unknown"
            freq_count[f] = freq_count.get(f, 0) + 1
        self._bar(body, "BY FREQUENCY", freq_count,
                  ["#3B82F6","#8B5CF6","#10B981","#F59E0B","#EF4444"], total)

        # ── Owner load ────────────────────────────────────
        owner_count = {}
        for p in processes:
            o = p.get("process_owner") or "Unassigned"
            owner_count[o] = owner_count.get(o, 0) + 1
        top_owners = dict(sorted(owner_count.items(), key=lambda x: -x[1])[:7])
        self._bar(body, "OWNER LOAD (TOP 7)", top_owners, DEPT_COLORS, total)

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
        BAR_W = 120
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
class ProcessDashboard:
    def __init__(self, root):
        self.root        = root
        self.root.title("GRC360 — Process Report Dashboard")
        self.root.geometry("1100x700")
        self.root.minsize(1100, 660)
        self.root.configure(bg=C["bg"])
        self._processes  = []
        self._all_depts  = []
        self._filtered   = []
        self._search_var = tk.StringVar()
        self._dept_var   = tk.StringVar(value="All")
        self._iid_map    = {}
        self._build_ui()
        self._load_data_async()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self.root, bg=C["sidebar"], height=56)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Frame(hdr, bg=C["accent"], width=4).pack(side="left", fill="y")
        cv = tk.Canvas(hdr, width=10, height=10, bg=C["sidebar"], highlightthickness=0)
        cv.create_oval(0, 0, 10, 10, fill=C["accent"], outline="")
        cv.pack(side="left", padx=(14,6), pady=23)
        tk.Label(hdr, text="GRC360", bg=C["sidebar"], fg=C["text_main"],
                 font=("Segoe UI", 15, "bold")).pack(side="left")
        tk.Label(hdr, text="  /  Process Report", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI", 11)).pack(side="left")
        self._status_lbl = tk.Label(hdr, text="⏳  Loading…",
                                    bg=C["sidebar"], fg=C["warning"],
                                    font=("Segoe UI", 9))
        self._status_lbl.pack(side="right", padx=18)
        tk.Button(hdr, text="↺  Refresh", font=("Segoe UI", 9, "bold"),
                  bg=C["accent"], fg="#FFFFFF", relief="flat", bd=0,
                  padx=12, pady=4, cursor="hand2",
                  activebackground="#1D4ED8", activeforeground="#FFFFFF",
                  command=self._load_data_async).pack(side="right", pady=14, padx=(0,8))

        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=14, pady=10)

        # Right quant panel
        self._quant = QuantPanel(body)
        self._quant.pack(side="right", fill="y", padx=(10,0))

        # Left detail panel
        self._detail = DetailPanel(body)
        self._detail.pack(side="left", fill="y", padx=(0,10))

        # Centre
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
                 insertbackground=C["input_fg"], relief="flat", width=24).pack(
                     side="left", ipady=5, padx=(0,8))
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        dept_btn = tk.Menubutton(toolbar, textvariable=self._dept_var,
                                 font=("Segoe UI",9), bg=C["input_bg"],
                                 fg=C["text_main"], relief="flat",
                                 highlightbackground=C["card_border"],
                                 highlightthickness=1, padx=10, pady=5,
                                 cursor="hand2", indicatoron=True)
        dept_btn.pack(side="left", padx=(8,0))
        self._dept_menu = tk.Menu(dept_btn, tearoff=0, bg=C["sidebar"],
                                  fg=C["text_main"], activebackground=C["accent"],
                                  activeforeground="#FFFFFF")
        dept_btn["menu"] = self._dept_menu

        self._count_lbl = tk.Label(toolbar, text="", bg=C["bg"],
                                   fg=C["text_dim"], font=("Segoe UI",9))
        self._count_lbl.pack(side="right")

        self._table_frame = tk.Frame(centre, bg=C["bg"])
        self._table_frame.pack(fill="both", expand=True)
        self._build_table()

    def _build_table(self):
        for w in self._table_frame.winfo_children(): w.destroy()
        style = ttk.Style(); style.theme_use("clam")
        style.configure("PRC.Treeview",
                        background=C["row_even"], foreground=C["text_main"],
                        fieldbackground=C["row_even"], rowheight=30,
                        font=FONT_CELL, borderwidth=0)
        style.configure("PRC.Treeview.Heading",
                        background=C["sidebar"], foreground=C["text_dim"],
                        font=FONT_HEAD, relief="flat", borderwidth=0)
        style.map("PRC.Treeview",
                  background=[("selected", C["row_select"])],
                  foreground=[("selected", "#FFFFFF")])
        style.layout("PRC.Treeview", [("PRC.Treeview.treearea", {"sticky": "nswe"})])

        vis_cols   = ("process_id","process_name","department","process_owner",
                      "frequency","triggers","outcomes")
        col_widths = {"process_id":60,"process_name":190,"department":110,
                      "process_owner":120,"frequency":90,"triggers":120,"outcomes":120}
        wrap = tk.Frame(self._table_frame, bg=C["bg"],
                        highlightbackground=C["card_border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(wrap, columns=vis_cols, show="headings",
                                  style="PRC.Treeview", selectmode="browse")
        for col in vis_cols:
            self.tree.heading(col, text=COL_LABELS[col],
                              command=lambda c=col: self._sort_col(c))
            self.tree.column(col, width=col_widths[col], anchor="w",
                             stretch=(col == "process_name"))
        vsb = tk.Scrollbar(wrap, orient="vertical", command=self.tree.yview,
                           bg=C["bg"], troughcolor=C["sidebar"])
        vsb.pack(side="right", fill="y")
        hsb = tk.Scrollbar(wrap, orient="horizontal", command=self.tree.xview,
                           bg=C["bg"], troughcolor=C["sidebar"])
        hsb.pack(side="bottom", fill="x")
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
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
            rows = fetch_processes()
            self.root.after(0, self._on_data_loaded, rows, None)
        except Exception as e:
            self.root.after(0, self._on_data_loaded, [], str(e))

    def _on_data_loaded(self, rows, error):
        if error:
            self._status_lbl.config(text=f"❌  {error}", fg=C["danger"])
            messagebox.showerror("Error", f"Failed to load:\n{error}", parent=self.root)
            return
        self._processes = rows
        self._all_depts = sorted({r.get("department") or "Unknown" for r in rows})
        self._status_lbl.config(text=f"● {len(rows)} records", fg=C["success"])
        self._dept_menu.delete(0, "end")
        self._dept_menu.add_command(label="All", command=lambda: self._set_dept("All"))
        for d in self._all_depts:
            self._dept_menu.add_command(label=d, command=lambda x=d: self._set_dept(x))
        self._build_stat_cards()
        self._apply_filter()

    def _build_stat_cards(self):
        for w in self._cards_frame.winfo_children(): w.destroy()
        total  = len(self._processes)
        depts  = len(self._all_depts)
        owners = len({r.get("process_owner") for r in self._processes if r.get("process_owner")})
        freqs  = len({r.get("frequency") for r in self._processes if r.get("frequency")})
        for icon, lbl, val, color in [
            ("🧩", "Total Processes", total,  C["accent2"]),
            ("🏢", "Departments",     depts,  C["purple"]),
            ("👤", "Unique Owners",   owners, C["success"]),
            ("🔁", "Freq. Types",     freqs,  C["warning"]),
        ]:
            StatCard(self._cards_frame, icon, lbl, val, color).pack(
                side="left", fill="x", expand=True, padx=(0,8))

    def _set_dept(self, val):
        self._dept_var.set(val); self._apply_filter()

    def _apply_filter(self):
        q    = self._search_var.get().lower().strip()
        dept = self._dept_var.get()
        self._filtered = [
            r for r in self._processes
            if (dept == "All" or r.get("department") == dept)
            and (not q or any(q in str(v).lower() for v in r.values()))
        ]
        self._populate_table(self._filtered)
        self._count_lbl.config(
            text=f"Showing {len(self._filtered)} of {len(self._processes)}")
        self._quant.refresh(self._processes, self._filtered)

    def _populate_table(self, rows):
        self.tree.delete(*self.tree.get_children())
        self._iid_map = {}
        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            vals = (row.get("process_id") or "",
                    row.get("process_name") or "",
                    row.get("department") or "",
                    row.get("process_owner") or "",
                    row.get("frequency") or "",
                    (row.get("triggers") or "")[:45],
                    (row.get("outcomes") or "")[:45])
            iid = self.tree.insert("", "end", values=vals, tags=(tag,))
            self._iid_map[iid] = row
        self._detail._build_empty()

    def _on_select(self, _event):
        sel = self.tree.selection()
        if sel:
            row = self._iid_map.get(sel[0])
            if row: self._detail.show(row, self._all_depts)


# ─────────────────────────────────────────────
#  PUBLIC LAUNCHER
# ─────────────────────────────────────────────
def open_process_dashboard(win=None):
    if win is None:
        win = tk.Tk()
        ProcessDashboard(win)
        win.mainloop()
    else:
        ProcessDashboard(win)
