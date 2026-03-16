"""
GRC360 — Test Results Dashboard
Tables : test_task_results  (primary)
         test_step_results  (secondary)
         test_plan          (lookup)
         test_steps         (lookup)
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
#  TABLE SCHEMAS
# ──────────────────────────────────────────────────────────────
# test_task_results
TTR_TABLE   = "test_task_results"
TTR_COLUMNS = ["test_task_result_id", "cycle_number", "test_task_id",
               "test_step_id", "test_plan_id", "control_id",
               "evidence_payload", "evidence_result",
               "status", "evaluation_source", "executed_at", "created_at"]

# test_step_results
TSR_TABLE   = "test_step_results"
TSR_COLUMNS = ["test_step_result_id", "test_plan_id", "test_step_id",
               "control_id", "status", "reason", "executed_at"]

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
#  DATA FETCH  — safe call with error logging
# ──────────────────────────────────────────────────────────────
def safe_fetch(table, columns):
    """Fetch from a table safely. Returns (records, error_str)."""
    try:
        r = call_lambda({"action": "select", "table": table, "columns": columns})
        err = r.get("error")
        if err:
            return [], str(err)
        return r.get("records", []), None
    except Exception as e:
        return [], str(e)


def fetch_task_results():
    """Fetch test_task_results enriched with test_plan + test_steps."""
    ttr, err1 = safe_fetch(TTR_TABLE, TTR_COLUMNS)
    tsr, err2 = safe_fetch(TSR_TABLE, TSR_COLUMNS)
    plans, _  = safe_fetch("test_plan",
                            ["test_plan_id", "test_plan_name",
                             "module", "created_by", "status"])
    steps, _  = safe_fetch("test_steps",
                            ["test_step_id", "control_assertion",
                             "step_order", "control_area", "risk_type", "status"])

    plan_map = {str(p["test_plan_id"]): p for p in plans}
    step_map = {str(s["test_step_id"]): s for s in steps}

    # ── Merge test_task_results ──────────────────────────────
    task_rows = []
    for row in ttr:
        pid  = str(row.get("test_plan_id") or "")
        sid  = str(row.get("test_step_id") or "")
        plan = plan_map.get(pid, {})
        step = step_map.get(sid, {})
        task_rows.append({
            **row,
            "_source":           "Task Result",
            "_result_id":        row.get("test_task_result_id", ""),
            "test_plan_name":    plan.get("test_plan_name",    "—"),
            "module":            plan.get("module",             "—"),
            "plan_author":       plan.get("created_by",        "—"),
            "plan_status":       plan.get("status",            "—"),
            "control_assertion": step.get("control_assertion", "—"),
            "step_order":        step.get("step_order",        "—"),
            "control_area":      step.get("control_area",      "—"),
            "risk_type":         step.get("risk_type",         "—"),
            "step_status":       step.get("status",            "—"),
            "reason":            row.get("evidence_result",    "—"),
        })

    # ── Merge test_step_results ──────────────────────────────
    step_rows = []
    for row in tsr:
        pid  = str(row.get("test_plan_id") or "")
        sid  = str(row.get("test_step_id") or "")
        plan = plan_map.get(pid, {})
        step = step_map.get(sid, {})
        step_rows.append({
            **row,
            "_source":           "Step Result",
            "_result_id":        row.get("test_step_result_id", ""),
            "test_plan_name":    plan.get("test_plan_name",    "—"),
            "module":            plan.get("module",             "—"),
            "plan_author":       plan.get("created_by",        "—"),
            "plan_status":       plan.get("status",            "—"),
            "control_assertion": step.get("control_assertion", "—"),
            "step_order":        step.get("step_order",        "—"),
            "control_area":      step.get("control_area",      "—"),
            "risk_type":         step.get("risk_type",         "—"),
            "step_status":       step.get("status",            "—"),
            "cycle_number":      row.get("cycle_number",       "—"),
            "evaluation_source": row.get("evaluation_source",  "—"),
            "evidence_payload":  row.get("evidence_payload",   "—"),
            "evidence_result":   row.get("evidence_result",    "—"),
        })

    # Combine and sort newest first
    all_rows = task_rows + step_rows
    all_rows.sort(key=lambda x: str(x.get("executed_at") or
                                    x.get("created_at") or ""), reverse=True)

    errors = [e for e in [err1, err2] if e]
    return all_rows, "; ".join(errors) if errors else None


def fetch_plans_only():
    recs, _ = safe_fetch("test_plan", ["test_plan_id", "test_plan_name"])
    return recs


def fetch_steps_only():
    recs, _ = safe_fetch("test_steps",
                         ["test_step_id", "control_assertion", "step_order"])
    return recs


def fetch_controls_only():
    recs, _ = safe_fetch("control", ["control_id", "control_name"])
    return recs


# ──────────────────────────────────────────────────────────────
#  STAT CARD
# ──────────────────────────────────────────────────────────────
class StatCard(tk.Frame):
    def __init__(self, parent, label, color, **kw):
        super().__init__(parent, bg=PANEL,
                         highlightbackground=color,
                         highlightthickness=2, **kw)
        self._val = tk.Label(self, text="0", bg=PANEL, fg=color,
                             font=("Segoe UI", 12, "bold"))
        self._val.pack(pady=(4, 0))
        tk.Label(self, text=label, bg=PANEL, fg=DIM,
                 font=("Segoe UI", 6)).pack(pady=(1, 4))

    def set(self, v):
        self._val.config(text=str(v))


# ──────────────────────────────────────────────────────────────
#  PASS RATE BAR
# ──────────────────────────────────────────────────────────────
class PassRateBar(tk.Frame):
    def __init__(self, parent, passed, total, **kw):
        super().__init__(parent, bg=BORDER, height=14, **kw)
        self.pack_propagate(False)
        pct  = passed / max(total, 1)
        pclr = GREEN if pct >= 0.5 else ROSE
        tk.Frame(self, bg=GREEN).place(relx=0,   rely=0,
                                       relwidth=pct,       relheight=1)
        tk.Frame(self, bg=ROSE ).place(relx=pct, rely=0,
                                       relwidth=1.0 - pct, relheight=1)
        tk.Label(self,
                 text=f" {int(pct*100)}%  pass rate"
                      f"   |   {passed} passed  /  {total - passed} not passed"
                      f"   |   {total} total",
                 bg=pclr, fg=WHITE,
                 font=("Segoe UI", 7, "bold")).place(relx=0.5, rely=0.5,
                                                     anchor="center")


# ──────────────────────────────────────────────────────────────
#  DETAIL PANEL
# ──────────────────────────────────────────────────────────────
class DetailPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=PANEL,
                         highlightbackground=BORDER,
                         highlightthickness=1,
                         width=220, **kw)
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
        sc  = sclr(row.get("status", ""))
        src = row.get("_source", "Result")

        # Header
        hdr = tk.Frame(self, bg=sc, padx=12, pady=10)
        hdr.pack(fill="x")
        tk.Label(hdr,
                 text=f"{src}  #{row.get('_result_id', '')}",
                 bg=sc, fg=WHITE,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(hdr,
                 text=(row.get("test_plan_name") or "—")[:28],
                 bg=sc, fg=WHITE,
                 font=("Segoe UI", 10, "bold"),
                 wraplength=200, justify="left").pack(anchor="w", pady=(4, 0))
        pill = tk.Frame(hdr, bg=WHITE, padx=6, pady=2)
        pill.pack(anchor="w", pady=(6, 0))
        tk.Label(pill,
                 text=(row.get("status") or "—").upper(),
                 bg=WHITE, fg=sc,
                 font=("Segoe UI", 7, "bold")).pack()

        # Scrollable body
        outer = tk.Frame(self, bg=PANEL)
        outer.pack(fill="both", expand=True)
        cv = tk.Canvas(outer, bg=PANEL, highlightthickness=0)
        sb = tk.Scrollbar(outer, orient="vertical",
                          command=cv.yview, width=6)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        cv.configure(yscrollcommand=sb.set)
        body = tk.Frame(cv, bg=PANEL, padx=12, pady=8)
        win  = cv.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>",
                  lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",
                lambda e: cv.itemconfig(win, width=e.width))

        def section(title, color=DIM):
            tk.Label(body, text=title, bg=PANEL, fg=color,
                     font=("Segoe UI", 8, "bold"),
                     anchor="w").pack(fill="x", pady=(10, 0))
            tk.Frame(body, bg=color, height=1).pack(fill="x", pady=(2, 0))

        def field(lbl, val):
            tk.Label(body, text=lbl, bg=PANEL, fg=DIM,
                     font=("Segoe UI", 7, "bold"),
                     anchor="w").pack(fill="x", pady=(6, 0))
            tk.Label(body, text=str(val) if val else "—",
                     bg=PANEL, fg=TEXT, font=("Segoe UI", 9),
                     wraplength=195, justify="left",
                     anchor="w").pack(fill="x")

        def text_box(lbl, val):
            tk.Label(body, text=lbl, bg=PANEL, fg=DIM,
                     font=("Segoe UI", 7, "bold"),
                     anchor="w").pack(fill="x", pady=(6, 0))
            box = tk.Frame(body, bg=REVE,
                           highlightbackground=BORDER, highlightthickness=1)
            box.pack(fill="x", pady=(2, 0))
            tk.Label(box, text=str(val) if val else "—",
                     bg=REVE, fg=TEXT, font=("Segoe UI", 8),
                     wraplength=195, justify="left",
                     anchor="w", padx=6, pady=5).pack(fill="x")

        # Force canvas to update scrollregion after all content is packed
        def _update_scroll(event=None):
            cv.configure(scrollregion=cv.bbox("all"))
        body.bind("<Configure>", lambda e: _update_scroll())

        # ── RESULT ─────────────────────────────────────
        section("RESULT", sc)
        field("Source",          row.get("_source"))
        field("Executed At",     str(row.get("executed_at") or "—")[:19])
        field("Created At",      str(row.get("created_at")  or "—")[:19])
        field("Cycle Number",    row.get("cycle_number"))
        field("Evaluation Src",  row.get("evaluation_source"))
        field("Control ID",      row.get("control_id"))
        text_box("Reason / Evidence Result",
                 row.get("reason") or row.get("evidence_result"))
        if row.get("evidence_payload"):
            text_box("Evidence Payload", row.get("evidence_payload"))

        # ── TEST PLAN ───────────────────────────────────
        section("TEST PLAN", ACC)
        field("Plan ID",     row.get("test_plan_id"))
        field("Plan Name",   row.get("test_plan_name"))
        field("Module",      row.get("module"))
        field("Author",      row.get("plan_author"))
        field("Plan Status", row.get("plan_status"))

        # ── TEST STEP ───────────────────────────────────
        section("TEST STEP", TEAL)
        field("Step ID",      row.get("test_step_id"))
        field("Step Order",   row.get("step_order"))
        field("Control Area", row.get("control_area"))
        field("Risk Type",    row.get("risk_type"))
        field("Assertion",    row.get("control_assertion"))
        field("Step Status",  row.get("step_status"))

        # Update scrollregion after all widgets are packed
        body.update_idletasks()
        cv.configure(scrollregion=cv.bbox("all"))



# ──────────────────────────────────────────────────────────────
#  PLAN STRIP  (slim horizontal bar above the table)
# ──────────────────────────────────────────────────────────────
class PlanStripPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG, height=38, **kw)
        self.pack_propagate(False)
        self._callback  = None
        self._active    = None
        self._cards     = {}
        # horizontal scrollable canvas
        self._cv = tk.Canvas(self, bg=BG, height=38, highlightthickness=0)
        self._cv.pack(side="left", fill="both", expand=True)
        self._inner = tk.Frame(self._cv, bg=BG)
        self._win   = self._cv.create_window((0, 0), window=self._inner, anchor="nw")
        self._inner.bind("<Configure>",
                         lambda e: self._cv.configure(
                             scrollregion=self._cv.bbox("all")))

    def set_callback(self, fn):
        self._callback = fn

    def rebuild(self, rows):
        for w in self._inner.winfo_children():
            w.destroy()
        self._cards = {}

        # Aggregate per plan
        plan_data = {}
        for r in rows:
            pid = str(r.get("test_plan_id") or "—")
            nm  = r.get("test_plan_name") or f"Plan {pid}"
            if pid not in plan_data:
                plan_data[pid] = {"name": nm, "pass": 0, "fail": 0, "total": 0}
            st = (r.get("status") or "").lower()
            plan_data[pid]["total"] += 1
            if st in ("pass", "passed"):  plan_data[pid]["pass"] += 1
            elif st in ("fail", "failed"): plan_data[pid]["fail"] += 1

        # "All" card first
        all_card = tk.Frame(self._inner, bg=HEADER, padx=6, pady=2,
                            highlightbackground=ACC, highlightthickness=2,
                            cursor="hand2")
        all_card.pack(side="left", padx=(0, 4), pady=2, fill="y")
        tk.Label(all_card, text="All Plans", bg=HEADER, fg=WHITE,
                 font=("Segoe UI", 7, "bold")).pack()
        tk.Label(all_card, text=f"{len(rows)} results",
                 bg=HEADER, fg=DIM,
                 font=("Segoe UI", 6)).pack()
        all_card.bind("<Button-1>", lambda e: self._select(None))
        for w in all_card.winfo_children():
            w.bind("<Button-1>", lambda e: self._select(None))
        self._cards["__all__"] = all_card

        for pid, d in sorted(plan_data.items()):
            total = max(d["total"], 1)
            pct   = int(d["pass"] / total * 100)
            pclr  = GREEN if pct >= 70 else (GOLD if pct >= 40 else ROSE)
            nm    = d["name"][:18]

            card = tk.Frame(self._inner, bg=PANEL, padx=6, pady=2,
                            highlightbackground=BORDER, highlightthickness=1,
                            cursor="hand2")
            card.pack(side="left", padx=(0, 4), pady=2, fill="y")

            tk.Label(card, text=nm, bg=PANEL, fg=TEXT,
                     font=("Segoe UI", 7, "bold")).pack(anchor="w")

            row_f = tk.Frame(card, bg=PANEL)
            row_f.pack(anchor="w")
            tk.Label(row_f, text=f"✓{d['pass']}",
                     bg=PANEL, fg=GREEN,
                     font=("Segoe UI", 6, "bold")).pack(side="left")
            tk.Label(row_f, text=f" ✗{d['fail']}",
                     bg=PANEL, fg=ROSE,
                     font=("Segoe UI", 6, "bold")).pack(side="left")
            tk.Label(row_f, text=f" {pct}%",
                     bg=PANEL, fg=pclr,
                     font=("Segoe UI", 6, "bold")).pack(side="left")

            def _click(e, p=pid):
                self._select(p)

            card.bind("<Button-1>", _click)
            for w in card.winfo_children() + [row_f] + list(row_f.winfo_children()):
                w.bind("<Button-1>", _click)
            self._cards[pid] = card

    def _select(self, pid):
        # Reset all card borders
        for k, card in self._cards.items():
            if k == "__all__":
                card.config(highlightbackground=ACC if pid is None else DIM,
                            bg=HEADER if pid is None else PANEL)
                for w in card.winfo_children():
                    w.config(bg=HEADER if pid is None else PANEL)
            else:
                hl = ACC if str(k) == str(pid) else BORDER
                card.config(highlightbackground=hl,
                            highlightthickness=2 if hl == ACC else 1)
        self._active = pid
        if self._callback:
            self._callback(pid)

# ──────────────────────────────────────────────────────────────
#  PLAN SUMMARY SIDEBAR
# ──────────────────────────────────────────────────────────────
class PlanSummaryPanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=PANEL,
                         highlightbackground=BORDER,
                         highlightthickness=1,
                         width=150, **kw)
        self.pack_propagate(False)
        self._callback = None
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
                 bg=PANEL, fg=DIM,
                 font=("Segoe UI", 9)).pack(pady=20)

    def set_callback(self, fn):
        self._callback = fn

    def rebuild(self, rows):
        for w in self._body.winfo_children(): w.destroy()

        # Aggregate per plan
        plan_data = {}
        for r in rows:
            pid = str(r.get("test_plan_id") or "—")
            nm  = r.get("test_plan_name") or f"Plan {pid}"
            if pid not in plan_data:
                plan_data[pid] = {"name": nm, "pass": 0,
                                  "fail": 0, "other": 0, "total": 0}
            st = (r.get("status") or "").lower()
            plan_data[pid]["total"] += 1
            if   st in ("pass", "passed"):  plan_data[pid]["pass"]  += 1
            elif st in ("fail", "failed"):  plan_data[pid]["fail"]  += 1
            else:                            plan_data[pid]["other"] += 1

        # Scrollable list
        cv = tk.Canvas(self._body, bg=PANEL, highlightthickness=0)
        sb = tk.Scrollbar(self._body, orient="vertical",
                          command=cv.yview, width=6)
        sb.pack(side="right", fill="y")
        cv.pack(side="left", fill="both", expand=True)
        cv.configure(yscrollcommand=sb.set)
        inner = tk.Frame(cv, bg=PANEL)
        win   = cv.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: cv.configure(scrollregion=cv.bbox("all")))
        cv.bind("<Configure>",
                lambda e: cv.itemconfig(win, width=e.width))

        if not plan_data:
            tk.Label(inner, text="No data yet",
                     bg=PANEL, fg=DIM,
                     font=("Segoe UI", 8)).pack(pady=12)
            return

        for pid, d in sorted(plan_data.items()):
            total = max(d["total"], 1)
            pct   = int(d["pass"] / total * 100)
            pclr  = GREEN if pct >= 70 else (GOLD if pct >= 40 else ROSE)

            card = tk.Frame(inner, bg=PANEL,
                            highlightbackground=BORDER,
                            highlightthickness=1)
            card.pack(fill="x", padx=5, pady=3)

            tk.Label(card, text=d["name"][:22],
                     bg=PANEL, fg=TEXT,
                     font=("Segoe UI", 8, "bold"),
                     anchor="w", padx=6,
                     pady=4).pack(fill="x")

            cnt_row = tk.Frame(card, bg=PANEL)
            cnt_row.pack(fill="x", padx=6, pady=(2, 0))
            for lbl, val, clr in [("✓", d["pass"],  GREEN),
                                   ("✗", d["fail"],  ROSE),
                                   ("◌", d["other"], DIM)]:
                tk.Label(cnt_row, text=f"{lbl} {val}",
                         bg=PANEL, fg=clr,
                         font=("Segoe UI", 8, "bold")).pack(
                             side="left", padx=(0, 6))

            bar_bg = tk.Frame(card, bg=BORDER, height=5)
            bar_bg.pack(fill="x", padx=6, pady=(3, 0))
            bar_bg.pack_propagate(False)
            tk.Frame(bar_bg, bg=pclr).place(
                relx=0, rely=0,
                relwidth=d["pass"] / total,
                relheight=1.0)

            tk.Label(card, text=f"{pct}% pass",
                     bg=PANEL, fg=pclr,
                     font=("Segoe UI", 7),
                     anchor="e", padx=6).pack(fill="x", pady=(0, 4))

            def _click(e, p=pid):
                if self._callback:
                    self._callback(p)

            for w in [card] + list(card.winfo_children()):
                w.bind("<Button-1>", _click)


# ──────────────────────────────────────────────────────────────
#  ADD RESULT FORM
# ──────────────────────────────────────────────────────────────
class AddResultForm(tk.Toplevel):
    def __init__(self, parent, on_saved, **kw):
        super().__init__(parent, **kw)
        self.title("GRC360 — Record Test Result")
        self.geometry("500x580")
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
        self._source_var = tk.StringVar(value="manual")
        self._table_var  = tk.StringVar(value=TTR_TABLE)
        self._build_ui()
        threading.Thread(target=self._load_refs, daemon=True).start()

    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=HEADER, height=44)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Frame(hdr, bg=GREEN, width=4).pack(side="left", fill="y")
        tk.Label(hdr, text="➕  Record Test Result",
                 bg=HEADER, fg=WHITE,
                 font=("Segoe UI", 11, "bold")).pack(side="left", padx=12)

        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=20, pady=10)

        def lbl(text):
            tk.Label(outer, text=text, bg=BG, fg=TEXT,
                     font=("Segoe UI", 9, "bold"),
                     anchor="w").pack(fill="x", pady=(8, 2))

        # Table selector
        lbl("Save To *")
        tbl_row = tk.Frame(outer, bg=BG)
        tbl_row.pack(fill="x")
        for txt, val in [("Task Results (test_task_results)", TTR_TABLE),
                         ("Step Results (test_step_results)", TSR_TABLE)]:
            tk.Radiobutton(tbl_row, text=txt,
                           variable=self._table_var, value=val,
                           bg=BG, fg=TEXT, activebackground=BG,
                           selectcolor=PANEL,
                           font=("Segoe UI", 8)).pack(anchor="w")

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
        lbl("Control (optional)")
        self._ctrl_cb = ttk.Combobox(outer, textvariable=self._ctrl_var,
                                     font=("Segoe UI", 9), state="readonly")
        self._ctrl_cb.pack(fill="x", ipady=3)

        # Status
        lbl("Result Status *")
        srow = tk.Frame(outer, bg=BG)
        srow.pack(fill="x")
        for opt in STATUS_OPTS:
            tk.Radiobutton(srow, text=opt.upper(),
                           variable=self._status_var, value=opt,
                           bg=BG, fg=sclr(opt),
                           selectcolor=PANEL, activebackground=BG,
                           font=("Segoe UI", 8, "bold"),
                           indicator=1).pack(side="left", padx=(0, 6))

        # Reason / Evidence
        lbl("Reason / Evidence Notes")
        self._reason_txt = tk.Text(outer, height=4,
                                   font=("Segoe UI", 9),
                                   bg=PANEL, fg=TEXT,
                                   relief="solid", bd=1,
                                   insertbackground=TEXT,
                                   wrap="word")
        self._reason_txt.pack(fill="x")

        # Buttons
        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(fill="x", pady=(14, 0))
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

        self._info = tk.Label(outer, text="", bg=BG, fg=DIM,
                              font=("Segoe UI", 8))
        self._info.pack(fill="x", pady=(8, 0))

    def _load_refs(self):
        try:
            plans    = fetch_plans_only()
            steps    = fetch_steps_only()
            controls = fetch_controls_only()
            self.after(0, self._populate_refs, plans, steps, controls)
        except Exception as e:
            self.after(0, lambda: self._info.config(
                text=f"❌ {e}", fg=ROSE))

    def _populate_refs(self, plans, steps, controls):
        self._plans    = plans
        self._steps    = steps
        self._controls = controls

        self._plan_cb["values"] = [
            f"{p['test_plan_id']} — {p.get('test_plan_name', '')}"
            for p in plans]
        self._step_cb["values"] = [
            f"{s['test_step_id']} — Order {s.get('step_order','')}  "
            f"{(s.get('control_assertion') or '')[:38]}"
            for s in steps]
        self._ctrl_cb["values"] = ["(none)"] + [
            f"{c['control_id']} — {c.get('control_name', '')}"
            for c in controls]

        if plans:    self._plan_cb.current(0)
        if steps:    self._step_cb.current(0)
        self._ctrl_cb.current(0)
        self._info.config(
            text=f"Loaded: {len(plans)} plans · {len(steps)} steps · "
                 f"{len(controls)} controls",
            fg=GREEN)

    def _save(self):
        plan_val   = self._plan_var.get()
        step_val   = self._step_var.get()
        status     = self._status_var.get()
        table      = self._table_var.get()
        reason_txt = self._reason_txt.get("1.0", "end").strip()

        if not plan_val or not step_val or not status:
            messagebox.showwarning(
                "Required Fields",
                "Please select Test Plan, Test Step and Status.",
                parent=self)
            return

        try:
            plan_id = int(plan_val.split("—")[0].strip())
        except Exception:
            messagebox.showerror("Error", "Invalid plan selection.", parent=self)
            return
        try:
            step_id = int(step_val.split("—")[0].strip())
        except Exception:
            messagebox.showerror("Error", "Invalid step selection.", parent=self)
            return

        ctrl_val   = self._ctrl_var.get()
        control_id = None
        if ctrl_val and ctrl_val != "(none)":
            try:
                control_id = int(ctrl_val.split("—")[0].strip())
            except Exception:
                pass

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if table == TTR_TABLE:
            data = {
                "test_plan_id":       plan_id,
                "test_step_id":       step_id,
                "status":             status,
                "evidence_result":    reason_txt or None,
                "evaluation_source":  self._source_var.get() or "manual",
                "executed_at":        now,
                "created_at":         now,
            }
        else:
            data = {
                "test_plan_id":  plan_id,
                "test_step_id":  step_id,
                "status":        status,
                "reason":        reason_txt or None,
                "executed_at":   now,
            }

        if control_id:
            data["control_id"] = control_id

        self._info.config(text="Saving…", fg=GOLD)
        threading.Thread(target=self._do_save,
                         args=(data, table), daemon=True).start()

    def _do_save(self, data, table):
        try:
            resp = call_lambda({"action": "insert", "table": table, "data": data})
            err  = resp.get("error")
            if err:
                self.after(0, lambda: messagebox.showerror(
                    "Save Failed", str(err), parent=self))
                self.after(0, lambda: self._info.config(
                    text=f"❌ {err}", fg=ROSE))
            else:
                self.after(0, self._saved_ok)
        except Exception as e:
            self.after(0, lambda: messagebox.showerror(
                "Error", str(e), parent=self))

    def _saved_ok(self):
        messagebox.showinfo("Saved",
                            "Test result recorded successfully.",
                            parent=self)
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
        self._src_var    = tk.StringVar(value="All Sources")
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

        rh = tk.Frame(hdr, bg=HEADER)
        rh.pack(side="right", padx=10)
        self._status_lbl = tk.Label(rh, text="⏳  Loading…",
                                    bg=HEADER, fg=GOLD,
                                    font=("Segoe UI", 9))
        self._status_lbl.pack(side="right", padx=(10, 0))
        tk.Button(rh, text="↺  Refresh",
                  font=("Segoe UI", 9),
                  bg=DIM, fg=WHITE, relief="flat", bd=0,
                  padx=10, pady=3, cursor="hand2",
                  command=self._load).pack(side="right", padx=(0, 6), pady=8)
        tk.Button(rh, text="➕  Add Result",
                  font=("Segoe UI", 9, "bold"),
                  bg=GREEN, fg=WHITE, relief="flat", bd=0,
                  padx=10, pady=3, cursor="hand2",
                  activebackground="#059669",
                  command=self._open_add_form).pack(side="right", pady=8)

        # STAT CARDS
        cr = tk.Frame(self.root, bg=BG)
        cr.pack(fill="x", padx=12, pady=(4, 2))
        self._c_total  = StatCard(cr, "Total Results", ACC)
        self._c_pass   = StatCard(cr, "Passed",        GREEN)
        self._c_fail   = StatCard(cr, "Failed",        ROSE)
        self._c_other  = StatCard(cr, "Other",         GOLD)
        self._c_plans  = StatCard(cr, "Test Plans",    VIOLET)
        self._c_steps  = StatCard(cr, "Test Steps",    TEAL)
        for c in (self._c_total, self._c_pass, self._c_fail,
                  self._c_other, self._c_plans, self._c_steps):
            c.pack(side="left", expand=True, fill="x", padx=3)

        # PASS RATE BAR
        self._bar_wrap = tk.Frame(self.root, bg=BG)
        self._bar_wrap.pack(fill="x", padx=12, pady=(0, 2))

        # TOOLBAR
        tb = tk.Frame(self.root, bg=BG)
        tb.pack(fill="x", padx=12, pady=(0, 2))

        sf = tk.Frame(tb, bg=WHITE,
                      highlightbackground=BORDER, highlightthickness=1)
        sf.pack(side="left")
        tk.Label(sf, text=" 🔍", bg=WHITE, fg=DIM,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Entry(sf, textvariable=self._search_var,
                 font=("Segoe UI", 9), bg=WHITE, fg=TEXT,
                 insertbackground=TEXT, relief="flat", width=16).pack(
                     side="left", ipady=5, padx=(2, 6))
        self._search_var.trace_add("write", lambda *_: self._filter())

        for var, attr in [(self._plan_var, "_plan_menu"),
                          (self._stat_var, "_stat_menu"),
                          (self._area_var, "_area_menu"),
                          (self._src_var,  "_src_menu")]:
            btn = tk.Menubutton(tb, textvariable=var,
                                font=("Segoe UI", 9), bg=WHITE, fg=TEXT,
                                relief="solid", bd=1,
                                padx=7, pady=5, cursor="hand2",
                                indicatoron=True)
            btn.pack(side="left", padx=(5, 0))
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

        # PLAN SUMMARY STRIP (horizontal scrollable row of plan cards)
        strip_frame = tk.Frame(self.root, bg=BG)
        strip_frame.pack(fill="x", padx=12, pady=(0, 2))
        self._plan_strip = PlanStripPanel(strip_frame)
        self._plan_strip.pack(fill="x")
        self._plan_strip.set_callback(self._filter_by_plan)

        # BODY
        body = tk.Frame(self.root, bg=BG)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 6))

        # Left: table only (no sidebar — plan filter is in toolbar dropdown)
        tframe = tk.Frame(body, bg=BG)
        tframe.pack(side="left", fill="both", expand=True)
        self._build_table(tframe)

        # Right: detail panel
        self._detail = DetailPanel(body)
        self._detail.pack(side="right", fill="both", padx=(8, 0))

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

        vis = ("_result_id", "_source", "test_plan_name",
               "control_assertion", "step_order",
               "control_area", "status", "executed_at")
        labels = {
            "_result_id":        "ID",
            "_source":           "Source",
            "test_plan_name":    "Test Plan",
            "control_assertion": "Assertion",
            "step_order":        "Order",
            "control_area":      "Control Area",
            "status":            "Result",
            "executed_at":       "Executed At",
        }
        widths = {
            "_result_id":        32,
            "_source":           72,
            "test_plan_name":    135,
            "control_assertion": 155,
            "step_order":        38,
            "control_area":      90,
            "status":            58,
            "executed_at":       110,
        }

        wrap = tk.Frame(parent, bg=BORDER, bd=1)
        wrap.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(wrap, columns=vis, show="headings",
                                  style="TR.Treeview", selectmode="browse")
        for c in vis:
            self.tree.heading(c, text=labels[c],
                              command=lambda col=c: self._sort(col))
            self.tree.column(c, width=widths[c], anchor="w",
                             stretch=(c in ("test_plan_name",
                                            "control_assertion")))

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
            rows, warn = fetch_task_results()
            self.root.after(0, self._loaded, rows, None, warn)
        except Exception as e:
            import traceback
            self.root.after(0, self._loaded, [], traceback.format_exc(), None)

    def _loaded(self, rows, err, warn):
        if err:
            short = str(err).strip().split("\n")[-1][:80]
            self._status_lbl.config(text=f"❌ {short}", fg=ROSE)
            messagebox.showerror("Load Error", str(err), parent=self.root)
            return

        self._rows = rows
        total  = len(rows)
        passed = sum(1 for r in rows
                     if (r.get("status") or "").lower() in ("pass", "passed"))
        failed = sum(1 for r in rows
                     if (r.get("status") or "").lower() in ("fail", "failed"))
        other  = total - passed - failed
        plans  = len({r.get("test_plan_id")
                      for r in rows if r.get("test_plan_id")})
        steps  = len({r.get("test_step_id")
                      for r in rows if r.get("test_step_id")})

        lbl = f"●  {total} results"
        if warn:
            lbl += f"  ⚠ {warn[:40]}"
        self._status_lbl.config(text=lbl, fg=GREEN if not warn else GOLD)

        self._c_total.set(total)
        self._c_pass.set(passed)
        self._c_fail.set(failed)
        self._c_other.set(other)
        self._c_plans.set(plans)
        self._c_steps.set(steps)

        # Pass rate bar
        for w in self._bar_wrap.winfo_children(): w.destroy()
        PassRateBar(self._bar_wrap, passed, total).pack(fill="x")

        # Dropdowns
        all_plans = sorted({r.get("test_plan_name") or "Unknown" for r in rows})
        all_stats = sorted({(r.get("status") or "Unknown").capitalize()
                            for r in rows})
        all_areas = sorted({r.get("control_area") or "Unknown" for r in rows})
        all_srcs  = sorted({r.get("_source") or "Unknown" for r in rows})

        def fill_menu(menu, var, default, values, key_fn):
            menu.delete(0, "end")
            menu.add_command(label=default,
                             command=lambda: var.set(default) or self._filter())
            for v in values:
                menu.add_command(label=v,
                                 command=lambda x=v: var.set(x) or self._filter())

        fill_menu(self._plan_menu, self._plan_var, "All Plans",   all_plans, None)
        fill_menu(self._stat_menu, self._stat_var, "All Status",  all_stats, None)
        fill_menu(self._area_menu, self._area_var, "All Areas",   all_areas, None)
        fill_menu(self._src_menu,  self._src_var,  "All Sources", all_srcs,  None)

        try:
            self._plan_strip.rebuild(rows)
        except Exception as e:
            print(f"[WARN] Plan strip rebuild error: {e}")
        self._filter()

    def _filter_by_plan(self, pid):
        self._active_pid = pid
        self._filter()

    def _clear_filter(self):
        self._active_pid = None
        self._plan_var.set("All Plans")
        self._stat_var.set("All Status")
        self._area_var.set("All Areas")
        self._src_var.set("All Sources")
        self._search_var.set("")
        self._filter()

    def _filter(self):
        q    = self._search_var.get().lower().strip()
        plan = self._plan_var.get()
        stat = self._stat_var.get()
        area = self._area_var.get()
        src  = self._src_var.get()

        self._filtered = [
            r for r in self._rows
            if (self._active_pid is None or
                str(r.get("test_plan_id")) == str(self._active_pid))
            and (plan == "All Plans"   or r.get("test_plan_name") == plan)
            and (stat == "All Status"  or
                 (r.get("status") or "").lower() == stat.lower())
            and (area == "All Areas"   or r.get("control_area") == area)
            and (src  == "All Sources" or r.get("_source") == src)
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
            vals = (r.get("_result_id")          or "",
                    r.get("_source")              or "",
                    r.get("test_plan_name")       or "",
                    r.get("control_assertion")    or "",
                    r.get("step_order")           or "",
                    r.get("control_area")         or "",
                    r.get("status")               or "",
                    str(r.get("executed_at") or "")[:19])
            iid = self.tree.insert("", "end", values=vals, tags=(base, stag))
            self._iid_map[iid] = r
        # Don't reset detail panel on every repopulate — only reset if no rows
        if not self._filtered:
            self._detail._idle()

    def _sort(self, col):
        rev = self._sort_state.get(col, False)
        try:
            self._filtered.sort(
                key=lambda r: int(r.get(col) or 0)
                if col == "step_order"
                else str(r.get(col) or ""),
                reverse=rev)
        except Exception:
            self._filtered.sort(
                key=lambda r: str(r.get(col) or ""), reverse=rev)
        self._sort_state[col] = not rev
        self._populate()

    def _on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return
        row = self._iid_map.get(sel[0])
        if row:
            self._detail.show(row)
        else:
            self._detail._idle()

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

