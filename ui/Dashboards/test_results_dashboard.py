"""
GRC360 — Test Results Dashboard
Tables : test_step_results  +  test_plan  +  test_steps
Place  : ui/Dashboards/test_results_dashboard.py
Launch : open_test_results_dashboard(tk.Toplevel())
"""

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime

from connectors.lambda_mysql import call_lambda

# ──────────────────────────────────────────────────────────────
#  PALETTE
# ──────────────────────────────────────────────────────────────
BG     = "#F0F4F8"
PANEL  = "#FFFFFF"
HEADER = "#1E2A3A"
BORDER = "#CBD5E1"
ACC    = "#2563EB"
TEXT   = "#1E293B"
DIM    = "#64748B"
GREEN  = "#10B981"
ROSE   = "#F43F5E"
GOLD   = "#F59E0B"
TEAL   = "#06B6D4"
VIOLET = "#8B5CF6"
AMBER  = "#F97316"
WHITE  = "#FFFFFF"
REVE   = "#F8FAFC"

STATUS_OPTS = ["pass", "fail", "pending", "skip", "review", "error"]
STATUS_C = {
    "pass":    GREEN,  "passed":  GREEN,
    "fail":    ROSE,   "failed":  ROSE,
    "pending": GOLD,
    "skip":    DIM,    "skipped": DIM,
    "error":   AMBER,
    "review":  VIOLET,
    "active":  TEAL,
}

def sclr(s): return STATUS_C.get((s or "").lower(), DIM)


# ──────────────────────────────────────────────────────────────
#  DATA FETCH
# ──────────────────────────────────────────────────────────────
def fetch_all():
    """Fetch test_step_results and enrich with test_plan + test_steps data."""
    r1 = call_lambda({
        "action":  "select",
        "table":   "test_step_results",
        "columns": ["test_step_result_id", "test_plan_id", "test_step_id",
                    "control_id", "status", "reason", "executed_at"]
    })
    results = r1.get("records", [])

    r2 = call_lambda({
        "action":  "select",
        "table":   "test_plan",
        "columns": ["test_plan_id", "test_plan_name", "module",
                    "created_by", "status"]
    })
    plan_map = {str(p["test_plan_id"]): p for p in r2.get("records", [])}

    r3 = call_lambda({
        "action":  "select",
        "table":   "test_steps",
        "columns": ["test_step_id", "control_assertion", "step_order",
                    "control_area", "risk_type", "status"]
    })
    step_map = {str(s["test_step_id"]): s for s in r3.get("records", [])}

    merged = []
    for row in results:
        pid  = str(row.get("test_plan_id")  or "")
        sid  = str(row.get("test_step_id")  or "")
        plan = plan_map.get(pid, {})
        step = step_map.get(sid, {})
        merged.append({
            **row,
            "test_plan_name":    plan.get("test_plan_name",    "—"),
            "module":            plan.get("module",             "—"),
            "plan_author":       plan.get("created_by",        "—"),
            "plan_status":       plan.get("status",            "—"),
            "control_assertion": step.get("control_assertion", "—"),
            "step_order":        step.get("step_order",        "—"),
            "control_area":      step.get("control_area",      "—"),
            "risk_type":         step.get("risk_type",         "—"),
            "step_status":       step.get("status",            "—"),
        })

    merged.sort(key=lambda x: str(x.get("executed_at") or ""), reverse=True)
    return merged, plan_map, step_map


def fetch_plans_only():
    r = call_lambda({
        "action":  "select",
        "table":   "test_plan",
        "columns": ["test_plan_id", "test_plan_name"]
    })
    return r.get("records", [])


def fetch_steps_only():
    r = call_lambda({
        "action":  "select",
        "table":   "test_steps",
        "columns": ["test_step_id", "control_assertion", "step_order"]
    })
    return r.get("records", [])


def fetch_controls_only():
    r = call_lambda({
        "action":  "select",
        "table":   "control",
        "columns": ["control_id", "control_name"]
    })
    return r.get("records", [])


# ──────────────────────────────────────────────────────────────
#  STAT CARD
# ──────────────────────────────────────────────────────────────
class StatCard(tk.Frame):
    def __init__(self, parent, label, color, **kw):
        super().__init__(parent, bg=PANEL,
                         highlightbackground=color,
                         highlightthickness=2, **kw)
        self._val = tk.Label(self, text="0", bg=PANEL, fg=color,
                             font=("Segoe UI", 18, "bold"))
        self._val.pack(pady=(8, 0))
        tk.Label(self, text=label, bg=PANEL, fg=DIM,
                 font=("Segoe UI", 7)).pack(pady=(2, 8))

    def set(self, v):
        self._val.config(text=str(v))


# ──────────────────────────────────────────────────────────────
#  PASS RATE BAR
# ──────────────────────────────────────────────────────────────
class PassRateBar(tk.Frame):
    def __init__(self, parent, passed, total, **kw):
        super().__init__(parent, bg=BORDER, height=20, **kw)
        self.pack_propagate(False)
        pct = max(min(passed / max(total, 1), 1.0), 0.0)
        tk.Frame(self, bg=GREEN).place(relx=0,   rely=0, relwidth=pct,       relheight=1)
        tk.Frame(self, bg=ROSE ).place(relx=pct, rely=0, relwidth=1.0 - pct, relheight=1)
        tk.Label(self,
                 text=f"  {int(pct*100)}%  pass rate   |   "
                      f"{passed} passed  /  {total - passed} not passed",
                 bg=GREEN if pct >= 0.5 else ROSE,
                 fg=WHITE, font=("Segoe UI", 8, "bold")).place(relx=0.5, rely=0.5, anchor="center")


# ──────────────────────────────────────────────────────────────
#  DETAIL PANEL
# ──────────────────────────────────────────────────────────────
class DetailPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=PANEL,
                         highlightbackground=BORDER,
                         highlightthickness=1,
                         width=240, **kw)
        self.pack_propagate(False)
        self._idle()

    def _clear(self):
        for w in self.winfo_children():
            w.destroy()

    def _idle(self):
        self._clear()
        tk.Label(self, text="Select a result\nto view details",
                 bg=PANEL, fg=DIM, font=("Segoe UI", 9),
                 justify="center").pack(expand=True)

    def show(self, row):
        self._clear()
        sc = sclr(row.get("status", ""))

        # Header
        hdr = tk.Frame(self, bg=sc, padx=12, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"Result  #{row.get('test_step_result_id', '')}",
                 bg=sc, fg=WHITE, font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(hdr, text=(row.get("test_plan_name") or "—")[:28],
                 bg=sc, fg=WHITE, font=("Segoe UI", 10, "bold"),
                 wraplength=215, justify="left").pack(anchor="w", pady=(4, 0))
        pill = tk.Frame(hdr, bg=WHITE, padx=6, pady=2)
        pill.pack(anchor="w", pady=(6, 0))
        tk.Label(pill, text=(row.get("status") or "—").upper(),
                 bg=WHITE, fg=sc, font=("Segoe UI", 7, "bold")).pack()

        # Scrollable body
        outer = tk.Frame(self, bg=PANEL)
        outer.pack(fill="both", expand=True)
        cv = tk.Canvas(outer, bg=PANEL, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical", command=cv.yview, width=6)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        cv.configure(yscrollcommand=sb.set)
        body = tk.Frame(cv, bg=PANEL, padx=12, pady=8)
        win  = cv.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",   lambda e: cv.itemconfig(win, width=e.width))

        def section(title, color=DIM):
            tk.Label(body, text=title, bg=PANEL, fg=color,
                     font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(10, 0))
            tk.Frame(body, bg=color, height=1).pack(fill="x", pady=(2, 0))

        def field(lbl, val):
            tk.Label(body, text=lbl, bg=PANEL, fg=DIM,
                     font=("Segoe UI", 7, "bold"), anchor="w").pack(fill="x", pady=(6, 0))
            tk.Label(body, text=str(val) if val else "—", bg=PANEL, fg=TEXT,
                     font=("Segoe UI", 9), wraplength=210,
                     justify="left", anchor="w").pack(fill="x")

        section("RESULT", sc)
        field("Executed At",  str(row.get("executed_at") or "—")[:19])
        field("Control ID",   row.get("control_id"))

        tk.Label(body, text="Reason", bg=PANEL, fg=DIM,
                 font=("Segoe UI", 7, "bold"), anchor="w").pack(fill="x", pady=(6, 0))
        rbox = tk.Frame(body, bg=REVE, highlightbackground=BORDER, highlightthickness=1)
        rbox.pack(fill="x", pady=(2, 0))
        tk.Label(rbox, text=row.get("reason") or "—",
                 bg=REVE, fg=TEXT, font=("Segoe UI", 8),
                 wraplength=210, justify="left", anchor="w",
                 padx=6, pady=6).pack(fill="x")

        section("TEST PLAN", ACC)
        field("Plan ID",     row.get("test_plan_id"))
        field("Plan Name",   row.get("test_plan_name"))
        field("Module",      row.get("module"))
        field("Author",      row.get("plan_author"))
        field("Plan Status", row.get("plan_status"))

        section("TEST STEP", TEAL)
        field("Step ID",      row.get("test_step_id"))
        field("Step Order",   row.get("step_order"))
        field("Control Area", row.get("control_area"))
        field("Risk Type",    row.get("risk_type"))
        field("Assertion",    row.get("control_assertion"))
        field("Step Status",  row.get("step_status"))


# ──────────────────────────────────────────────────────────────
#  PLAN SUMMARY SIDEBAR
# ──────────────────────────────────────────────────────────────
class PlanSummaryPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=PANEL,
                         highlightbackground=BORDER,
                         highlightthickness=1,
                         width=195, **kw)
        self.pack_propagate(False)
        self._callback = None
        self._active   = None
        self._build_skeleton()

    def _build_skeleton(self):
        for w in self.winfo_children(): w.destroy()
        tk.Label(self, text="PLAN SUMMARY",
                 bg=HEADER, fg=WHITE,
                 font=("Segoe UI", 8, "bold"),
                 padx=8, pady=6).pack(fill="x")
        self._body = tk.Frame(self, bg=PANEL)
        self._body.pack(fill="both", expand=True)
        tk.Label(self._body, text="Loading…",
                 bg=PANEL, fg=DIM, font=("Segoe UI", 9)).pack(pady=20)

    def set_callback(self, fn):
        self._callback = fn

    def rebuild(self, rows):
        for w in self._body.winfo_children(): w.destroy()

        plan_data = {}
        for r in rows:
            pid = r.get("test_plan_id") or "—"
            nm  = r.get("test_plan_name") or f"Plan {pid}"
            if pid not in plan_data:
                plan_data[pid] = {"name": nm, "pass": 0, "fail": 0,
                                  "other": 0, "total": 0}
            st = (r.get("status") or "").lower()
            plan_data[pid]["total"] += 1
            if   st in ("pass", "passed"):  plan_data[pid]["pass"]  += 1
            elif st in ("fail", "failed"):  plan_data[pid]["fail"]  += 1
            else:                            plan_data[pid]["other"] += 1

        cv = tk.Canvas(self._body, bg=PANEL, highlightthickness=0)
        sb = tk.Scrollbar(self._body, orient="vertical",
                          command=cv.yview, width=6)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        cv.configure(yscrollcommand=sb.set)
        inner = tk.Frame(cv, bg=PANEL)
        win   = cv.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",    lambda e: cv.itemconfig(win, width=e.width))

        if not plan_data:
            tk.Label(inner, text="No plans found",
                     bg=PANEL, fg=DIM, font=("Segoe UI", 8)).pack(pady=10)
            return

        for pid, d in sorted(plan_data.items()):
            total = max(d["total"], 1)
            pct   = int(d["pass"] / total * 100)
            pclr  = GREEN if pct >= 70 else (GOLD if pct >= 40 else ROSE)

            card = tk.Frame(inner, bg=PANEL,
                            highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", padx=5, pady=3)

            tk.Label(card, text=d["name"][:22],
                     bg=PANEL, fg=TEXT,
                     font=("Segoe UI", 8, "bold"),
                     anchor="w", padx=6, pady=(5, 0)).pack(fill="x")

            row_f = tk.Frame(card, bg=PANEL)
            row_f.pack(fill="x", padx=6, pady=(2, 0))
            for lbl, val, clr in [("✓", d["pass"],  GREEN),
                                   ("✗", d["fail"],  ROSE),
                                   ("◌", d["other"], DIM)]:
                tk.Label(row_f, text=f"{lbl}{val}",
                         bg=PANEL, fg=clr,
                         font=("Segoe UI", 8, "bold")).pack(side="left", padx=(0, 5))

            # pass rate bar
            bar_bg = tk.Frame(card, bg=BORDER, height=5)
            bar_bg.pack(fill="x", padx=6, pady=(3, 0))
            bar_bg.pack_propagate(False)
            tk.Frame(bar_bg, bg=pclr).place(
                relx=0, rely=0, relwidth=d["pass"] / total, relheight=1)

            tk.Label(card, text=f"{pct}% pass",
                     bg=PANEL, fg=pclr,
                     font=("Segoe UI", 7), anchor="e", padx=6).pack(fill="x", pady=(0, 4))

            def _click(e, p=pid):
                if self._callback: self._callback(p)
            for w in [card] + list(card.winfo_children()):
                w.bind("<Button-1>", _click)


# ──────────────────────────────────────────────────────────────
#  ADD RESULT FORM  (popup)
# ──────────────────────────────────────────────────────────────
class AddResultForm(tk.Toplevel):
    def __init__(self, parent, on_saved, **kw):
        super().__init__(parent, **kw)
        self.title("GRC360 — Record Test Result")
        self.geometry("480x520")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.grab_set()
        self._on_saved   = on_saved
        self._plans      = []
        self._steps      = []
        self._controls   = []
        self._plan_var   = tk.StringVar()
        self._step_var   = tk.StringVar()
        self._ctrl_var   = tk.StringVar()
        self._status_var = tk.StringVar(value="pass")
        self._reason_var = tk.StringVar()
        self._build_ui()
        threading.Thread(target=self._load_refs, daemon=True).start()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=HEADER, height=44)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=ACC, width=4).pack(side="left", fill="y")
        tk.Label(hdr, text="➕  Record Test Result",
                 bg=HEADER, fg=WHITE,
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=12)

        # Form body
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=20, pady=14)

        def lbl(text):
            tk.Label(outer, text=text, bg=BG, fg=TEXT,
                     font=("Segoe UI", 9, "bold"),
                     anchor="w").pack(fill="x", pady=(10, 2))

        # Test Plan
        lbl("Test Plan *")
        self._plan_cb = ttk.Combobox(outer, textvariable=self._plan_var,
                                     font=("Segoe UI", 9), state="readonly")
        self._plan_cb.pack(fill="x", ipady=3)

        # Test Step
        lbl("Test Step *")
        self._step_cb = ttk.Combobox(outer, textvariable=self._step_var,
                                     font=("Segoe UI", 9), state="readonly")
        self._step_cb.pack(fill="x", ipady=3)

        # Control
        lbl("Control")
        self._ctrl_cb = ttk.Combobox(outer, textvariable=self._ctrl_var,
                                     font=("Segoe UI", 9), state="readonly")
        self._ctrl_cb.pack(fill="x", ipady=3)

        # Status
        lbl("Result Status *")
        status_row = tk.Frame(outer, bg=BG)
        status_row.pack(fill="x")
        for opt in STATUS_OPTS:
            clr = sclr(opt)
            rb  = tk.Radiobutton(status_row,
                                 text=opt.upper(),
                                 variable=self._status_var,
                                 value=opt,
                                 bg=BG, fg=clr,
                                 selectcolor=PANEL,
                                 activebackground=BG,
                                 font=("Segoe UI", 8, "bold"),
                                 indicator=1)
            rb.pack(side="left", padx=(0, 8))

        # Reason
        lbl("Reason / Notes")
        self._reason_txt = tk.Text(outer, height=4,
                                   font=("Segoe UI", 9),
                                   bg=PANEL, fg=TEXT,
                                   relief="solid", bd=1,
                                   insertbackground=TEXT,
                                   wrap="word")
        self._reason_txt.pack(fill="x")

        # Buttons
        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(fill="x", pady=(16, 0))
        tk.Button(btn_row, text="  Save Result  ",
                  font=("Segoe UI", 10, "bold"),
                  bg=GREEN, fg=WHITE, relief="flat", bd=0,
                  padx=14, pady=6, cursor="hand2",
                  activebackground="#059669",
                  command=self._save).pack(side="left")
        tk.Button(btn_row, text="  Cancel  ",
                  font=("Segoe UI", 10),
                  bg=REVE, fg=DIM, relief="flat", bd=1,
                  padx=14, pady=6, cursor="hand2",
                  command=self.destroy).pack(side="left", padx=(10, 0))

        self._info_lbl = tk.Label(outer, text="", bg=BG, fg=DIM,
                                  font=("Segoe UI", 8))
        self._info_lbl.pack(fill="x", pady=(8, 0))

    def _load_refs(self):
        try:
            plans    = fetch_plans_only()
            steps    = fetch_steps_only()
            controls = fetch_controls_only()
            self.after(0, self._populate_refs, plans, steps, controls)
        except Exception as e:
            self.after(0, lambda: self._info_lbl.config(
                text=f"❌ Error loading refs: {e}", fg=ROSE))

    def _populate_refs(self, plans, steps, controls):
        self._plans    = plans
        self._steps    = steps
        self._controls = controls

        self._plan_cb["values"] = [
            f"{p['test_plan_id']} — {p.get('test_plan_name','')}" for p in plans]
        self._step_cb["values"] = [
            f"{s['test_step_id']} — Order {s.get('step_order','')}  {s.get('control_assertion','')[:40]}"
            for s in steps]
        self._ctrl_cb["values"] = ["(none)"] + [
            f"{c['control_id']} — {c.get('control_name','')}" for c in controls]

        if plans:    self._plan_cb.current(0)
        if steps:    self._step_cb.current(0)
        self._ctrl_cb.current(0)
        self._info_lbl.config(
            text=f"Loaded {len(plans)} plans, {len(steps)} steps, {len(controls)} controls",
            fg=GREEN)

    def _save(self):
        plan_sel = self._plan_var.get()
        step_sel = self._step_var.get()
        status   = self._status_var.get()
        reason   = self._reason_txt.get("1.0", "end").strip()

        if not plan_sel or not step_sel or not status:
            messagebox.showwarning("Required Fields",
                                   "Please select Test Plan, Test Step and Status.",
                                   parent=self)
            return

        try:
            plan_id = int(plan_sel.split("—")[0].strip())
        except Exception:
            messagebox.showerror("Error", "Invalid Test Plan selection.", parent=self)
            return

        try:
            step_id = int(step_sel.split("—")[0].strip())
        except Exception:
            messagebox.showerror("Error", "Invalid Test Step selection.", parent=self)
            return

        ctrl_sel = self._ctrl_var.get()
        control_id = None
        if ctrl_sel and ctrl_sel != "(none)":
            try:
                control_id = int(ctrl_sel.split("—")[0].strip())
            except Exception:
                control_id = None

        data = {
            "test_plan_id":  plan_id,
            "test_step_id":  step_id,
            "status":        status,
            "reason":        reason or None,
            "executed_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
        if control_id:
            data["control_id"] = control_id

        self._info_lbl.config(text="Saving…", fg=GOLD)
        threading.Thread(target=self._do_save, args=(data,), daemon=True).start()

    def _do_save(self, data):
        try:
            resp = call_lambda({
                "action": "insert",
                "table":  "test_step_results",
                "data":   data
            })
            err = resp.get("error")
            if err:
                self.after(0, lambda: messagebox.showerror(
                    "Save Failed", str(err), parent=self))
                self.after(0, lambda: self._info_lbl.config(
                    text=f"❌ {err}", fg=ROSE))
            else:
                self.after(0, self._saved_ok)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Error", str(e), parent=self))

    def _saved_ok(self):
        messagebox.showinfo("Saved", "Test result recorded successfully.", parent=self)
        self.destroy()
        if self._on_saved:
            self._on_saved()


# ──────────────────────────────────────────────────────────────
#  MAIN DASHBOARD
# ──────────────────────────────────────────────────────────────
class TestResultsDashboard:

    def __init__(self, root):
        self.root        = root
        self.root.title("GRC360 — Test Results Dashboard")
        self.root.geometry("1020x660")
        self.root.resizable(False, False)
        self.root.configure(bg=BG)

        self._rows       = []
        self._filtered   = []
        self._iid_map    = {}
        self._search_var = tk.StringVar()
        self._plan_var   = tk.StringVar(value="All Plans")
        self._stat_var   = tk.StringVar(value="All Status")
        self._area_var   = tk.StringVar(value="All Areas")
        self._sort_state = {}
        self._active_pid = None

        self._build_ui()
        self._load()

    # ── UI BUILD ─────────────────────────────────────────────
    def _build_ui(self):
        # HEADER
        hdr = tk.Frame(self.root, bg=HEADER, height=46)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=ACC, width=4).pack(side="left", fill="y")
        tk.Label(hdr, text="📊  Test Results Dashboard",
                 bg=HEADER, fg=WHITE,
                 font=("Segoe UI", 12, "bold")).pack(side="left", padx=12)

        right_hdr = tk.Frame(hdr, bg=HEADER)
        right_hdr.pack(side="right", padx=10)
        self._status_lbl = tk.Label(right_hdr, text="⏳  Loading…",
                                    bg=HEADER, fg=GOLD,
                                    font=("Segoe UI", 9))
        self._status_lbl.pack(side="right", padx=(10, 0))
        tk.Button(right_hdr, text="↺  Refresh",
                  font=("Segoe UI", 9),
                  bg=DIM, fg=WHITE, relief="flat", bd=0,
                  padx=10, pady=3, cursor="hand2",
                  command=self._load).pack(side="right", padx=(0, 6), pady=8)
        tk.Button(right_hdr, text="➕  Add Result",
                  font=("Segoe UI", 9, "bold"),
                  bg=GREEN, fg=WHITE, relief="flat", bd=0,
                  padx=10, pady=3, cursor="hand2",
                  activebackground="#059669",
                  command=self._open_add_form).pack(side="right", pady=8)

        # STAT CARDS
        cards_row = tk.Frame(self.root, bg=BG)
        cards_row.pack(fill="x", padx=12, pady=(8, 4))
        self._c_total  = StatCard(cards_row, "Total Results", ACC)
        self._c_pass   = StatCard(cards_row, "Passed",        GREEN)
        self._c_fail   = StatCard(cards_row, "Failed",        ROSE)
        self._c_other  = StatCard(cards_row, "Other",         GOLD)
        self._c_plans  = StatCard(cards_row, "Test Plans",    VIOLET)
        self._c_steps  = StatCard(cards_row, "Test Steps",    TEAL)
        for c in (self._c_total, self._c_pass, self._c_fail,
                  self._c_other, self._c_plans, self._c_steps):
            c.pack(side="left", expand=True, fill="x", padx=3)

        # PASS RATE BAR
        self._bar_wrap = tk.Frame(self.root, bg=BG)
        self._bar_wrap.pack(fill="x", padx=12, pady=(0, 4))

        # TOOLBAR
        tb = tk.Frame(self.root, bg=BG)
        tb.pack(fill="x", padx=12, pady=(0, 4))

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

        for var, attr in [(self._plan_var, "_plan_menu"),
                          (self._stat_var, "_stat_menu"),
                          (self._area_var, "_area_menu")]:
            btn = tk.Menubutton(tb, textvariable=var,
                                font=("Segoe UI", 9), bg=WHITE, fg=TEXT,
                                relief="solid", bd=1,
                                padx=8, pady=5, cursor="hand2",
                                indicatoron=True)
            btn.pack(side="left", padx=(6, 0))
            m = tk.Menu(btn, tearoff=0, bg=WHITE, fg=TEXT,
                        activebackground=ACC, activeforeground=WHITE)
            btn["menu"] = m
            setattr(self, attr, m)

        tk.Button(tb, text="✕ Clear",
                  font=("Segoe UI", 8), bg=REVE, fg=DIM,
                  relief="flat", bd=1, padx=6, pady=4, cursor="hand2",
                  command=self._clear_filter).pack(side="left", padx=(6, 0))

        self._count_lbl = tk.Label(tb, text="", bg=BG, fg=DIM,
                                   font=("Segoe UI", 8))
        self._count_lbl.pack(side="right")

        # BODY
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        # Left — plan summary
        self._plan_panel = PlanSummaryPanel(body)
        self._plan_panel.pack(side="left", fill="y", padx=(0, 8))
        self._plan_panel.set_callback(self._filter_by_plan)

        # Centre — table
        tframe = tk.Frame(body, bg=BG)
        tframe.pack(side="left", fill="both", expand=True)
        self._build_table(tframe)

        # Right — detail
        self._detail = DetailPanel(body)
        self._detail.pack(side="right", fill="y", padx=(8, 0))

    def _build_table(self, parent):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("TR.Treeview",
                    background=WHITE, foreground=TEXT,
                    fieldbackground=WHITE, rowheight=24,
                    font=("Segoe UI", 9), borderwidth=0)
        s.configure("TR.Treeview.Heading",
                    background=HEADER, foreground=WHITE,
                    font=("Segoe UI", 9, "bold"), relief="flat")
        s.map("TR.Treeview",
              background=[("selected", ACC)],
              foreground=[("selected", WHITE)])

        vis = ("test_step_result_id", "test_plan_name", "control_assertion",
               "step_order", "control_area", "status", "executed_at")
        labels = {
            "test_step_result_id": "ID",
            "test_plan_name":      "Test Plan",
            "control_assertion":   "Assertion",
            "step_order":          "Order",
            "control_area":        "Control Area",
            "status":              "Result",
            "executed_at":         "Executed At",
        }
        widths = {
            "test_step_result_id": 38,
            "test_plan_name":      160,
            "control_assertion":   170,
            "step_order":          42,
            "control_area":        90,
            "status":              65,
            "executed_at":         115,
        }

        wrap = tk.Frame(parent, bg=BORDER, bd=1)
        wrap.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(wrap, columns=vis, show="headings",
                                  style="TR.Treeview", selectmode="browse")
        for c in vis:
            self.tree.heading(c, text=labels[c],
                              command=lambda col=c: self._sort(col))
            self.tree.column(c, width=widths[c], anchor="w",
                             stretch=(c in ("test_plan_name", "control_assertion")))

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

    # ── DATA FLOW ────────────────────────────────────────────
    def _load(self):
        self._status_lbl.config(text="⏳  Loading…", fg=GOLD)
        threading.Thread(target=self._fetch, daemon=True).start()

    def _fetch(self):
        try:
            rows, _, _ = fetch_all()
            self.root.after(0, self._loaded, rows, None)
        except Exception as e:
            import traceback
            self.root.after(0, self._loaded, [], traceback.format_exc())

    def _loaded(self, rows, err):
        if err:
            short = str(err).split("\n")[-1] or str(err)[:80]
            self._status_lbl.config(text=f"❌ {short}", fg=ROSE)
            messagebox.showerror("Load Error", str(err), parent=self.root)
            return

        self._rows = rows
        total  = len(rows)
        passed = sum(1 for r in rows if (r.get("status") or "").lower() in ("pass","passed"))
        failed = sum(1 for r in rows if (r.get("status") or "").lower() in ("fail","failed"))
        other  = total - passed - failed
        plans  = len({r.get("test_plan_id")  for r in rows if r.get("test_plan_id")})
        steps  = len({r.get("test_step_id")  for r in rows if r.get("test_step_id")})

        self._status_lbl.config(text=f"●  {total} results", fg=GREEN)
        self._c_total.set(total)
        self._c_pass.set(passed)
        self._c_fail.set(failed)
        self._c_other.set(other)
        self._c_plans.set(plans)
        self._c_steps.set(steps)

        # Pass rate bar
        for w in self._bar_wrap.winfo_children(): w.destroy()
        PassRateBar(self._bar_wrap, passed, total).pack(fill="x", ipady=1)

        # Dropdowns
        all_plans = sorted({r.get("test_plan_name") or "Unknown" for r in rows})
        all_stats = sorted({(r.get("status") or "Unknown").capitalize() for r in rows})
        all_areas = sorted({r.get("control_area") or "Unknown" for r in rows})

        self._plan_menu.delete(0, "end")
        self._plan_menu.add_command(label="All Plans",
            command=lambda: self._plan_var.set("All Plans") or self._clear_filter())
        for p in all_plans:
            self._plan_menu.add_command(label=p,
                command=lambda x=p: self._plan_var.set(x) or self._filter())

        self._stat_menu.delete(0, "end")
        self._stat_menu.add_command(label="All Status",
            command=lambda: self._stat_var.set("All Status") or self._filter())
        for s in all_stats:
            self._stat_menu.add_command(label=s,
                command=lambda x=s: self._stat_var.set(x) or self._filter())

        self._area_menu.delete(0, "end")
        self._area_menu.add_command(label="All Areas",
            command=lambda: self._area_var.set("All Areas") or self._filter())
        for a in all_areas:
            self._area_menu.add_command(label=a,
                command=lambda x=a: self._area_var.set(x) or self._filter())

        self._plan_panel.rebuild(rows)
        self._filter()

    def _filter_by_plan(self, pid):
        self._active_pid = pid
        self._filter()

    def _clear_filter(self):
        self._active_pid = None
        self._plan_var.set("All Plans")
        self._stat_var.set("All Status")
        self._area_var.set("All Areas")
        self._search_var.set("")
        self._filter()

    def _filter(self):
        q    = self._search_var.get().lower().strip()
        plan = self._plan_var.get()
        stat = self._stat_var.get()
        area = self._area_var.get()

        self._filtered = [
            r for r in self._rows
            if (self._active_pid is None or
                str(r.get("test_plan_id")) == str(self._active_pid))
            and (plan == "All Plans"   or r.get("test_plan_name") == plan)
            and (stat == "All Status"  or (r.get("status") or "").lower() == stat.lower())
            and (area == "All Areas"   or r.get("control_area") == area)
            and (not q or any(q in str(v).lower() for v in r.values()))
        ]
        self._populate()
        self._count_lbl.config(
            text=f"{len(self._filtered)} / {len(self._rows)} records")

    def _populate(self):
        self.tree.delete(*self.tree.get_children())
        self._iid_map = {}
        for i, r in enumerate(self._filtered):
            base = "even" if i % 2 == 0 else "odd"
            stag = f"s_{(r.get('status') or '').lower()}"
            vals = (r.get("test_step_result_id") or "",
                    r.get("test_plan_name")       or "",
                    r.get("control_assertion")    or "",
                    r.get("step_order")           or "",
                    r.get("control_area")         or "",
                    r.get("status")               or "",
                    str(r.get("executed_at") or "")[:19])
            iid = self.tree.insert("", "end", values=vals, tags=(base, stag))
            self._iid_map[iid] = r
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

    def _open_add_form(self):
        AddResultForm(self.root, on_saved=self._load)


# ──────────────────────────────────────────────────────────────
#  LAUNCHER
# ──────────────────────────────────────────────────────────────
def open_test_results_dashboard(win=None):
    if win is None:
        win = tk.Tk()
        TestResultsDashboard(win)
        win.mainloop()
    else:
        TestResultsDashboard(win)
