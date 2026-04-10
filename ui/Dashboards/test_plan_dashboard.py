"""
GRC360 — Test Plan Report Dashboard  (Enhanced Edition)
• Quantitative Analytics panel on the right
• Module / Status / Author breakdowns with %
• Rich detail panel with scrollable full record
Place in: ui/Dashboards/test_plan_dashboard.py
Call:     open_test_plan_dashboard(tk.Toplevel())
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

# ── PALETTE  (dark purple theme) ─────────────────────────────
C = {
    "bg":          "#0F0A1E",
    "sidebar":     "#1A1030",
    "card":        "#1E1538",
    "card_border": "#3B2A6A",
    "accent":      "#7C3AED",
    "accent2":     "#A78BFA",
    "success":     "#10B981",
    "warning":     "#F59E0B",
    "danger":      "#EF4444",
    "teal":        "#06B6D4",
    "rose":        "#F43F5E",
    "text_main":   "#EDE9FE",
    "text_dim":    "#8B7FC8",
    "text_tiny":   "#4C3A7A",
    "row_even":    "#0A071A",
    "row_odd":     "#1E1538",
    "row_select":  "#2D1B6E",
    "input_bg":    "#1A1030",
    "input_fg":    "#EDE9FE",
}

STATUS_COLORS = {
    "active":      "#10B981",
    "inactive":    "#EF4444",
    "draft":       "#8B7FC8",
    "completed":   "#06B6D4",
    "in progress": "#7C3AED",
    "pending":     "#F59E0B",
    "approved":    "#06B6D4",
    "review":      "#F59E0B",
}
MODULE_COLORS = ["#7C3AED","#06B6D4","#10B981","#F59E0B","#EF4444","#F97316","#A78BFA","#38BDF8"]

FONT_HEAD   = ("Segoe UI", 9,  "bold")
FONT_CELL   = ("Segoe UI", 9)
FONT_CARD_N = ("Segoe UI", 22, "bold")
FONT_CARD_L = ("Segoe UI", 8)
FONT_SECT   = ("Segoe UI", 8,  "bold")
FONT_SEARCH = ("Segoe UI", 10)

# ── DATA ──────────────────────────────────────────────────────
def fetch_plans():
    r = call_lambda({"action": "select", "table": TABLE, "columns": COLUMNS})
    return r.get("records", [])


def sclr(s): return STATUS_COLORS.get((s or "").lower(), C["text_dim"])

# ── STAT CARD ─────────────────────────────────────────────────
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


# ── DETAIL PANEL ──────────────────────────────────────────────
class DetailPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["sidebar"],
                         highlightbackground=C["card_border"],
                         highlightthickness=1, width=265, **kw)
        self.pack_propagate(False)
        self._idle()

    def _clear(self):
        for w in self.winfo_children(): w.destroy()

    def _idle(self):
        self._clear()
        tk.Label(self, text="📋\n\nSelect a plan\nto view full details",
                 bg=C["sidebar"], fg=C["text_tiny"],
                 font=("Segoe UI", 10), justify="center").pack(expand=True)

    def show(self, row):
        self._clear()
        sc  = sclr(row.get("status",""))
        hdr = tk.Frame(self, bg=sc, padx=12, pady=10)
        hdr.pack(fill="x")
        top = tk.Frame(hdr, bg=sc)
        top.pack(fill="x")
        tk.Label(top, text=f"Plan #{row.get('test_plan_id','')}",
                 bg=sc, fg="#FFFFFF", font=("Segoe UI", 8, "bold")).pack(side="left")
        pill = tk.Frame(top, bg="#FFFFFF", padx=6, pady=1)
        pill.pack(side="right")
        tk.Label(pill, text=(row.get("status") or "—").upper(),
                 bg="#FFFFFF", fg=sc, font=("Segoe UI", 7, "bold")).pack()
        tk.Label(hdr, text=row.get("test_plan_name",""), bg=sc, fg="#FFFFFF",
                 font=("Segoe UI", 11, "bold"),
                 wraplength=240, justify="left").pack(anchor="w", pady=(4,0))

        # Module badge
        if row.get("module"):
            mb = tk.Frame(hdr, bg=C["accent"], padx=7, pady=2)
            mb.pack(anchor="w", pady=(6,0))
            tk.Label(mb, text=f"📦  {row.get('module','')}",
                     bg=C["accent"], fg="#FFFFFF",
                     font=("Segoe UI", 8, "bold")).pack()

        # Scrollable body
        outer = tk.Frame(self, bg=C["sidebar"])
        outer.pack(fill="both", expand=True)
        cv = tk.Canvas(outer, bg=C["sidebar"], highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=cv.yview, width=6)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        cv.configure(yscrollcommand=sb.set)
        body = tk.Frame(cv, bg=C["sidebar"], padx=12, pady=10)
        win  = cv.create_window((0,0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>", lambda e: cv.itemconfig(win, width=e.width))

        for lbl, key in [("✍️  Created By",   "created_by"),
                          ("📅  Created Date", "created_date"),
                          ("📄  Description",  "description")]:
            tk.Label(body, text=lbl, bg=C["sidebar"], fg=C["text_dim"],
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(8,0))
            val = str(row.get(key) or "—")
            if key == "created_date": val = val[:19]
            tk.Label(body, text=val, bg=C["sidebar"],
                     fg=C["text_main"], font=("Segoe UI", 9),
                     wraplength=235, justify="left", anchor="w").pack(fill="x")
            tk.Frame(body, bg=C["card_border"], height=1).pack(fill="x", pady=(6,0))


# ── QUANT PANEL ───────────────────────────────────────────────
class QuantPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=C["bg"], width=270, **kw)
        self.pack_propagate(False)
        hdr = tk.Frame(self, bg=C["card_border"], height=32)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Label(hdr, text="📊  PLAN ANALYTICS", bg=C["card_border"],
                 fg=C["text_dim"], font=FONT_SECT).pack(side="left", padx=10, pady=7)
        self._body_frame = None

    def refresh(self, plans, filtered):
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

        total   = len(plans)
        visible = len(filtered)
        active  = sum(1 for p in plans if (p.get("status") or "").lower() == "active")
        draft   = sum(1 for p in plans if (p.get("status") or "").lower() == "draft")
        done    = sum(1 for p in plans if (p.get("status") or "").lower() == "completed")
        modules = len({p.get("module") for p in plans if p.get("module")})
        authors = len({p.get("created_by") for p in plans if p.get("created_by")})

        # KPI
        sf = self._section(body, "KEY METRICS")
        for lbl, val, clr in [
            ("Total Plans",        total,   C["accent2"]),
            ("Showing (filtered)", visible, C["teal"]),
            ("Active",             active,  C["success"]),
            ("Draft",              draft,   C["text_dim"]),
            ("Completed",          done,    C["teal"]),
            ("Modules",            modules, C["accent"]),
            ("Authors",            authors, C["warning"]),
        ]:
            r = tk.Frame(sf, bg=C["card"])
            r.pack(fill="x", pady=2)
            tk.Label(r, text=lbl, bg=C["card"], fg=C["text_dim"],
                     font=("Segoe UI", 8), anchor="w").pack(side="left")
            tk.Label(r, text=str(val), bg=C["card"], fg=clr,
                     font=("Segoe UI", 10, "bold")).pack(side="right")

        # Status
        sc_c = {}
        for p in plans:
            k = (p.get("status") or "Unknown").capitalize()
            sc_c[k] = sc_c.get(k, 0) + 1
        self._bar(body, "BY STATUS", sc_c, list(STATUS_COLORS.values()), total)

        # Module
        mod_c = {}
        for p in plans:
            k = p.get("module") or "Unknown"
            mod_c[k] = mod_c.get(k, 0) + 1
        self._bar(body, "BY MODULE", mod_c, MODULE_COLORS, total)

        # Author
        auth_c = {}
        for p in plans:
            k = p.get("created_by") or "Unknown"
            auth_c[k] = auth_c.get(k, 0) + 1
        top_auth = dict(sorted(auth_c.items(), key=lambda x: -x[1])[:7])
        self._bar(body, "BY AUTHOR (TOP 7)", top_auth, MODULE_COLORS, total)

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


# ── MAIN DASHBOARD ────────────────────────────────────────────
class TestPlanDashboard:
    def __init__(self, root):
        self.root        = root
        self.root.title("GRC360 — Test Plan Report Dashboard")
        self.root.geometry("1480x830")
        self.root.minsize(1100, 660)
        self.root.configure(bg=C["bg"])
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
        hdr = tk.Frame(self.root, bg=C["sidebar"], height=56)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        tk.Frame(hdr, bg=C["accent"], width=4).pack(side="left", fill="y")
        cv = tk.Canvas(hdr, width=10, height=10, bg=C["sidebar"], highlightthickness=0)
        cv.create_oval(0, 0, 10, 10, fill=C["accent"], outline="")
        cv.pack(side="left", padx=(14,6), pady=23)
        tk.Label(hdr, text="GRC360", bg=C["sidebar"], fg=C["text_main"],
                 font=("Segoe UI", 15, "bold")).pack(side="left")
        tk.Label(hdr, text="  /  Test Plan Report", bg=C["sidebar"],
                 fg=C["text_dim"], font=("Segoe UI", 11)).pack(side="left")
        self._status_lbl = tk.Label(hdr, text="⏳  Loading…",
                                    bg=C["sidebar"], fg=C["warning"],
                                    font=("Segoe UI", 9))
        self._status_lbl.pack(side="right", padx=18)
        tk.Button(hdr, text="↺  Refresh", font=("Segoe UI", 9, "bold"),
                  bg=C["accent"], fg="#FFFFFF", relief="flat", bd=0,
                  padx=12, pady=4, cursor="hand2",
                  activebackground="#5B21B6", activeforeground="#FFFFFF",
                  command=self._load).pack(side="right", pady=14, padx=(0,8))

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
                 insertbackground=C["input_fg"], relief="flat", width=22).pack(
                     side="left", ipady=5, padx=(0,8))
        self._search_var.trace_add("write", lambda *_: self._filter())

        for var, attr in [(self._mod_var,  "_mod_menu"),
                          (self._stat_var, "_stat_menu")]:
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
        style.configure("TP.Treeview",
                        background=C["row_even"], foreground=C["text_main"],
                        fieldbackground=C["row_even"], rowheight=30,
                        font=FONT_CELL, borderwidth=0)
        style.configure("TP.Treeview.Heading",
                        background=C["sidebar"], foreground=C["text_dim"],
                        font=FONT_HEAD, relief="flat", borderwidth=0)
        style.map("TP.Treeview",
                  background=[("selected", C["row_select"])],
                  foreground=[("selected", "#FFFFFF")])
        style.layout("TP.Treeview", [("TP.Treeview.treearea", {"sticky": "nswe"})])

        vis    = ("test_plan_id","test_plan_name","module","created_by","created_date","status")
        labels = {"test_plan_id":"ID","test_plan_name":"Plan Name",
                  "module":"Module","created_by":"Author",
                  "created_date":"Created Date","status":"Status"}
        widths = {"test_plan_id":50,"test_plan_name":210,"module":110,
                  "created_by":110,"created_date":115,"status":80}

        wrap = tk.Frame(self._table_frame, bg=C["bg"],
                        highlightbackground=C["card_border"], highlightthickness=1)
        wrap.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(wrap, columns=vis, show="headings",
                                  style="TP.Treeview", selectmode="browse")
        for c in vis:
            self.tree.heading(c, text=labels[c],
                              command=lambda col=c: self._sort(col))
            self.tree.column(c, width=widths[c], anchor="w",
                             stretch=(c == "test_plan_name"))
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
        for sk, clr in STATUS_COLORS.items():
            self.tree.tag_configure(f"s_{sk}", foreground=clr)
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

    def _load(self):
        self._status_lbl.config(text="⏳  Loading…", fg=C["warning"])
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            rows = fetch_plans()
            self.root.after(0, self._loaded, rows, None)
        except Exception as e:
            self.root.after(0, self._loaded, [], str(e))

    def _loaded(self, rows, err):
        if err:
            self._status_lbl.config(text=f"❌ {err}", fg=C["danger"])
            messagebox.showerror("Error", err, parent=self.root)
            return
        self._plans = rows
        self._status_lbl.config(text=f"●  {len(rows)} records", fg=C["success"])

        total    = len(rows)
        active   = sum(1 for p in rows if (p.get("status") or "").lower() == "active")
        modules  = len({p.get("module") for p in rows if p.get("module")})
        authors  = len({p.get("created_by") for p in rows if p.get("created_by")})
        draft    = sum(1 for p in rows if (p.get("status") or "").lower() == "draft")

        # Stat cards
        for w in self._cards_frame.winfo_children(): w.destroy()
        for icon, lbl, val, color in [
            ("📋", "Total Plans", total,   C["accent2"]),
            ("✅", "Active",      active,  C["success"]),
            ("📝", "Draft",       draft,   C["text_dim"]),
            ("📦", "Modules",     modules, C["teal"]),
            ("✍️", "Authors",     authors, C["warning"]),
        ]:
            StatCard(self._cards_frame, icon, lbl, val, color).pack(
                side="left", fill="x", expand=True, padx=(0,8))

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
            and (st == "All Status" or (p.get("status") or "").lower() == st.lower())
            and (not q or any(q in str(v).lower() for v in p.values()))
        ]
        self._populate()
        self._count_lbl.config(
            text=f"{len(self._filtered)} / {len(self._plans)} records")
        self._quant.refresh(self._plans, self._filtered)

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
            if row: self._detail.show(row)


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
