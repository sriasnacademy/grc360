"""
GRC360 — Subprocess Dashboard
Place in: ui/Dashboards/subprocess_dashboard.py
Call:     open_subprocess_dashboard(tk.Toplevel())
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
    "sub_process_id", "sub_process_name", "description",
    "department", "sub_process_owner", "frequency",
    "triggers", "outcomes", "status",
]
COL_LABELS = {
    "sub_process_id":    "SP ID",
    "sub_process_name":  "Subprocess Name",
    "description":       "Description",
    "department":        "Department",
    "sub_process_owner": "Owner",
    "frequency":         "Frequency",
    "triggers":          "Triggers",
    "outcomes":          "Outcomes",
    "status":            "Status",
}

# ─────────────────────────────────────────────
#  DESIGN TOKENS  (sky-blue theme)
# ─────────────────────────────────────────────
C = {
    "bg":          "#0D1B2A",
    "sidebar":     "#112236",
    "card":        "#0F2035",
    "card_border": "#1B3A5C",
    "accent":      "#0EA5E9",
    "accent2":     "#38BDF8",
    "success":     "#10B981",
    "warning":     "#F59E0B",
    "danger":      "#EF4444",
    "purple":      "#A78BFA",
    "teal":        "#2DD4BF",
    "text_main":   "#E0F2FE",
    "text_dim":    "#7FB3D3",
    "text_tiny":   "#4A7A9B",
    "row_even":    "#0A1828",
    "row_odd":     "#0F2035",
    "row_select":  "#0C3460",
    "input_bg":    "#112236",
    "input_fg":    "#E0F2FE",
}

STATUS_COLORS = {
    "active":    "#10B981",
    "inactive":  "#EF4444",
    "pending":   "#F59E0B",
    "draft":     "#7FB3D3",
    "completed": "#2DD4BF",
}
DEPT_COLORS = ["#0EA5E9","#A78BFA","#10B981","#F59E0B",
               "#EF4444","#2DD4BF","#F97316","#84CC16"]

FONT_HEAD   = ("Segoe UI", 9,  "bold")
FONT_CELL   = ("Segoe UI", 9)
FONT_CARD_N = ("Segoe UI", 26, "bold")
FONT_CARD_L = ("Segoe UI", 9)
FONT_SECT   = ("Segoe UI", 8,  "bold")
FONT_SEARCH = ("Segoe UI", 10)


# ─────────────────────────────────────────────
#  DATA FETCH
# ─────────────────────────────────────────────
def fetch_subprocesses():
    payload = {"action": "select", "table": "sub_processes", "columns": COLUMNS}
    response = call_lambda(payload)
    return response.get("records", [])


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
                         highlightthickness=1, width=295, **kw)
        self.pack_propagate(False)
        self._build_empty()

    def _clear(self):
        for w in self.winfo_children(): w.destroy()

    def _build_empty(self):
        self._clear()
        tk.Label(self, text="🔀\n\nSelect a row\nto view details",
                 bg=C["sidebar"], fg=C["text_tiny"],
                 font=("Segoe UI", 10), justify="center").pack(expand=True)

    def show(self, row):
        self._clear()
        sc  = status_color(row.get("status", ""))
        hdr = tk.Frame(self, bg=C["accent"], padx=14, pady=10)
        hdr.pack(fill="x")
        top = tk.Frame(hdr, bg=C["accent"])
        top.pack(fill="x")
        tk.Label(top, text=f"SP-{row.get('sub_process_id','')}",
                 bg=C["accent"], fg="#FFFFFF",
                 font=("Segoe UI", 9, "bold")).pack(side="left")
        pill = tk.Frame(top, bg=sc, padx=6, pady=1)
        pill.pack(side="right")
        tk.Label(pill, text=(row.get("status") or "—").capitalize(),
                 bg=sc, fg="#FFFFFF", font=("Segoe UI", 8, "bold")).pack()
        tk.Label(hdr, text=row.get("sub_process_name",""), bg=C["accent"],
                 fg="#FFFFFF", font=("Segoe UI", 12, "bold"),
                 wraplength=265, justify="left").pack(anchor="w", pady=(4, 0))
        body = tk.Frame(self, bg=C["sidebar"], padx=14, pady=10)
        body.pack(fill="both", expand=True)
        for lbl, key in [("🏢  Department",  "department"),
                          ("👤  Owner",       "sub_process_owner"),
                          ("🔁  Frequency",   "frequency"),
                          ("⚡  Triggers",    "triggers"),
                          ("✅  Outcomes",    "outcomes")]:
            tk.Label(body, text=lbl, bg=C["sidebar"], fg=C["text_dim"],
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(8, 0))
            tk.Label(body, text=row.get(key) or "—", bg=C["sidebar"],
                     fg=C["text_main"], font=("Segoe UI", 9),
                     wraplength=260, justify="left", anchor="w").pack(fill="x")
        tk.Frame(body, bg=C["card_border"], height=1).pack(fill="x", pady=10)
        tk.Label(body, text="📄  Description", bg=C["sidebar"], fg=C["text_dim"],
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x")
        tk.Label(body, text=row.get("description") or "—", bg=C["sidebar"],
                 fg=C["text_main"], font=("Segoe UI", 9),
                 wraplength=260, justify="left", anchor="w").pack(fill="x", pady=(4, 0))


class ChartsPanel(tk.Frame):
    def __init__(self, parent, subprocesses, **kw):
        super().__init__(parent, bg=C["bg"], **kw)
        self._draw(subprocesses)

    def _bar_block(self, title, data_dict, colors):
        f = tk.Frame(self, bg=C["card"], highlightbackground=C["card_border"],
                     highlightthickness=1, padx=14, pady=12)
        f.pack(fill="x", pady=(0, 10))
        tk.Label(f, text=title, bg=C["card"], fg=C["text_dim"],
                 font=FONT_SECT).pack(anchor="w")
        tk.Frame(f, bg=C["card_border"], height=1).pack(fill="x", pady=6)
        max_v = max(data_dict.values(), default=1)
        BAR_W = 148
        for i, (k, v) in enumerate(sorted(data_dict.items(), key=lambda x: -x[1])):
            color = colors[i % len(colors)] if isinstance(colors, list) \
                    else colors.get(k.lower(), C["text_dim"])
            row = tk.Frame(f, bg=C["card"])
            row.pack(fill="x", pady=2)
            tk.Label(row, text=k or "—", bg=C["card"], fg=C["text_main"],
                     font=("Segoe UI", 8), width=14, anchor="w").pack(side="left")
            cv = tk.Canvas(row, bg=C["card"], height=14, width=BAR_W, highlightthickness=0)
            cv.pack(side="left", padx=(4, 0))
            fw = int(BAR_W * v / max_v)
            cv.create_rectangle(0, 2, BAR_W, 12, fill=C["card_border"], outline="")
            if fw: cv.create_rectangle(0, 2, fw, 12, fill=color, outline="")
            tk.Label(row, text=str(v), bg=C["card"], fg=color,
                     font=("Segoe UI", 8, "bold"), width=3).pack(side="left", padx=4)

    def _draw(self, subprocesses):
        # Status summary (big numbers)
        status_counts = {}
        for s in subprocesses:
            k = (s.get("status") or "Unknown").capitalize()
            status_counts[k] = status_counts.get(k, 0) + 1
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
            cell = tk.Frame(row, bg=C["card"], padx=6)
            cell.pack(side="left")
            tk.Label(cell, text=str(cnt), bg=C["card"], fg=col,
                     font=("Segoe UI", 18, "bold")).pack()
            tk.Label(cell, text=s, bg=C["card"], fg=C["text_dim"],
                     font=("Segoe UI", 7)).pack()

        dept_count = {}
        for s in subprocesses:
            d = s.get("department") or "Unknown"
            dept_count[d] = dept_count.get(d, 0) + 1
        self._bar_block("BY DEPARTMENT", dept_count, DEPT_COLORS)

        freq_count = {}
        for s in subprocesses:
            f = s.get("frequency") or "Unknown"
            freq_count[f] = freq_count.get(f, 0) + 1
        self._bar_block("BY FREQUENCY", freq_count, DEPT_COLORS)


# ─────────────────────────────────────────────
#  MAIN DASHBOARD
# ─────────────────────────────────────────────
class SubprocessDashboard:
    def __init__(self, root):
        self.root        = root
        self.root.title("GRC360 — Subprocess Dashboard")
        self.root.geometry("1300x800")
        self.root.minsize(1050, 640)
        self.root.configure(bg=C["bg"])
        self._subprocesses = []
        self._filtered     = []
        self._search_var   = tk.StringVar()
        self._dept_var     = tk.StringVar(value="All")
        self._status_var   = tk.StringVar(value="All")
        self._iid_map      = {}
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
        tk.Label(hdr, text="  /  Subprocess Dashboard", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI", 11)).pack(side="left")
        self._status_lbl = tk.Label(hdr, text="⏳  Loading…",
                                    bg=C["sidebar"], fg=C["warning"],
                                    font=("Segoe UI", 9))
        self._status_lbl.pack(side="right", padx=18)
        tk.Button(hdr, text="↺  Refresh", font=("Segoe UI", 9, "bold"),
                  bg=C["accent"], fg="#FFFFFF", relief="flat", bd=0,
                  padx=12, pady=4, cursor="hand2",
                  activebackground="#0284C7", activeforeground="#FFFFFF",
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
                 insertbackground=C["input_fg"], relief="flat", width=26).pack(
                     side="left", ipady=5, padx=(0, 8))
        self._search_var.trace_add("write", lambda *_: self._apply_filter())

        for var, attr in [(self._dept_var, "_dept_menu"),
                          (self._status_var, "_status_menu")]:
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

        co = tk.Frame(split, bg=C["bg"], width=240)
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
        style.configure("SP.Treeview",
                        background=C["row_even"], foreground=C["text_main"],
                        fieldbackground=C["row_even"], rowheight=28,
                        font=FONT_CELL, borderwidth=0)
        style.configure("SP.Treeview.Heading",
                        background=C["sidebar"], foreground=C["text_dim"],
                        font=FONT_HEAD, relief="flat", borderwidth=0)
        style.map("SP.Treeview",
                  background=[("selected", C["row_select"])],
                  foreground=[("selected", "#FFFFFF")])
        style.layout("SP.Treeview", [("SP.Treeview.treearea", {"sticky": "nswe"})])

        vis_cols   = ("sub_process_id","sub_process_name","department",
                      "sub_process_owner","frequency","status")
        col_widths = {"sub_process_id":60,"sub_process_name":180,"department":110,
                      "sub_process_owner":120,"frequency":90,"status":80}
        wrap = tk.Frame(self._table_frame, bg=C["bg"],
                        highlightbackground=C["card_border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(wrap, columns=vis_cols, show="headings",
                                  style="SP.Treeview", selectmode="browse")
        for col in vis_cols:
            self.tree.heading(col, text=COL_LABELS[col],
                              command=lambda c=col: self._sort_col(c))
            self.tree.column(col, width=col_widths[col], anchor="w",
                             stretch=(col == "sub_process_name"))
        vsb = tk.Scrollbar(wrap, orient="vertical", command=self.tree.yview,
                           bg=C["bg"], troughcolor=C["sidebar"])
        vsb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=vsb.set)
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
            rows = fetch_subprocesses()
            self.root.after(0, self._on_data_loaded, rows, None)
        except Exception as e:
            self.root.after(0, self._on_data_loaded, [], str(e))

    def _on_data_loaded(self, rows, error):
        if error:
            self._status_lbl.config(text=f"❌  {error}", fg=C["danger"])
            messagebox.showerror("Error", f"Failed to load subprocesses:\n{error}",
                                 parent=self.root)
            return
        self._subprocesses = rows
        self._status_lbl.config(
            text=f"● {len(rows)} subprocesses loaded", fg=C["success"])

        all_depts    = sorted({r.get("department") or "Unknown" for r in rows})
        all_statuses = sorted({(r.get("status") or "Unknown").capitalize() for r in rows})

        self._dept_menu.delete(0, "end")
        self._dept_menu.add_command(label="All", command=lambda: self._set_dept("All"))
        for d in all_depts:
            self._dept_menu.add_command(label=d, command=lambda x=d: self._set_dept(x))

        self._status_menu.delete(0, "end")
        self._status_menu.add_command(label="All",
                                      command=lambda: self._set_status("All"))
        for s in all_statuses:
            self._status_menu.add_command(label=s, command=lambda x=s: self._set_status(x))

        self._build_stat_cards()
        self._apply_filter()
        self._refresh_charts()

    def _build_stat_cards(self):
        for w in self._cards_frame.winfo_children(): w.destroy()
        total    = len(self._subprocesses)
        active   = sum(1 for r in self._subprocesses
                       if (r.get("status") or "").lower() == "active")
        inactive = sum(1 for r in self._subprocesses
                       if (r.get("status") or "").lower() == "inactive")
        depts    = len({r.get("department") for r in self._subprocesses if r.get("department")})
        owners   = len({r.get("sub_process_owner") for r in self._subprocesses
                        if r.get("sub_process_owner")})
        for icon, lbl, val, color in [
            ("🔀", "Total",       total,    C["accent2"]),
            ("✅", "Active",      active,   C["success"]),
            ("🔴", "Inactive",    inactive, C["danger"]),
            ("🏢", "Departments", depts,    C["purple"]),
            ("👤", "Owners",      owners,   C["warning"]),
        ]:
            StatCard(self._cards_frame, icon, lbl, val, color).pack(
                side="left", fill="x", expand=True, padx=(0, 8))

    def _set_dept(self, val):
        self._dept_var.set(val); self._apply_filter()

    def _set_status(self, val):
        self._status_var.set(val); self._apply_filter()

    def _apply_filter(self):
        q      = self._search_var.get().lower().strip()
        dept   = self._dept_var.get()
        status = self._status_var.get()
        self._filtered = [
            r for r in self._subprocesses
            if (dept   == "All" or r.get("department") == dept)
            and (status == "All" or (r.get("status") or "").lower() == status.lower())
            and (not q  or any(q in str(v).lower() for v in r.values()))
        ]
        self._populate_table(self._filtered)
        self._count_lbl.config(
            text=f"Showing {len(self._filtered)} of {len(self._subprocesses)}")

    def _populate_table(self, rows):
        self.tree.delete(*self.tree.get_children())
        self._iid_map = {}
        for i, row in enumerate(rows):
            tag = "even" if i % 2 == 0 else "odd"
            vals = (row.get("sub_process_id") or "", row.get("sub_process_name") or "",
                    row.get("department") or "", row.get("sub_process_owner") or "",
                    row.get("frequency") or "", row.get("status") or "")
            iid = self.tree.insert("", "end", values=vals, tags=(tag,))
            self._iid_map[iid] = row
        self._detail._build_empty()

    def _refresh_charts(self):
        for w in self._charts_inner.winfo_children(): w.destroy()
        ChartsPanel(self._charts_inner, self._subprocesses).pack(fill="both", expand=True)
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
def open_subprocess_dashboard(win=None):
    if win is None:
        win = tk.Tk()
        SubprocessDashboard(win)
    else:
        SubprocessDashboard(win)

