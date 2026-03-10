# ui/accept_issue_screen.py
import tkinter as tk
from tkinter import ttk, messagebox
from connectors.lambda_mysql import call_lambda


class AcceptIssueScreen:

    def __init__(self, parent, current_user_role, current_user, on_accept_callback=None):
        self.parent = parent
        self.current_user_role = current_user_role
        self.current_user = current_user
        self.on_accept_callback = on_accept_callback

        self.window = tk.Toplevel(parent)
        self.window.title("Accept Issues")
        self.window.geometry("900x560")
        self.window.configure(bg="#F4F6F9")
        self.window.resizable(True, True)
        self.window.grab_set()

        self._build_ui()
        self._load_issues()

    # ─────────────────────────────────────────────
    # UI CONSTRUCTION
    # ─────────────────────────────────────────────

    def _build_ui(self):
        # ── Header
        header = tk.Frame(self.window, bg="#1E3A5F", height=55)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="📋  Accept Issues",
            font=("Segoe UI", 14, "bold"),
            fg="white", bg="#1E3A5F"
        ).pack(side="left", padx=20, pady=12)

        tk.Label(
            header, text=f"Role: {self.current_user_role}  |  User: {self.current_user}",
            font=("Segoe UI", 9),
            fg="#A8C4E0", bg="#1E3A5F"
        ).pack(side="right", padx=20, pady=12)

        # ── Info bar
        info = tk.Frame(self.window, bg="#EAF2FB", height=32)
        info.pack(fill="x")
        info.pack_propagate(False)
        tk.Label(
            info,
            text="Showing issues assigned to your role. Select an issue and click Accept to proceed.",
            font=("Segoe UI", 9), fg="#1E3A5F", bg="#EAF2FB"
        ).pack(side="left", padx=16, pady=6)

        # ── Refresh button
        btn_frame = tk.Frame(self.window, bg="#F4F6F9")
        btn_frame.pack(fill="x", padx=16, pady=(10, 4))

        tk.Button(
            btn_frame, text="🔄  Refresh",
            font=("Segoe UI", 9), bg="#E8EDF2", fg="#1E3A5F",
            relief="flat", cursor="hand2", padx=10,
            command=self._load_issues
        ).pack(side="right")

        tk.Label(
            btn_frame, text="Issues pending your acceptance:",
            font=("Segoe UI", 10, "bold"), fg="#1E3A5F", bg="#F4F6F9"
        ).pack(side="left")

        # ── Table
        table_frame = tk.Frame(self.window, bg="#F4F6F9")
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        columns = ("issue_id", "title", "test_plan", "test_cycle", "assigned_to")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)

        # Column definitions
        self.tree.heading("issue_id",    text="Issue ID")
        self.tree.heading("title",       text="Issue Title")
        self.tree.heading("test_plan",   text="Test Plan")
        self.tree.heading("test_cycle",  text="Test Cycle")
        self.tree.heading("assigned_to", text="Assigned To")

        self.tree.column("issue_id",    width=80,  anchor="center")
        self.tree.column("title",       width=280, anchor="w")
        self.tree.column("test_plan",   width=180, anchor="w")
        self.tree.column("test_cycle",  width=100, anchor="center")
        self.tree.column("assigned_to", width=140, anchor="center")

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        # Row styling
        self.tree.tag_configure("odd",  background="#FFFFFF")
        self.tree.tag_configure("even", background="#F0F5FB")

        # ── Bottom action bar
        action_bar = tk.Frame(self.window, bg="#E8EDF2", height=56)
        action_bar.pack(fill="x", side="bottom")
        action_bar.pack_propagate(False)

        self.status_label = tk.Label(
            action_bar, text="Select an issue to accept.",
            font=("Segoe UI", 9), fg="#555", bg="#E8EDF2"
        )
        self.status_label.pack(side="left", padx=16, pady=16)

        tk.Button(
            action_bar, text="✖  Close",
            font=("Segoe UI", 10), bg="#E8EDF2", fg="#555",
            relief="flat", cursor="hand2", padx=14,
            command=self.window.destroy
        ).pack(side="right", padx=10, pady=10)

        self.accept_btn = tk.Button(
            action_bar, text="✔  Accept Issue",
            font=("Segoe UI", 10, "bold"),
            bg="#1E7E34", fg="white",
            relief="flat", cursor="hand2", padx=16,
            command=self._on_accept
        )
        self.accept_btn.pack(side="right", padx=4, pady=10)

        # Bind selection
        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    # ─────────────────────────────────────────────
    # DATA LOADING
    # ─────────────────────────────────────────────

    def _load_issues(self):
        """Load issues assigned to current user's role that are pending acceptance."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        self.status_label.config(text="Loading...", fg="#555")
        self.window.update()

        try:
            payload = {
                "action": "raw_sql",
                "sql": """
                    SELECT 
                        i.issue_id,
                        i.issue_title,
                        tp.plan_name      AS test_plan,
                        tc.cycle_number   AS test_cycle,
                        i.assigned_to,
                        wi.instance_id,
                        ws.stage_name     AS current_stage
                    FROM issues i
                    JOIN workflow_instance wi  ON wi.reference_id = i.issue_id
                                              AND wi.module_name = 'ISSUE'
                                              AND wi.status = 'ACTIVE'
                    JOIN workflow_stages ws    ON ws.stage_id = wi.current_stage_id
                    LEFT JOIN test_plans tp    ON tp.plan_id = i.plan_id
                    LEFT JOIN test_cycle tc    ON tc.cycle_id = wi.cycle_id
                    WHERE i.assigned_to = %s
                    ORDER BY i.issue_id DESC
                """,
                "params": [self.current_user_role]
            }
            response = call_lambda(payload)
            records = response.get("records", [])

            if not records:
                self.status_label.config(text="No issues assigned to your role.", fg="#888")
                return

            for i, rec in enumerate(records):
                tag = "even" if i % 2 == 0 else "odd"
                self.tree.insert("", "end", iid=str(rec["issue_id"]), tags=(tag,), values=(
                    rec["issue_id"],
                    rec["issue_title"],
                    rec.get("test_plan", "—"),
                    f"Cycle {rec.get('test_cycle', '—')}",
                    rec.get("assigned_to", "—"),
                ))
                # Store instance_id hidden per row
                self.tree.set(str(rec["issue_id"]), "issue_id", rec["issue_id"])
                self._instance_map = {
                    str(rec["issue_id"]): rec["instance_id"]
                    for rec in records
                }

            self.status_label.config(
                text=f"{len(records)} issue(s) found. Select one to accept.",
                fg="#1E3A5F"
            )

        except Exception as e:
            self.status_label.config(text=f"❌ Error loading issues: {e}", fg="red")

    # ─────────────────────────────────────────────
    # EVENTS
    # ─────────────────────────────────────────────

    def _on_row_select(self, event):
        selected = self.tree.selection()
        if selected:
            vals = self.tree.item(selected[0], "values")
            self.status_label.config(
                text=f"Selected: Issue #{vals[0]} — {vals[1]}",
                fg="#1E3A5F"
            )

    def _on_accept(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an issue to accept.", parent=self.window)
            return

        issue_id = selected[0]
        instance_id = self._instance_map.get(str(issue_id))
        vals = self.tree.item(issue_id, "values")
        issue_title = vals[1]

        confirm = messagebox.askyesno(
            "Confirm Accept",
            f"Accept Issue #{issue_id}?\n\n\"{issue_title}\"\n\nThis will move the workflow to the next stage and assign it to the responsible person.",
            parent=self.window
        )
        if not confirm:
            return

        self._accept_issue(issue_id, instance_id)

    def _accept_issue(self, issue_id, instance_id):
        """
        1. Get next role from workflow_transitions for 'accept_issue' action
        2. Update issues.assigned_to with next role
        3. Transition workflow stage
        """
        try:
            # 1. Get next role from workflow_transitions
            role_payload = {
                "action": "raw_sql",
                "sql": """
                    SELECT wt.role_required, wt.to_stage_id, ws.stage_name AS next_stage
                    FROM workflow_instance wi
                    JOIN workflow_transitions wt ON wi.current_stage_id = wt.from_stage_id
                                                AND wi.workflow_id = wt.workflow_id
                    JOIN workflow_stages ws ON ws.stage_id = wt.to_stage_id
                    WHERE wi.instance_id = %s
                    AND wt.action_name = 'accept_issue'
                    AND wt.active = 1
                    LIMIT 1
                """,
                "params": [instance_id]
            }
            response = call_lambda(role_payload)
            records = response.get("records", [])

            if not records:
                messagebox.showerror("Error", "No 'accept_issue' transition found for this stage.", parent=self.window)
                return

            next_role  = records[0]["role_required"]
            next_stage = records[0]["next_stage"]

            # 2. Update issues.assigned_to with next role
            update_payload = {
                "action": "raw_sql",
                "sql": """UPDATE issues 
                          SET assigned_to = %s, assigned_by = %s, assigned_at = NOW()
                          WHERE issue_id = %s""",
                "params": [next_role, self.current_user, issue_id]
            }
            call_lambda(update_payload)

            # 3. Transition workflow stage + log history
            transition_payload = {
                "action": "raw_sql",
                "sql": """
                    SELECT wi.current_stage_id, wt.to_stage_id, wi.workflow_id
                    FROM workflow_instance wi
                    JOIN workflow_transitions wt ON wi.current_stage_id = wt.from_stage_id
                                                AND wi.workflow_id = wt.workflow_id
                    WHERE wi.instance_id = %s AND wt.action_name = 'accept_issue' AND wt.active = 1
                    LIMIT 1
                """,
                "params": [instance_id]
            }
            t_response = call_lambda(transition_payload)
            t_records  = t_response.get("records", [])

            if t_records:
                from_stage_id = t_records[0]["current_stage_id"]
                to_stage_id   = t_records[0]["to_stage_id"]
                workflow_id   = t_records[0]["workflow_id"]

                # Update workflow_instance stage
                call_lambda({
                    "action": "raw_sql",
                    "sql": "UPDATE workflow_instance SET current_stage_id = %s WHERE instance_id = %s",
                    "params": [to_stage_id, instance_id]
                })

                # Log workflow_history
                call_lambda({
                    "action": "raw_sql",
                    "sql": """INSERT INTO workflow_history 
                              (instance_id, workflow_id, from_stage_id, to_stage_id, 
                               action_performed, performed_by, remarks, performed_at)
                              VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
                    "params": [
                        instance_id, workflow_id,
                        from_stage_id, to_stage_id,
                        "accept_issue", self.current_user,
                        f"Issue accepted by {self.current_user}. Assigned to role: {next_role}"
                    ]
                })

            messagebox.showinfo(
                "Issue Accepted",
                f"✔ Issue #{issue_id} accepted.\n\nMoved to: {next_stage}\nAssigned to: {next_role}",
                parent=self.window
            )

            # Callback to refresh parent if provided
            if self.on_accept_callback:
                self.on_accept_callback()

            # Refresh table
            self._load_issues()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to accept issue:\n{e}", parent=self.window)