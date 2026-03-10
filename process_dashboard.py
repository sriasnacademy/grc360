"""
GRC360 — Process Dashboard
Drop this file into your project root (alongside main.py) and run it directly,
OR call  open_process_dashboard(parent_window)  from mainform.py.

Requires:  pymysql  (already in your requirements.txt)
"""

import sys, os
sys.path.append(os.path.dirname(__file__))

import tkinter as tk
from tkinter import ttk, messagebox
import pymysql
import threading

# ─────────────────────────────────────────────
#  DB CONFIG  (reused from mysqldb_engine.py)
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":        "srv840.hstgr.io",
    "user":        "u567123576_grcdevuser",
    "password":    "DevStart@26",
    "database":    "u567123576_grc360",
    "charset":     "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
    "port":        3306,
    "autocommit":  True,
    "connect_timeout": 10,
}

COLUMNS = [
    "process_id", "process_name", "description",
    "department", "process_owner", "frequency",
    "triggers",   "outcomes",
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
#  DESIGN TOKENS  (mirrors mainform.py palette)
# ─────────────────────────────────────────────
C = {
    "bg":           "#0F1923",
    "sidebar":      "#1E2A3A",
    "card":         "#1A2535",
    "card_border":  "#2A3F58",
    "accent":       "#2563EB",
    "accent2":      "#3B82F6",
    "success":      "#10B981",
    "warning":      "#F59E0B",
    "danger":       "#EF4444",
    "purple":       "#8B5CF6",
    "text_main":    "#E2E8F0",
    "text_dim":     "#94A3B8",
    "text_tiny":    "#64748B",
    "row_even":     "#131E2B",
    "row_odd":      "#1A2535",
    "row_hover":    "#253447",
    "row_select":   "#1D3461",
    "divider":      "#1E2A3A",
    "input_bg":     "#1E2A3A",
    "input_fg":     "#E2E8F0",
    "scrollbar":    "#2A3F58",
    "tag_it":       "#1A3254",
    "tag_fin":      "#1A2E1A",
    "tag_hr":       "#2E1A2E",
    "tag_risk":     "#2E1A1A",
    "tag_comp":     "#1A2E2E",
}

FREQ_COLORS = {
    "Monthly":   C["accent2"],
    "Quarterly": C["purple"],
    "Annual":    C["success"],
    "Weekly":    C["warning"],
    "As needed": C["danger"],
}

DEPT_COLORS = [C["accent2"], C["purple"], C["success"], C["warning"],
               C["danger"], "#06B6D4", "#F97316", "#84CC16"]

FONT_TITLE  = ("Segoe UI", 18, "bold")
FONT_SUB    = ("Segoe UI", 8,  "bold")
FONT_CARD_N = ("Segoe UI", 26, "bold")
FONT_CARD_L = ("Segoe UI", 9)
FONT_HEAD   = ("Segoe UI", 9,  "bold")
FONT_CELL   = ("Segoe UI", 9)
FONT_BADGE  = ("Segoe UI", 8,  "bold")
FONT_DETAIL = ("Segoe UI", 10)
FONT_DETAIL_B = ("Segoe UI", 10, "bold")
FONT_SEARCH = ("Segoe UI", 10)
FONT_STATUS = ("Segoe UI", 9)


# ─────────────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────────────
def fetch_processes():
    """Return list[dict] from MySQL processes table."""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cols = ", ".join(COLUMNS)
            cur.execute(f"SELECT {cols} FROM processes")
            return cur.fetchall()
    finally:
        conn.close()


def dept_color(dept: str, all_depts: list) -> str:
    try:
        idx = all_depts.index(dept) % len(DEPT_COLORS)
    except ValueError:
        idx = 0
    return DEPT_COLORS[idx]


def freq_color(freq: str) -> str:
    return FREQ_COLORS.get(freq, C["text_dim"])


def make_bar(canvas, x, y, w, h, value, max_val, color, label=""):
    """Draw a horizontal bar on a Canvas widget."""
    filled = int(w * (value / max_val)) if max_val else 0
    canvas.create_rectangle(x, y, x + w, y + h,
                             fill=C["card_border"], outline="", width=0)
    if filled:
        canvas.create_rectangle(x, y, x + filled, y + h,
                                 fill=color, outline="", width=0)
    if label:
        canvas.create_text(x + w + 6, y + h // 2,
                           text=str(value), fill=C["text_dim"],
                           font=("Segoe UI", 8), anchor="w")


# ─────────────────────────────────────────────────────
#  STAT CARD  widget
# ─────────────────────────────────────────────────────
class StatCard(tk.Frame):
    def __init__(self, parent, icon, label, value, accent, **kw):
        super().__init__(parent, bg=C["card"],
                         highlightbackground=accent,
                         highlightthickness=1, **kw)
        # accent bottom bar
        tk.Frame(self, bg=accent, height=3).pack(side="bottom", fill="x")

        inner = tk.Frame(self, bg=C["card"], padx=14, pady=12)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text=icon, bg=C["card"], fg=accent,
                 font=("Segoe UI", 20)).pack(anchor="w")
        tk.Label(inner, text=str(value), bg=C["card"], fg=accent,
                 font=FONT_CARD_N).pack(anchor="w")
        tk.Label(inner, text=label.upper(), bg=C["card"], fg=C["text_dim"],
                 font=FONT_CARD_L).pack(anchor="w")


# ─────────────────────────────────────────────────────
#  DETAIL PANEL  (right-side drawer)
# ─────────────────────────────────────────────────────
class DetailPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["sidebar"],
                         highlightbackground=C["card_border"],
                         highlightthickness=1, width=300, **kw)
        self.pack_propagate(False)
        self._build_empty()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _build_empty(self):
        self._clear()
        tk.Label(self, text="Select a row\nto view details",
                 bg=C["sidebar"], fg=C["text_tiny"],
                 font=("Segoe UI", 10), justify="center").pack(expand=True)

    def show(self, row: dict, all_depts: list):
        self._clear()
        # header strip
        dc = dept_color(row.get("department", ""), all_depts)
        hdr = tk.Frame(self, bg=dc, padx=14, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text=row.get("process_id", ""),
                 bg=dc, fg="#FFFFFF",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(hdr, text=row.get("process_name", ""),
                 bg=dc, fg="#FFFFFF",
                 font=("Segoe UI", 12, "bold"),
                 wraplength=270, justify="left").pack(anchor="w")

        body = tk.Frame(self, bg=C["sidebar"], padx=14, pady=10)
        body.pack(fill="both", expand=True)

        fields = [
            ("🏢 Department",   "department"),
            ("👤 Owner",        "process_owner"),
            ("🔁 Frequency",    "frequency"),
            ("⚡ Triggers",     "triggers"),
            ("✅ Outcomes",     "outcomes"),
        ]
        for lbl, key in fields:
            tk.Label(body, text=lbl, bg=C["sidebar"],
                     fg=C["text_dim"], font=("Segoe UI", 8, "bold"),
                     anchor="w").pack(fill="x", pady=(8, 0))
            val = row.get(key) or "—"
            tk.Label(body, text=val, bg=C["sidebar"],
                     fg=C["text_main"], font=("Segoe UI", 9),
                     wraplength=265, justify="left",
                     anchor="w").pack(fill="x")

        # description
        tk.Frame(body, bg=C["card_border"], height=1).pack(fill="x", pady=10)
        tk.Label(body, text="📄 Description", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI", 8, "bold"),
                 anchor="w").pack(fill="x")
        tk.Label(body, text=row.get("description") or "—",
                 bg=C["sidebar"], fg=C["text_main"],
                 font=("Segoe UI", 9), wraplength=265,
                 justify="left", anchor="w").pack(fill="x", pady=(4, 0))


# ─────────────────────────────────────────────────────
#  CHARTS  panel (department + frequency bars)
# ─────────────────────────────────────────────────────
class ChartsPanel(tk.Frame):
    def __init__(self, parent, processes, all_depts, **kw):
        super().__init__(parent, bg=C["bg"], **kw)
        self._draw(processes, all_depts)

    def _draw(self, processes, all_depts):
        # ── Dept breakdown ──
        dept_count = {}
        for p in processes:
            d = p.get("department") or "Unknown"
            dept_count[d] = dept_count.get(d, 0) + 1
        max_d = max(dept_count.values(), default=1)

        dept_frame = tk.Frame(self, bg=C["card"],
                              highlightbackground=C["card_border"],
                              highlightthickness=1, padx=14, pady=12)
        dept_frame.pack(fill="x", padx=0, pady=(0, 10))

        tk.Label(dept_frame, text="BY DEPARTMENT", bg=C["card"],
                 fg=C["text_dim"], font=FONT_CARD_L).pack(anchor="w")
        tk.Frame(dept_frame, bg=C["card_border"], height=1).pack(fill="x", pady=6)

        BAR_W = 160
        for i, (dep, cnt) in enumerate(sorted(dept_count.items(),
                                              key=lambda x: -x[1])):
            row = tk.Frame(dept_frame, bg=C["card"])
            row.pack(fill="x", pady=2)
            color = DEPT_COLORS[i % len(DEPT_COLORS)]

            tk.Label(row, text=dep, bg=C["card"], fg=C["text_main"],
                     font=("Segoe UI", 9), width=16,
                     anchor="w").pack(side="left")

            cv = tk.Canvas(row, bg=C["card"], height=14,
                           width=BAR_W, highlightthickness=0)
            cv.pack(side="left", padx=(4, 0))
            fill_w = int(BAR_W * cnt / max_d)
            cv.create_rectangle(0, 2, BAR_W, 12,
                                 fill=C["card_border"], outline="")
            if fill_w:
                cv.create_rectangle(0, 2, fill_w, 12,
                                     fill=color, outline="")

            tk.Label(row, text=str(cnt), bg=C["card"],
                     fg=color, font=("Segoe UI", 8, "bold"),
                     width=3).pack(side="left", padx=4)

        # ── Frequency breakdown ──
        freq_count = {}
        for p in processes:
            f = p.get("frequency") or "Unknown"
            freq_count[f] = freq_count.get(f, 0) + 1
        max_f = max(freq_count.values(), default=1)

        freq_frame = tk.Frame(self, bg=C["card"],
                              highlightbackground=C["card_border"],
                              highlightthickness=1, padx=14, pady=12)
        freq_frame.pack(fill="x", padx=0)

        tk.Label(freq_frame, text="BY FREQUENCY", bg=C["card"],
                 fg=C["text_dim"], font=FONT_CARD_L).pack(anchor="w")
        tk.Frame(freq_frame, bg=C["card_border"], height=1).pack(fill="x", pady=6)

        for freq, cnt in sorted(freq_count.items(), key=lambda x: -x[1]):
            row = tk.Frame(freq_frame, bg=C["card"])
            row.pack(fill="x", pady=2)
            color = FREQ_COLORS.get(freq, C["text_dim"])

            tk.Label(row, text=freq, bg=C["card"], fg=C["text_main"],
                     font=("Segoe UI", 9), width=16,
                     anchor="w").pack(side="left")

            cv = tk.Canvas(row, bg=C["card"], height=14,
                           width=BAR_W, highlightthickness=0)
            cv.pack(side="left", padx=(4, 0))
            fill_w = int(BAR_W * cnt / max_f)
            cv.create_rectangle(0, 2, BAR_W, 12,
                                 fill=C["card_border"], outline="")
            if fill_w:
                cv.create_rectangle(0, 2, fill_w, 12,
                                     fill=color, outline="")

            tk.Label(row, text=str(cnt), bg=C["card"],
                     fg=color, font=("Segoe UI", 8, "bold"),
                     width=3).pack(side="left", padx=4)


# ─────────────────────────────────────────────────────
#  MAIN DASHBOARD
# ─────────────────────────────────────────────────────
class ProcessDashboard:

    def __init__(self, root):
        self.root = root
        self.root.title("GRC360 — Process Dashboard")
        self.root.geometry("1280x780")
        self.root.minsize(1000, 620)
        self.root.configure(bg=C["bg"])

        self._processes     = []
        self._all_depts     = []
        self._filtered      = []
        self._search_var    = tk.StringVar()
        self._dept_var      = tk.StringVar(value="All")
        self._selected_row  = None

        self._build_ui()
        self._load_data_async()

    # ── UI skeleton ──────────────────────────────────
    def _build_ui(self):
        # ── Header bar ──
        hdr = tk.Frame(self.root, bg=C["sidebar"], height=56)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        tk.Frame(hdr, bg=C["accent"], width=4).pack(side="left", fill="y")
        dot_cv = tk.Canvas(hdr, width=10, height=10, bg=C["sidebar"],
                           highlightthickness=0)
        dot_cv.create_oval(0, 0, 10, 10, fill=C["accent"], outline="")
        dot_cv.pack(side="left", padx=(14, 6), pady=23)

        tk.Label(hdr, text="GRC360", bg=C["sidebar"], fg=C["text_main"],
                 font=("Segoe UI", 15, "bold")).pack(side="left")
        tk.Label(hdr, text="  /  Process Dashboard",
                 bg=C["sidebar"], fg=C["text_dim"],
                 font=("Segoe UI", 11)).pack(side="left")

        self._status_lbl = tk.Label(hdr, text="⏳  Loading…",
                                    bg=C["sidebar"], fg=C["warning"],
                                    font=FONT_STATUS)
        self._status_lbl.pack(side="right", padx=18)

        # refresh button
        tk.Button(hdr, text="↺  Refresh", font=("Segoe UI", 9, "bold"),
                  bg=C["accent"], fg="#FFFFFF", relief="flat", bd=0,
                  padx=12, pady=4, cursor="hand2",
                  activebackground="#1D4ED8", activeforeground="#FFFFFF",
                  command=self._load_data_async).pack(side="right", pady=14, padx=(0, 8))

        # ── Body: left content + right detail panel ──
        body = tk.Frame(self.root, bg=C["bg"])
        body.pack(fill="both", expand=True, padx=16, pady=12)

        self._left  = tk.Frame(body, bg=C["bg"])
        self._left.pack(side="left", fill="both", expand=True)

        self._detail = DetailPanel(body)
        self._detail.pack(side="right", fill="y", padx=(12, 0))

        # ── Stat cards row ──
        self._cards_frame = tk.Frame(self._left, bg=C["bg"])
        self._cards_frame.pack(fill="x", pady=(0, 12))

        # ── Toolbar: search + filter ──
        toolbar = tk.Frame(self._left, bg=C["bg"])
        toolbar.pack(fill="x", pady=(0, 8))

        search_wrap = tk.Frame(toolbar,
                               bg=C["input_bg"],
                               highlightbackground=C["card_border"],
                               highlightthickness=1)
        search_wrap.pack(side="left")
        tk.Label(search_wrap, text="🔍", bg=C["input_bg"],
                 fg=C["text_dim"], font=("Segoe UI", 10)).pack(side="left", padx=(8, 4))
        tk.Entry(search_wrap, textvariable=self._search_var,
                 font=FONT_SEARCH, bg=C["input_bg"],
                 fg=C["input_fg"], insertbackground=C["input_fg"],
                 relief="flat", width=28).pack(side="left", ipady=5, padx=(0, 8))
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        self._dept_menu_btn = tk.Menubutton(
            toolbar, textvariable=self._dept_var,
            font=("Segoe UI", 9), bg=C["input_bg"],
            fg=C["text_main"], relief="flat",
            highlightbackground=C["card_border"],
            highlightthickness=1,
            padx=10, pady=5, cursor="hand2",
            indicatoron=True)
        self._dept_menu_btn.pack(side="left", padx=(8, 0))
        self._dept_menu = tk.Menu(self._dept_menu_btn, tearoff=0,
                                  bg=C["sidebar"], fg=C["text_main"],
                                  activebackground=C["accent"],
                                  activeforeground="#FFFFFF")
        self._dept_menu_btn["menu"] = self._dept_menu

        self._count_lbl = tk.Label(toolbar, text="",
                                   bg=C["bg"], fg=C["text_dim"],
                                   font=("Segoe UI", 9))
        self._count_lbl.pack(side="right")

        # ── Main split: table + charts ──
        split = tk.Frame(self._left, bg=C["bg"])
        split.pack(fill="both", expand=True)

        # table area
        self._table_frame = tk.Frame(split, bg=C["bg"])
        self._table_frame.pack(side="left", fill="both", expand=True)

        # charts area  (fixed width, scrollable)
        charts_outer = tk.Frame(split, bg=C["bg"], width=230)
        charts_outer.pack(side="right", fill="y", padx=(10, 0))
        charts_outer.pack_propagate(False)

        c_canvas = tk.Canvas(charts_outer, bg=C["bg"],
                             highlightthickness=0, width=218)
        c_canvas.pack(side="left", fill="both", expand=True)
        c_sb = tk.Scrollbar(charts_outer, orient="vertical",
                            command=c_canvas.yview)
        c_sb.pack(side="right", fill="y")
        c_canvas.configure(yscrollcommand=c_sb.set)

        self._charts_inner = tk.Frame(c_canvas, bg=C["bg"])
        cwin = c_canvas.create_window((0, 0), window=self._charts_inner,
                                       anchor="nw")
        self._charts_inner.bind("<Configure>",
            lambda e: c_canvas.configure(scrollregion=c_canvas.bbox("all")))
        c_canvas.bind("<Configure>",
            lambda e: c_canvas.itemconfig(cwin, width=e.width))

        self._c_canvas = c_canvas

        # ── Build the Treeview ──
        self._build_table()

    # ── Treeview ─────────────────────────────────────
    def _build_table(self):
        for w in self._table_frame.winfo_children():
            w.destroy()

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("GRC.Treeview",
                        background=C["row_even"],
                        foreground=C["text_main"],
                        fieldbackground=C["row_even"],
                        rowheight=28,
                        font=FONT_CELL,
                        borderwidth=0)
        style.configure("GRC.Treeview.Heading",
                        background=C["sidebar"],
                        foreground=C["text_dim"],
                        font=FONT_HEAD,
                        relief="flat",
                        borderwidth=0)
        style.map("GRC.Treeview",
                  background=[("selected", C["row_select"])],
                  foreground=[("selected", "#FFFFFF")])
        style.layout("GRC.Treeview", [("GRC.Treeview.treearea", {"sticky": "nswe"})])

        vis_cols = ("process_id", "process_name", "department",
                    "process_owner", "frequency")
        col_widths = {
            "process_id":    80,
            "process_name":  190,
            "department":    120,
            "process_owner": 130,
            "frequency":     90,
        }

        wrap = tk.Frame(self._table_frame, bg=C["bg"],
                        highlightbackground=C["card_border"],
                        highlightthickness=1)
        wrap.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(wrap, columns=vis_cols,
                                  show="headings",
                                  style="GRC.Treeview",
                                  selectmode="browse")

        for col in vis_cols:
            self.tree.heading(col, text=COL_LABELS[col],
                              command=lambda c=col: self._sort_col(c))
            self.tree.column(col, width=col_widths[col],
                             anchor="w", stretch=(col == "process_name"))

        vsb = tk.Scrollbar(wrap, orient="vertical",
                           command=self.tree.yview, bg=C["bg"],
                           troughcolor=C["sidebar"])
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)

        self.tree.tag_configure("odd",  background=C["row_odd"])
        self.tree.tag_configure("even", background=C["row_even"])

        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        self._sort_state = {}

    # ── Sorting ──────────────────────────────────────
    def _sort_col(self, col):
        rev = self._sort_state.get(col, False)
        self._filtered.sort(key=lambda r: str(r.get(col) or ""), reverse=rev)
        self._sort_state[col] = not rev
        self._populate_table(self._filtered)

    # ── Data loading ─────────────────────────────────
    def _load_data_async(self):
        self._status_lbl.config(text="⏳  Loading…", fg=C["warning"])
        t = threading.Thread(target=self._fetch_thread, daemon=True)
        t.start()

    def _fetch_thread(self):
        try:
            rows = fetch_processes()
            self.root.after(0, self._on_data_loaded, rows, None)
        except Exception as e:
            self.root.after(0, self._on_data_loaded, [], str(e))

    def _on_data_loaded(self, rows, error):
        if error:
            self._status_lbl.config(text=f"❌  {error}", fg=C["danger"])
            messagebox.showerror("DB Error",
                                 f"Failed to load processes:\n{error}",
                                 parent=self.root)
            return

        self._processes  = rows
        self._all_depts  = sorted({r.get("department") or "Unknown"
                                   for r in rows})
        self._status_lbl.config(
            text=f"● {len(rows)} processes loaded",
            fg=C["success"])

        # refresh dept filter menu
        self._dept_menu.delete(0, "end")
        self._dept_menu.add_command(label="All",
                                    command=lambda: self._set_dept("All"))
        for d in self._all_depts:
            self._dept_menu.add_command(
                label=d, command=lambda x=d: self._set_dept(x))

        self._build_stat_cards()
        self._apply_filter()
        self._refresh_charts()

    # ── Stat cards ───────────────────────────────────
    def _build_stat_cards(self):
        for w in self._cards_frame.winfo_children():
            w.destroy()

        total   = len(self._processes)
        depts   = len(self._all_depts)
        owners  = len({r.get("process_owner") for r in self._processes
                       if r.get("process_owner")})
        freqs   = len({r.get("frequency") for r in self._processes
                       if r.get("frequency")})

        cards = [
            ("🧩", "Total Processes", total,   C["accent2"]),
            ("🏢", "Departments",     depts,   C["purple"]),
            ("👤", "Owners",          owners,  C["success"]),
            ("🔁", "Freq. Types",     freqs,   C["warning"]),
        ]
        for icon, lbl, val, color in cards:
            StatCard(self._cards_frame, icon, lbl, val, color).pack(
                side="left", fill="x", expand=True, padx=(0, 8))

    # ── Filter & populate ────────────────────────────
    def _set_dept(self, val):
        self._dept_var.set(val)
        self._apply_filter()

    def _apply_filter(self):
        q    = self._search_var.get().lower().strip()
        dept = self._dept_var.get()

        self._filtered = [
            r for r in self._processes
            if (dept == "All" or r.get("department") == dept)
            and (not q or any(q in str(v).lower()
                              for v in r.values()))
        ]
        self._populate_table(self._filtered)
        self._count_lbl.config(
            text=f"Showing {len(self._filtered)} of {len(self._processes)}")

    def _populate_table(self, rows):
        self.tree.delete(*self.tree.get_children())
        self._iid_map = {}

        for i, row in enumerate(rows):
            tag  = "even" if i % 2 == 0 else "odd"
            vals = (
                row.get("process_id")    or "",
                row.get("process_name")  or "",
                row.get("department")    or "",
                row.get("process_owner") or "",
                row.get("frequency")     or "",
            )
            iid = self.tree.insert("", "end", values=vals, tags=(tag,))
            self._iid_map[iid] = row

        # color frequency cell via tag trick
        self._detail._build_empty()
        self._selected_row = None

    # ── Charts refresh ───────────────────────────────
    def _refresh_charts(self):
        for w in self._charts_inner.winfo_children():
            w.destroy()
        ChartsPanel(self._charts_inner,
                    self._processes,
                    self._all_depts).pack(fill="both", expand=True)
        self._c_canvas.update_idletasks()
        self._c_canvas.configure(
            scrollregion=self._c_canvas.bbox("all"))

    # ── Row selection ────────────────────────────────
    def _on_select(self, _event):
        sel = self.tree.selection()
        if not sel:
            return
        iid = sel[0]
        row = self._iid_map.get(iid)
        if row:
            self._selected_row = row
            self._detail.show(row, self._all_depts)


# ─────────────────────────────────────────────────────
#  PUBLIC LAUNCHER  (call from mainform.py)
# ─────────────────────────────────────────────────────
def open_process_dashboard(parent=None):
    win = tk.Toplevel(parent)   # creates Window #2 — this was the ghost popup!
    ProcessDashboard(win)  


# ─────────────────────────────────────────────────────
#  STANDALONE RUN
# ─────────────────────────────────────────────────────
# if __name__ == "__main__":
#     open_process_dashboard()
