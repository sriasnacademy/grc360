import tkinter as tk
from tkinter import ttk
from connectors.lambda_mysql import call_lambda


# ─────────────────────────────────────────────────────────
# DATA LAYER
# ─────────────────────────────────────────────────────────

def fetch_workflow_instances():
    payload = {
        "action": "raw_sql",
        "sql": """
            SELECT 
                wi.instance_id,
                wi.reference_id,
                wi.module_name,
                wi.status,
                wi.started_at,
                wi.completed_at,
                ws.stage_name AS current_stage,
                ws.stage_order,
                wd.workflow_name,
                (SELECT COUNT(*) FROM workflow_stages WHERE workflow_id = wi.workflow_id) AS total_stages
            FROM workflow_instance wi
            JOIN workflow_stages ws ON wi.current_stage_id = ws.stage_id
            JOIN workflow_definitions wd ON wi.workflow_id = wd.workflow_id
            ORDER BY wi.started_at DESC
        """,
        "params": []
    }
    try:
        response = call_lambda(payload)
        return response.get("records", [])
    except Exception as e:
        print("❌ fetch_workflow_instances:", e)
    return []


def fetch_available_transitions(instance_id):
    payload = {
        "action": "raw_sql",
        "sql": """
            SELECT wt.transition_id, wt.action_name, wt.to_stage_id, wt.role_required,
                   ws.stage_name AS to_stage_name
            FROM workflow_instance wi
            JOIN workflow_transitions wt ON wi.current_stage_id = wt.from_stage_id
                                        AND wi.workflow_id = wt.workflow_id
            JOIN workflow_stages ws ON wt.to_stage_id = ws.stage_id
            WHERE wi.instance_id = %s AND wt.active = 1
        """,
        "params": [instance_id]
    }
    try:
        response = call_lambda(payload)
        return response.get("records", [])
    except Exception as e:
        print("❌ fetch_available_transitions:", e)
    return []


def fetch_workflow_history(instance_id):
    payload = {
        "action": "raw_sql",
        "sql": """
            SELECT wh.action_performed, wh.performed_by, wh.remarks, wh.performed_at,
                   fs.stage_name AS from_stage, ts.stage_name AS to_stage
            FROM workflow_history wh
            LEFT JOIN workflow_stages fs ON wh.from_stage_id = fs.stage_id
            LEFT JOIN workflow_stages ts ON wh.to_stage_id = ts.stage_id
            WHERE wh.instance_id = %s
            ORDER BY wh.performed_at ASC
        """,
        "params": [instance_id]
    }
    try:
        response = call_lambda(payload)
        return response.get("records", [])
    except Exception as e:
        print("❌ fetch_workflow_history:", e)
    return []


def fetch_all_stages(instance_id):
    payload = {
        "action": "raw_sql",
        "sql": """
            SELECT ws.stage_id, ws.stage_name, ws.stage_order, ws.is_terminal
            FROM workflow_instance wi
            JOIN workflow_stages ws ON wi.workflow_id = ws.workflow_id
            WHERE wi.instance_id = %s
            ORDER BY ws.stage_order ASC
        """,
        "params": [instance_id]
    }
    try:
        response = call_lambda(payload)
        return response.get("records", [])
    except Exception as e:
        print("❌ fetch_all_stages:", e)
    return []


# ─────────────────────────────────────────────────────────
# WORKFLOW TRACKER TAB
# ─────────────────────────────────────────────────────────

class WorkflowTrackerTab:

    STAGE_COLORS = {
        "done":    {"bg": "#D1FAE5", "fg": "#065F46", "circle": "#10B981"},
        "active":  {"bg": "#DBEAFE", "fg": "#1E40AF", "circle": "#3B82F6"},
        "pending": {"bg": "#F3F4F6", "fg": "#9CA3AF", "circle": "#D1D5DB"},
    }

    STATUS_COLORS = {
        "ACTIVE":    ("#EFF6FF", "#1D4ED8"),
        "COMPLETED": ("#ECFDF5", "#065F46"),
        "CANCELLED": ("#FEF2F2", "#991B1B"),
    }

    def __init__(self, parent_notebook):
        self.tab = tk.Frame(parent_notebook, bg="#F9FAFB")
        parent_notebook.add(self.tab, text="Workflow Tracker")
        self._build()

    def _build(self):
        # ── Top bar ──
        topbar = tk.Frame(self.tab, bg="#1E3A5F", pady=12)
        topbar.pack(fill="x")

        tk.Label(
            topbar,
            text="⚙  Workflow Instance Tracker",
            font=("Segoe UI", 14, "bold"),
            fg="white", bg="#1E3A5F"
        ).pack(side="left", padx=20)

        tk.Button(
            topbar,
            text="⟳  Refresh",
            font=("Segoe UI", 10, "bold"),
            bg="#3B82F6", fg="white",
            relief="flat", padx=12, pady=4,
            cursor="hand2",
            command=self._load_instances
        ).pack(side="right", padx=20)

        # ── Search ──
        search_bar = tk.Frame(self.tab, bg="#F9FAFB", pady=8)
        search_bar.pack(fill="x", padx=20)

        tk.Label(search_bar, text="🔍", font=("Segoe UI", 12), bg="#F9FAFB").pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_instances())
        tk.Entry(
            search_bar,
            textvariable=self.search_var,
            font=("Segoe UI", 11),
            width=35,
            relief="solid", bd=1
        ).pack(side="left", padx=8)

        # ── Status filter ──
        tk.Label(search_bar, text="Status:", font=("Segoe UI", 10), bg="#F9FAFB").pack(side="left", padx=(20, 4))
        self.status_filter = ttk.Combobox(
            search_bar,
            values=["All", "ACTIVE", "COMPLETED", "CANCELLED"],
            width=12, state="readonly", font=("Segoe UI", 10)
        )
        self.status_filter.set("All")
        self.status_filter.bind("<<ComboboxSelected>>", lambda *_: self._filter_instances())
        self.status_filter.pack(side="left")

        # ── Main split ──
        pane = tk.PanedWindow(self.tab, orient="horizontal", bg="#E5E7EB", sashwidth=4)
        pane.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # LEFT: instance list
        left = tk.Frame(pane, bg="#F9FAFB")
        pane.add(left, minsize=340)

        tk.Label(
            left,
            text="Instances",
            font=("Segoe UI", 11, "bold"),
            bg="#F9FAFB", fg="#374151"
        ).pack(anchor="w", padx=10, pady=(8, 4))

        list_container = tk.Frame(left, bg="#F9FAFB")
        list_container.pack(fill="both", expand=True)

        self.list_canvas = tk.Canvas(list_container, bg="#F9FAFB", highlightthickness=0)
        list_scroll = ttk.Scrollbar(list_container, orient="vertical", command=self.list_canvas.yview)
        self.list_inner = tk.Frame(self.list_canvas, bg="#F9FAFB")

        self.list_inner.bind(
            "<Configure>",
            lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all"))
        )
        self.list_canvas.create_window((0, 0), window=self.list_inner, anchor="nw")
        self.list_canvas.configure(yscrollcommand=list_scroll.set)

        self.list_canvas.pack(side="left", fill="both", expand=True)
        list_scroll.pack(side="right", fill="y")

        # RIGHT: detail panel
        self.right = tk.Frame(pane, bg="white")
        pane.add(self.right, minsize=500)

        self._show_empty_detail()
        self._load_instances()

    # ─────────────────────────────────────────────
    # LOAD & FILTER
    # ─────────────────────────────────────────────

    def _load_instances(self):
        self.all_instances = fetch_workflow_instances()
        self._filter_instances()

    def _filter_instances(self):
        keyword = self.search_var.get().lower()
        status_f = self.status_filter.get()

        filtered = [
            i for i in self.all_instances
            if keyword in (
                str(i.get("reference_id", "")) +
                i.get("module_name", "") +
                i.get("workflow_name", "") +
                i.get("current_stage", "")
            ).lower()
            and (status_f == "All" or i.get("status") == status_f)
        ]
        self._render_instance_list(filtered)

    # ─────────────────────────────────────────────
    # LEFT PANEL: INSTANCE LIST
    # ─────────────────────────────────────────────

    def _render_instance_list(self, instances):
        for w in self.list_inner.winfo_children():
            w.destroy()

        if not instances:
            tk.Label(
                self.list_inner,
                text="No instances found.",
                font=("Segoe UI", 10),
                fg="#9CA3AF", bg="#F9FAFB"
            ).pack(pady=30)
            return

        for inst in instances:
            self._create_instance_card(inst)

    def _create_instance_card(self, inst):
        status = inst.get("status", "ACTIVE")
        bg_color, fg_color = self.STATUS_COLORS.get(status, ("#F9FAFB", "#374151"))

        card = tk.Frame(
            self.list_inner,
            bg=bg_color, bd=1, relief="solid",
            padx=12, pady=8, cursor="hand2"
        )
        card.pack(fill="x", padx=8, pady=4)

        # Header row
        header = tk.Frame(card, bg=bg_color)
        header.pack(fill="x")

        tk.Label(
            header,
            text=f"#{inst['instance_id']}  {inst.get('module_name', '')} — Ref {inst['reference_id']}",
            font=("Segoe UI", 10, "bold"),
            fg=fg_color, bg=bg_color
        ).pack(side="left")

        tk.Label(
            header,
            text=status,
            font=("Segoe UI", 8, "bold"),
            fg=fg_color, bg=bg_color
        ).pack(side="right")

        # Stage
        tk.Label(
            card,
            text=f"📍 {inst.get('current_stage', '—')}",
            font=("Segoe UI", 9),
            fg="#4B5563", bg=bg_color
        ).pack(anchor="w", pady=(2, 0))

        # Progress bar
        total = inst.get("total_stages", 1) or 1
        order = inst.get("stage_order", 1) or 1
        pct = int((order / total) * 100)

        pb_frame = tk.Frame(card, bg=bg_color)
        pb_frame.pack(fill="x", pady=(4, 0))

        ttk.Progressbar(
            pb_frame,
            orient="horizontal",
            length=200,
            mode="determinate",
            value=pct
        ).pack(side="left")

        tk.Label(
            pb_frame,
            text=f"{pct}%",
            font=("Segoe UI", 8),
            fg="#6B7280", bg=bg_color
        ).pack(side="left", padx=6)

        # Started at
        tk.Label(
            card,
            text=f"Started: {inst.get('started_at', '—')}",
            font=("Segoe UI", 8),
            fg="#9CA3AF", bg=bg_color
        ).pack(anchor="w")

        # Click binding
        for widget in [card, header] + card.winfo_children():
            widget.bind("<Button-1>", lambda e, i=inst: self._show_detail(i))

        card.bind("<Enter>", lambda e, c=card, b=bg_color: c.configure(relief="groove"))
        card.bind("<Leave>", lambda e, c=card: c.configure(relief="solid"))

    # ─────────────────────────────────────────────
    # RIGHT PANEL: DETAIL VIEW
    # ─────────────────────────────────────────────

    def _clear_detail(self):
        for w in self.right.winfo_children():
            w.destroy()

    def _show_empty_detail(self):
        self._clear_detail()
        tk.Label(
            self.right,
            text="← Select an instance to view details",
            font=("Segoe UI", 12),
            fg="#9CA3AF", bg="white"
        ).pack(expand=True)

    def _show_detail(self, inst):
        self._clear_detail()

        instance_id = inst["instance_id"]

        # Scrollable detail
        canvas = tk.Canvas(self.right, bg="white", highlightthickness=0)
        scroll = ttk.Scrollbar(self.right, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="white")

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scroll.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

        # ── Header ──
        hdr = tk.Frame(inner, bg="#1E3A5F", pady=14)
        hdr.pack(fill="x")

        tk.Label(
            hdr,
            text=f"Instance #{instance_id}  ·  {inst.get('module_name','')} Ref:{inst['reference_id']}",
            font=("Segoe UI", 13, "bold"),
            fg="white", bg="#1E3A5F"
        ).pack(anchor="w", padx=20)

        tk.Label(
            hdr,
            text=inst.get("workflow_name", ""),
            font=("Segoe UI", 10),
            fg="#93C5FD", bg="#1E3A5F"
        ).pack(anchor="w", padx=20)

        # ── Stage Pipeline ──
        self._render_stage_pipeline(inner, instance_id, inst.get("stage_order", 1))

        # ── Available Actions ──
        self._render_actions_panel(inner, instance_id)

        # ── History ──
        self._render_history(inner, instance_id)

    # ─────────────────────────────────────────────
    # STAGE PIPELINE
    # ─────────────────────────────────────────────

    def _render_stage_pipeline(self, parent, instance_id, current_order):
        stages = fetch_all_stages(instance_id)
        if not stages:
            return

        section = tk.Frame(parent, bg="white", pady=10)
        section.pack(fill="x", padx=20)

        tk.Label(
            section,
            text="STAGE PIPELINE",
            font=("Segoe UI", 9, "bold"),
            fg="#6B7280", bg="white"
        ).pack(anchor="w", pady=(0, 8))

        pipeline = tk.Frame(section, bg="white")
        pipeline.pack(fill="x")

        for idx, stage in enumerate(stages):
            order = stage.get("stage_order", idx + 1)

            if order < current_order:
                state = "done"
                icon = "✓"
            elif order == current_order:
                state = "active"
                icon = "●"
            else:
                state = "pending"
                icon = str(order)

            colors = self.STAGE_COLORS[state]

            col = tk.Frame(pipeline, bg="white")
            col.pack(side="left", padx=4)

            # Circle
            circle = tk.Label(
                col,
                text=icon,
                font=("Segoe UI", 9, "bold"),
                fg=colors["fg"],
                bg=colors["circle"],
                width=3, height=1,
                relief="flat"
            )
            circle.pack()

            # Label
            tk.Label(
                col,
                text=stage["stage_name"],
                font=("Segoe UI", 8),
                fg=colors["fg"],
                bg="white",
                wraplength=70,
                justify="center"
            ).pack()

            # Connector arrow (not after last)
            if idx < len(stages) - 1:
                tk.Label(
                    pipeline,
                    text="→",
                    font=("Segoe UI", 12),
                    fg="#D1D5DB", bg="white"
                ).pack(side="left", pady=0)

        # Separator
        tk.Frame(parent, bg="#E5E7EB", height=1).pack(fill="x", padx=20, pady=8)

    # ─────────────────────────────────────────────
    # AVAILABLE ACTIONS
    # ─────────────────────────────────────────────

    def _render_actions_panel(self, parent, instance_id):
        transitions = fetch_available_transitions(instance_id)

        section = tk.Frame(parent, bg="white", pady=6)
        section.pack(fill="x", padx=20)

        tk.Label(
            section,
            text="AVAILABLE NEXT ACTIONS",
            font=("Segoe UI", 9, "bold"),
            fg="#6B7280", bg="white"
        ).pack(anchor="w", pady=(0, 6))

        if not transitions:
            tk.Label(
                section,
                text="No actions available (terminal stage or workflow complete).",
                font=("Segoe UI", 9),
                fg="#9CA3AF", bg="white"
            ).pack(anchor="w")
        else:
            for t in transitions:
                row = tk.Frame(section, bg="#EFF6FF", bd=1, relief="solid", padx=10, pady=6)
                row.pack(fill="x", pady=3)

                tk.Label(
                    row,
                    text=f"▶  {t['action_name']}",
                    font=("Segoe UI", 10, "bold"),
                    fg="#1D4ED8", bg="#EFF6FF"
                ).pack(side="left")

                tk.Label(
                    row,
                    text=f"→ {t['to_stage_name']}",
                    font=("Segoe UI", 9),
                    fg="#3B82F6", bg="#EFF6FF"
                ).pack(side="left", padx=10)

                if t.get("role_required"):
                    tk.Label(
                        row,
                        text=f"🔒 {t['role_required']}",
                        font=("Segoe UI", 8),
                        fg="#6B7280", bg="#EFF6FF"
                    ).pack(side="right")

        tk.Frame(parent, bg="#E5E7EB", height=1).pack(fill="x", padx=20, pady=8)

    # ─────────────────────────────────────────────
    # HISTORY TIMELINE
    # ─────────────────────────────────────────────

    def _render_history(self, parent, instance_id):
        history = fetch_workflow_history(instance_id)

        section = tk.Frame(parent, bg="white", pady=6)
        section.pack(fill="x", padx=20, pady=(0, 20))

        tk.Label(
            section,
            text="HISTORY TIMELINE",
            font=("Segoe UI", 9, "bold"),
            fg="#6B7280", bg="white"
        ).pack(anchor="w", pady=(0, 6))

        if not history:
            tk.Label(
                section,
                text="No history available.",
                font=("Segoe UI", 9),
                fg="#9CA3AF", bg="white"
            ).pack(anchor="w")
            return

        for entry in history:
            row = tk.Frame(section, bg="white")
            row.pack(fill="x", pady=2)

            # Timeline dot
            tk.Label(
                row,
                text="◉",
                font=("Segoe UI", 10),
                fg="#3B82F6", bg="white"
            ).pack(side="left", anchor="n", pady=2)

            info = tk.Frame(row, bg="#F9FAFB", bd=1, relief="solid", padx=10, pady=6)
            info.pack(side="left", fill="x", expand=True, padx=8)

            # Action + time
            top_row = tk.Frame(info, bg="#F9FAFB")
            top_row.pack(fill="x")

            tk.Label(
                top_row,
                text=entry.get("action_performed", ""),
                font=("Segoe UI", 10, "bold"),
                fg="#111827", bg="#F9FAFB"
            ).pack(side="left")

            tk.Label(
                top_row,
                text=str(entry.get("performed_at", "")),
                font=("Segoe UI", 8),
                fg="#9CA3AF", bg="#F9FAFB"
            ).pack(side="right")

            # Stage transition
            from_s = entry.get("from_stage") or "—"
            to_s = entry.get("to_stage") or "—"
            tk.Label(
                info,
                text=f"{from_s}  →  {to_s}",
                font=("Segoe UI", 9),
                fg="#4B5563", bg="#F9FAFB"
            ).pack(anchor="w")

            # Performed by + remarks
            meta = f"By: {entry.get('performed_by', '—')}"
            if entry.get("remarks"):
                meta += f"   |   {entry['remarks']}"

            tk.Label(
                info,
                text=meta,
                font=("Segoe UI", 8),
                fg="#6B7280", bg="#F9FAFB",
                wraplength=400,
                justify="left"
            ).pack(anchor="w")