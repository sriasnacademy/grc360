# ui/workflow_tracker.py
import tkinter as tk
from tkinter import ttk
from connectors.lambda_mysql import call_lambda


# ─────────────────────────────────────────────────────────
# DATA LAYER
# ─────────────────────────────────────────────────────────

def fetch_test_plans():
    try:
        response = call_lambda({
            "action": "raw_sql",
            "sql": "SELECT test_plan_id, test_plan_name FROM test_plan ORDER BY test_plan_id DESC",
            "params": []
        })
        return response.get("records", [])
    except Exception as e:
        print("❌ fetch_test_plans:", e)
    return []


def fetch_cycles_for_plan(test_plan_id):
    try:
        response = call_lambda({
            "action": "raw_sql",
            "sql": """
                SELECT cycle_id, cycle_number, run_by, run_at, active
                FROM test_cycle
                WHERE test_plan_id = %s
                ORDER BY cycle_number ASC
            """,
            "params": [test_plan_id]
        })
        return response.get("records", [])
    except Exception as e:
        print("❌ fetch_cycles_for_plan:", e)
    return []


def fetch_issues_for_cycle(test_plan_id, cycle_id):
    try:
        response = call_lambda({
            "action": "raw_sql",
            "sql": """
                SELECT
                    i.issue_id,
                    i.issue_type,
                    i.status           AS issue_status,
                    i.assigned_to,
                    ws.stage_name      AS current_stage,
                    ws.stage_order     AS stage_order,
                    wi.instance_id,
                    wi.status          AS workflow_status,
                    wi.started_at,
                    wi.completed_at,
                    (SELECT COUNT(*) FROM workflow_stages WHERE workflow_id = wi.workflow_id) AS total_stages
                FROM issues i
                JOIN workflow_instance wi ON wi.reference_id = i.issue_id
                                         AND wi.module_name  = 'ISSUE'
                JOIN workflow_stages ws   ON ws.stage_id = wi.current_stage_id
                WHERE i.test_plan_id = %s
                AND wi.cycle_id      = %s
                ORDER BY i.issue_id ASC
            """,
            "params": [test_plan_id, cycle_id]
        })
        return response.get("records", [])
    except Exception as e:
        print("❌ fetch_issues_for_cycle:", e)
    return []


def fetch_workflow_history(instance_id):
    try:
        response = call_lambda({
            "action": "raw_sql",
            "sql": """
                SELECT wh.action_performed, wh.performed_by, wh.remarks, wh.performed_at,
                       fs.stage_name AS from_stage, ts.stage_name AS to_stage
                FROM workflow_history wh
                LEFT JOIN workflow_stages fs ON wh.from_stage_id = fs.stage_id
                LEFT JOIN workflow_stages ts ON wh.to_stage_id   = ts.stage_id
                WHERE wh.instance_id = %s
                ORDER BY wh.performed_at ASC
            """,
            "params": [instance_id]
        })
        return response.get("records", [])
    except Exception as e:
        print("❌ fetch_workflow_history:", e)
    return []


def fetch_all_stages(instance_id):
    try:
        response = call_lambda({
            "action": "raw_sql",
            "sql": """
                SELECT ws.stage_id, ws.stage_name, ws.stage_order, ws.is_terminal
                FROM workflow_instance wi
                JOIN workflow_stages ws ON wi.workflow_id = ws.workflow_id
                WHERE wi.instance_id = %s
                ORDER BY ws.stage_order ASC
            """,
            "params": [instance_id]
        })
        return response.get("records", [])
    except Exception as e:
        print("❌ fetch_all_stages:", e)
    return []


# ─────────────────────────────────────────────────────────
# WORKFLOW TRACKER TAB
# ─────────────────────────────────────────────────────────

class WorkflowTrackerTab:

    # Colours
    C_BG        = "#F0F4F8"
    C_SIDEBAR   = "#1B2A3B"
    C_PANEL     = "#FFFFFF"
    C_ACCENT    = "#2563EB"
    C_GREEN     = "#059669"
    C_AMBER     = "#D97706"
    C_RED       = "#DC2626"
    C_MUTED     = "#6B7280"
    C_BORDER    = "#E2E8F0"
    C_CYCLE_HDR = "#EFF6FF"

    STATUS_META = {
        "ISSUE CLOSED": ("#D1FAE5", "#065F46", "✔  CLOSED"),
        "fix_issue":    ("#FEF3C7", "#92400E", "🔧  FIXED"),
        "OPEN":         ("#FEE2E2", "#991B1B", "⚠  OPEN"),
        "ACTIVE":       ("#DBEAFE", "#1E40AF", "⏳  ACTIVE"),
    }

    def __init__(self, parent_notebook):
        self.tab = tk.Frame(parent_notebook, bg=self.C_BG)
        parent_notebook.add(self.tab, text="Workflow Tracker")
        self._selected_plan_id   = None
        self._selected_cycle_id  = None
        self._plan_buttons        = {}
        self._cycle_buttons       = {}
        self._build()

    # ─────────────────────────────────────────────
    # LAYOUT
    # ─────────────────────────────────────────────

    def _build(self):
        # ── Top bar ──────────────────────────────
        topbar = tk.Frame(self.tab, bg=self.C_SIDEBAR, height=52)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        tk.Label(
            topbar,
            text="⚙   GRC360 — Workflow Tracker",
            font=("Segoe UI", 13, "bold"),
            fg="white", bg=self.C_SIDEBAR
        ).pack(side="left", padx=20, pady=12)

        tk.Button(
            topbar, text="⟳  Refresh",
            font=("Segoe UI", 9, "bold"),
            bg=self.C_ACCENT, fg="white",
            relief="flat", padx=12, pady=4,
            cursor="hand2",
            command=self._load_plans
        ).pack(side="right", padx=16, pady=10)

        # ── Three-column layout ───────────────────
        body = tk.Frame(self.tab, bg=self.C_BG)
        body.pack(fill="both", expand=True)

        # Col 1 — Test Plans
        self._col_plans = self._make_sidebar_col(body, "TEST PLANS", 220)
        self._col_plans.pack(side="left", fill="y")

        tk.Frame(body, bg=self.C_BORDER, width=1).pack(side="left", fill="y")

        # Col 2 — Cycles + Issues
        self._col_cycles = self._make_sidebar_col(body, "CYCLES & ISSUES", 310)
        self._col_cycles.pack(side="left", fill="y")

        tk.Frame(body, bg=self.C_BORDER, width=1).pack(side="left", fill="y")

        # Col 3 — Detail
        self._col_detail = tk.Frame(body, bg=self.C_PANEL)
        self._col_detail.pack(side="left", fill="both", expand=True)

        self._show_placeholder(self._col_detail, "← Select a Test Plan")
        self._load_plans()

    def _make_sidebar_col(self, parent, title, width):
        outer = tk.Frame(parent, bg=self.C_BG, width=width)
        outer.pack_propagate(False)

        hdr = tk.Frame(outer, bg=self.C_SIDEBAR, height=34)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text=title, font=("Segoe UI", 8, "bold"),
                 fg="#93C5FD", bg=self.C_SIDEBAR).pack(side="left", padx=12, pady=8)

        canvas = tk.Canvas(outer, bg=self.C_BG, highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=self.C_BG)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Mouse wheel scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # store inner and canvas for later population
        outer._inner  = inner
        outer._canvas = canvas
        return outer

    # ─────────────────────────────────────────────
    # PLANS
    # ─────────────────────────────────────────────

    def _load_plans(self):
        plans = fetch_test_plans()
        inner = self._col_plans._inner
        for w in inner.winfo_children():
            w.destroy()
        self._plan_buttons = {}

        if not plans:
            tk.Label(inner, text="No plans found.", font=("Segoe UI", 9),
                     fg=self.C_MUTED, bg=self.C_BG).pack(pady=20)
            return

        for plan in plans:
            pid  = plan["test_plan_id"]
            name = plan["test_plan_name"]

            btn = tk.Label(
                inner,
                text=f"  📋  {name}",
                font=("Segoe UI", 9),
                fg="#1E293B", bg=self.C_BG,
                anchor="w", cursor="hand2",
                padx=8, pady=8,
                wraplength=195, justify="left"
            )
            btn.pack(fill="x", padx=4, pady=2)
            btn.bind("<Button-1>", lambda e, p=plan: self._select_plan(p))
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#DBEAFE"))
            btn.bind("<Leave>", lambda e, b=btn, pid=pid: b.configure(
                bg=self.C_ACCENT if pid == self._selected_plan_id else self.C_BG
            ))
            self._plan_buttons[pid] = btn

    def _select_plan(self, plan):
        pid = plan["test_plan_id"]
        self._selected_plan_id  = pid
        self._selected_cycle_id = None

        # Highlight
        for p, b in self._plan_buttons.items():
            b.configure(bg=self.C_ACCENT if p == pid else self.C_BG,
                        fg="white" if p == pid else "#1E293B")

        self._load_cycles(pid)
        self._show_placeholder(self._col_detail, "← Select a Cycle to view issues")

    # ─────────────────────────────────────────────
    # CYCLES
    # ─────────────────────────────────────────────

    def _load_cycles(self, plan_id):
        cycles = fetch_cycles_for_plan(plan_id)
        inner  = self._col_cycles._inner
        for w in inner.winfo_children():
            w.destroy()
        self._cycle_buttons = {}

        if not cycles:
            tk.Label(inner, text="No cycles found.", font=("Segoe UI", 9),
                     fg=self.C_MUTED, bg=self.C_BG).pack(pady=20)
            return

        for cyc in cycles:
            cid    = cyc["cycle_id"]
            cnum   = cyc["cycle_number"]
            run_by = cyc.get("run_by", "—")
            run_at = str(cyc.get("run_at", "—"))[:16]

            card = tk.Frame(inner, bg=self.C_PANEL, bd=1, relief="solid", padx=10, pady=8)
            card.pack(fill="x", padx=6, pady=4)

            tk.Label(card, text=f"Cycle #{cnum}",
                     font=("Segoe UI", 10, "bold"),
                     fg=self.C_ACCENT, bg=self.C_PANEL).pack(anchor="w")
            tk.Label(card, text=f"Run by: {run_by}  |  {run_at}",
                     font=("Segoe UI", 8), fg=self.C_MUTED,
                     bg=self.C_PANEL).pack(anchor="w")

            def _bind_card(card, cyc, cid):
                def on_click(e):
                    self._select_cycle(cyc)
                def on_enter(e):
                    card.configure(bg="#EFF6FF")
                    for w in card.winfo_children():
                        try: w.configure(bg="#EFF6FF")
                        except: pass
                def on_leave(e):
                    clr = self.C_CYCLE_HDR if cid == self._selected_cycle_id else self.C_PANEL
                    card.configure(bg=clr)
                    for w in card.winfo_children():
                        try: w.configure(bg=clr)
                        except: pass

                card.bind("<Button-1>", on_click)
                card.bind("<Enter>", on_enter)
                card.bind("<Leave>", on_leave)
                for w in card.winfo_children():
                    w.bind("<Button-1>", on_click)
                    w.bind("<Enter>", on_enter)
                    w.bind("<Leave>", on_leave)

            _bind_card(card, cyc, cid)
            self._cycle_buttons[cid] = card

    def _select_cycle(self, cyc):
        cid = cyc["cycle_id"]
        self._selected_cycle_id = cid

        for c, card in self._cycle_buttons.items():
            card.configure(bg=self.C_CYCLE_HDR if c == cid else self.C_PANEL)

        issues = fetch_issues_for_cycle(self._selected_plan_id, cid)
        self._render_detail(cyc, issues)

    # ─────────────────────────────────────────────
    # DETAIL PANEL
    # ─────────────────────────────────────────────

    def _show_placeholder(self, parent, msg):
        for w in parent.winfo_children():
            w.destroy()
        tk.Label(parent, text=msg, font=("Segoe UI", 12),
                 fg=self.C_MUTED, bg=self.C_PANEL).pack(expand=True)

    def _render_detail(self, cyc, issues):
        panel = self._col_detail
        for w in panel.winfo_children():
            w.destroy()

        # Scrollable canvas
        canvas = tk.Canvas(panel, bg=self.C_PANEL, highlightthickness=0)
        sb     = ttk.Scrollbar(panel, orient="vertical", command=canvas.yview)
        inner  = tk.Frame(canvas, bg=self.C_PANEL)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=sb.set)
        canvas.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        def _on_mousewheel_detail(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel_detail))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        # ── Cycle header ──────────────────────────
        hdr = tk.Frame(inner, bg=self.C_SIDEBAR, pady=14)
        hdr.pack(fill="x")

        tk.Label(hdr,
                 text=f"Cycle #{cyc['cycle_number']}",
                 font=("Segoe UI", 14, "bold"),
                 fg="white", bg=self.C_SIDEBAR).pack(anchor="w", padx=20)
        tk.Label(hdr,
                 text=f"Run by: {cyc.get('run_by','—')}   Started: {str(cyc.get('run_at','—'))[:16]}",
                 font=("Segoe UI", 9), fg="#93C5FD",
                 bg=self.C_SIDEBAR).pack(anchor="w", padx=20)

        # ── Summary bar ───────────────────────────
        total  = len(issues)
        closed = sum(1 for i in issues if i["issue_status"] == "ISSUE CLOSED")
        fixed  = sum(1 for i in issues if i["issue_status"] == "fix_issue")
        open_  = total - closed - fixed

        sumbar = tk.Frame(inner, bg="#F8FAFC", pady=10)
        sumbar.pack(fill="x", padx=20, pady=(12, 4))

        for label, val, color in [
            ("Total Issues", total, self.C_ACCENT),
            ("Closed",       closed, self.C_GREEN),
            ("Fixed",        fixed,  self.C_AMBER),
            ("Open",         open_,  self.C_RED),
        ]:
            box = tk.Frame(sumbar, bg=color, padx=16, pady=8)
            box.pack(side="left", padx=6)
            tk.Label(box, text=str(val), font=("Segoe UI", 18, "bold"),
                     fg="white", bg=color).pack()
            tk.Label(box, text=label, font=("Segoe UI", 8),
                     fg="white", bg=color).pack()

        tk.Frame(inner, bg=self.C_BORDER, height=1).pack(fill="x", padx=20, pady=10)

        # ── Issue cards ───────────────────────────
        if not issues:
            tk.Label(inner, text="No issues raised in this cycle.",
                     font=("Segoe UI", 10), fg=self.C_MUTED,
                     bg=self.C_PANEL).pack(pady=30)
            return

        tk.Label(inner, text="ISSUES",
                 font=("Segoe UI", 9, "bold"),
                 fg=self.C_MUTED, bg=self.C_PANEL).pack(anchor="w", padx=20, pady=(0, 6))

        for issue in issues:
            self._render_issue_card(inner, issue)

    def _render_issue_card(self, parent, issue):
        status     = issue.get("issue_status", "OPEN")
        wf_status  = issue.get("workflow_status", "ACTIVE")
        stage_ord  = issue.get("stage_order", 1) or 1
        total_stg  = issue.get("total_stages", 1) or 1
        instance_id = issue.get("instance_id")

        # If ISSUE CLOSED → 100%. Otherwise proportional.
        if status == "ISSUE CLOSED" or wf_status == "COMPLETED":
            pct = 100
        else:
            pct = int((stage_ord / total_stg) * 100)

        bg_clr, fg_clr, status_lbl = self.STATUS_META.get(
            status, ("#F3F4F6", "#374151", status)
        )

        # Card frame
        card = tk.Frame(parent, bg=bg_clr, bd=1, relief="solid", padx=14, pady=10)
        card.pack(fill="x", padx=20, pady=5)

        # ── Row 1: Issue ID + status badge ────────
        row1 = tk.Frame(card, bg=bg_clr)
        row1.pack(fill="x")

        tk.Label(row1,
                 text=f"Issue #{issue['issue_id']}",
                 font=("Segoe UI", 11, "bold"),
                 fg=fg_clr, bg=bg_clr).pack(side="left")

        badge = tk.Label(row1, text=status_lbl,
                         font=("Segoe UI", 8, "bold"),
                         fg=fg_clr, bg=bg_clr,
                         relief="solid", bd=1, padx=6, pady=2)
        badge.pack(side="right")

        # ── Row 2: Issue type ─────────────────────
        tk.Label(card,
                 text=issue.get("issue_type", "—"),
                 font=("Segoe UI", 9),
                 fg="#4B5563", bg=bg_clr,
                 wraplength=460, justify="left").pack(anchor="w", pady=(2, 4))

        # ── Row 3: Stage + assigned ───────────────
        row3 = tk.Frame(card, bg=bg_clr)
        row3.pack(fill="x")

        tk.Label(row3,
                 text=f"📍 {issue.get('current_stage','—')}",
                 font=("Segoe UI", 9),
                 fg="#374151", bg=bg_clr).pack(side="left")

        tk.Label(row3,
                 text=f"👤 {issue.get('assigned_to','—')}",
                 font=("Segoe UI", 9),
                 fg=self.C_MUTED, bg=bg_clr).pack(side="right")

        # ── Progress bar ──────────────────────────
        pb_frame = tk.Frame(card, bg=bg_clr)
        pb_frame.pack(fill="x", pady=(6, 2))

        bar_color = "#059669" if pct == 100 else self.C_ACCENT
        style_name = f"Issue{issue['issue_id']}.Horizontal.TProgressbar"
        style = ttk.Style()
        style.configure(style_name,
                        troughcolor=self.C_BORDER,
                        background=bar_color,
                        thickness=10)

        ttk.Progressbar(pb_frame,
                        style=style_name,
                        orient="horizontal",
                        length=400,
                        mode="determinate",
                        value=pct).pack(side="left", fill="x", expand=True)

        tk.Label(pb_frame,
                 text=f"{pct}%",
                 font=("Segoe UI", 9, "bold"),
                 fg=fg_clr, bg=bg_clr).pack(side="left", padx=8)

        # ── Expandable history ─────────────────────
        hist_frame = tk.Frame(card, bg=bg_clr)

        def toggle_history(hf=hist_frame, iid=instance_id):
            if hf.winfo_viewable():
                hf.pack_forget()
            else:
                for w in hf.winfo_children():
                    w.destroy()
                history = fetch_workflow_history(iid)
                if not history:
                    tk.Label(hf, text="No history.",
                             font=("Segoe UI", 8),
                             fg=self.C_MUTED, bg=bg_clr).pack(anchor="w")
                else:
                    for entry in history:
                        self._render_history_row(hf, entry, bg_clr)
                hf.pack(fill="x", pady=(6, 0))

        tk.Button(card,
                  text="▸ View History",
                  font=("Segoe UI", 8),
                  fg=self.C_ACCENT, bg=bg_clr,
                  relief="flat", cursor="hand2",
                  command=toggle_history).pack(anchor="w", pady=(4, 0))

    def _render_history_row(self, parent, entry, bg_clr):
        row = tk.Frame(parent, bg=bg_clr, pady=3)
        row.pack(fill="x")

        tk.Label(row, text="◉",
                 font=("Segoe UI", 9), fg=self.C_ACCENT,
                 bg=bg_clr).pack(side="left", anchor="n", pady=1)

        info = tk.Frame(row, bg="#F1F5F9", bd=1, relief="solid", padx=8, pady=4)
        info.pack(side="left", fill="x", expand=True, padx=6)

        top = tk.Frame(info, bg="#F1F5F9")
        top.pack(fill="x")

        tk.Label(top,
                 text=entry.get("action_performed", ""),
                 font=("Segoe UI", 9, "bold"),
                 fg="#111827", bg="#F1F5F9").pack(side="left")

        tk.Label(top,
                 text=str(entry.get("performed_at", ""))[:16],
                 font=("Segoe UI", 8),
                 fg=self.C_MUTED, bg="#F1F5F9").pack(side="right")

        from_s = entry.get("from_stage") or "—"
        to_s   = entry.get("to_stage")   or "—"
        tk.Label(info,
                 text=f"{from_s}  →  {to_s}",
                 font=("Segoe UI", 8),
                 fg="#4B5563", bg="#F1F5F9").pack(anchor="w")

        meta = f"By: {entry.get('performed_by','—')}"
        if entry.get("remarks"):
            meta += f"   |   {entry['remarks']}"
        tk.Label(info,
                 text=meta,
                 font=("Segoe UI", 8),
                 fg=self.C_MUTED, bg="#F1F5F9",
                 wraplength=380, justify="left").pack(anchor="w")