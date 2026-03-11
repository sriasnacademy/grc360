# ui/fix_issue.py
import tkinter as tk
from tkinter import ttk, messagebox
from connectors.lambda_mysql import call_lambda


class FixIssueScreen:

    def __init__(self, parent, current_user_role, current_user, on_close_callback=None):
        self.parent = parent
        self.current_user_role = current_user_role
        self.current_user = current_user
        self.on_close_callback = on_close_callback

        # Use parent directly — no extra Toplevel
        self.window = parent
        self.window.title("Fix Issue")
        self.window.geometry("980x600")
        self.window.configure(bg="#F4F6F9")
        self.window.resizable(True, True)

        self._instance_map = {}
        self._build_ui()
        self._load_issues()

    # ─────────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────────

    def _build_ui(self):
        # Header
        header = tk.Frame(self.window, bg="#1E3A5F", height=55)
        header.pack(fill="x")
        header.pack_propagate(False)

        tk.Label(
            header, text="🔧  Fix Issue",
            font=("Segoe UI", 14, "bold"), fg="white", bg="#1E3A5F"
        ).pack(side="left", padx=20, pady=12)

        tk.Label(
            header, text=f"Role: {self.current_user_role}  |  User: {self.current_user}",
            font=("Segoe UI", 9), fg="#A8C4E0", bg="#1E3A5F"
        ).pack(side="right", padx=20, pady=12)

        # Info bar
        info = tk.Frame(self.window, bg="#EAF2FB", height=32)
        info.pack(fill="x")
        info.pack_propagate(False)
        tk.Label(
            info,
            text="Issues assigned to your role for fixing. Select an issue and choose an action.",
            font=("Segoe UI", 9), fg="#1E3A5F", bg="#EAF2FB"
        ).pack(side="left", padx=16, pady=6)

        # Toolbar
        btn_frame = tk.Frame(self.window, bg="#F4F6F9")
        btn_frame.pack(fill="x", padx=16, pady=(10, 4))

        tk.Button(
            btn_frame, text="🔄  Refresh",
            font=("Segoe UI", 9), bg="#E8EDF2", fg="#1E3A5F",
            relief="flat", cursor="hand2", padx=10,
            command=self._load_issues
        ).pack(side="right")

        tk.Label(
            btn_frame, text="Issues assigned to you:",
            font=("Segoe UI", 10, "bold"), fg="#1E3A5F", bg="#F4F6F9"
        ).pack(side="left")

        # Table
        table_frame = tk.Frame(self.window, bg="#F4F6F9")
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        columns = ("issue_id", "type", "test_plan", "test_cycle", "current_stage", "assigned_to")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=13)

        self.tree.heading("issue_id",      text="Issue ID")
        self.tree.heading("type",         text="Issue type")
        self.tree.heading("test_plan",     text="Test Plan")
        self.tree.heading("test_cycle",    text="Test Cycle")
        self.tree.heading("current_stage", text="Current Stage")
        self.tree.heading("assigned_to",   text="Assigned To")

        self.tree.column("issue_id",      width=75,  anchor="center")
        self.tree.column("type",         width=240, anchor="w")
        self.tree.column("test_plan",     width=160, anchor="w")
        self.tree.column("test_cycle",    width=90,  anchor="center")
        self.tree.column("current_stage", width=160, anchor="center")
        self.tree.column("assigned_to",   width=120, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure("odd",      background="#FFFFFF")
        self.tree.tag_configure("even",     background="#F0F5FB")
        self.tree.tag_configure("closed",   background="#D4EDDA", foreground="#155724")

        # Action bar
        action_bar = tk.Frame(self.window, bg="#E8EDF2", height=56)
        action_bar.pack(fill="x", side="bottom")
        action_bar.pack_propagate(False)

        self.status_label = tk.Label(
            action_bar, text="Select an issue to take action.",
            font=("Segoe UI", 9), fg="#555", bg="#E8EDF2"
        )
        self.status_label.pack(side="left", padx=16, pady=16)

        tk.Button(
            action_bar, text="✖  Close",
            font=("Segoe UI", 10), bg="#E8EDF2", fg="#555",
            relief="flat", cursor="hand2", padx=14,
            command=self.window.destroy
        ).pack(side="right", padx=10, pady=10)

        # Close Issue button (terminal action)
        self.close_btn = tk.Button(
            action_bar, text="🔒  Close Issue",
            font=("Segoe UI", 10, "bold"),
            bg="#DC3545", fg="white",
            relief="flat", cursor="hand2", padx=14,
            command=self._on_close_issue
        )
        self.close_btn.pack(side="right", padx=4, pady=10)

        # Fix Issue button
        self.fix_btn = tk.Button(
            action_bar, text="🔧  Mark as Fixed",
            font=("Segoe UI", 10, "bold"),
            bg="#1E7E34", fg="white",
            relief="flat", cursor="hand2", padx=14,
            command=lambda: self._on_action("fix_issue", "Fix Issue")
        )
        self.fix_btn.pack(side="right", padx=4, pady=10)

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

    # ─────────────────────────────────────────────
    # DATA
    # ─────────────────────────────────────────────

    def _load_issues(self):
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
                        i.issue_type,
                        tp.test_plan_name       AS test_plan,
                        tc.cycle_number    AS test_cycle,
                        ws.stage_name      AS current_stage,
                        i.assigned_to,
                        wi.instance_id,
                        wi.status          AS workflow_status
                    FROM issues i
                    JOIN workflow_instance wi  ON wi.reference_id = i.issue_id
                                              AND wi.module_name  = 'ISSUE'
                    JOIN workflow_stages ws    ON ws.stage_id = wi.current_stage_id
                    LEFT JOIN test_plan tp    ON tp.test_plan_id  = i.test_plan_id
                    LEFT JOIN test_cycle tc    ON tc.cycle_number = wi.cycle_id
                    WHERE i.assigned_to = %s
                    ORDER BY i.issue_id DESC
                """,
                "params": [self.current_user_role]
            }
            response = call_lambda(payload)
            records  = response.get("records", [])

            if not records:
                self.status_label.config(text="No issues assigned to your role.", fg="#888")
                return

            self._instance_map = {
                str(rec["issue_id"]): {
                    "instance_id":     rec["instance_id"],
                    "workflow_status": rec["workflow_status"],
                    "current_stage":   rec["current_stage"]
                }
                for rec in records
            }

            for i, rec in enumerate(records):
                is_closed = rec["workflow_status"] == "COMPLETED"
                tag = "closed" if is_closed else ("even" if i % 2 == 0 else "odd")
                self.tree.insert("", "end", iid=str(rec["issue_id"]), tags=(tag,), values=(
                    rec["issue_id"],
                    rec["issue_type"],
                    rec.get("test_plan",     "—"),
                    f"Cycle {rec.get('test_cycle', '—')}",
                    rec.get("current_stage", "—"),
                    rec.get("assigned_to",   "—"),
                ))

            self.status_label.config(
                text=f"{len(records)} issue(s) found. Select one to take action.",
                fg="#1E3A5F"
            )

        except Exception as e:
            self.status_label.config(text=f"❌ Error: {e}", fg="red")

    # ─────────────────────────────────────────────
    # EVENTS
    # ─────────────────────────────────────────────

    def _on_row_select(self, event):
        selected = self.tree.selection()
        if selected:
            vals = self.tree.item(selected[0], "values")
            info = self._instance_map.get(str(vals[0]), {})
            self.status_label.config(
                text=f"Selected: Issue #{vals[0]} — {vals[1]}  |  Stage: {info.get('current_stage', '—')}",
                fg="#1E3A5F"
            )

    def _get_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an issue first.", parent=self.window)
            return None, None, None
        issue_id  = selected[0]
        info      = self._instance_map.get(str(issue_id), {})
        instance_id = info.get("instance_id")
        vals      = self.tree.item(issue_id, "values")
        return issue_id, instance_id, vals[1]

    # ─────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────

    def _on_action(self, action_name, action_label):
        issue_id, instance_id, type = self._get_selected()
        if not issue_id:
            return

        confirm = messagebox.askyesno(
            f"Confirm: {action_label}",
            f"Mark Issue #{issue_id} as '{action_label}'?\n\n\"{type}\"",
            parent=self.window
        )
        if not confirm:
            return

        self._perform_transition(issue_id, instance_id, action_name, action_label)

    def _on_close_issue(self):
        issue_id, instance_id, type = self._get_selected()
        if not issue_id:
            return

        confirm = messagebox.askyesno(
            "Confirm: Close Issue",
            f"Close Issue #{issue_id}?\n\n\"{type}\"\n\n⚠ This will mark the issue as CLOSED and check if the test plan can be re-executed.",
            parent=self.window
        )
        if not confirm:
            return

        self._perform_transition(issue_id, instance_id, "close_issue", "Close Issue", is_closing=True)

    def _perform_transition(self, issue_id, instance_id, action_name, action_label, is_closing=False):
        try:
            # 1. Get transition details
            t_response = call_lambda({
                "action": "raw_sql",
                "sql": """
                    SELECT wi.current_stage_id, wt.to_stage_id, wi.workflow_id,
                           wt.role_required, ws.stage_name AS next_stage
                    FROM workflow_instance wi
                    JOIN workflow_transitions wt ON wi.current_stage_id = wt.from_stage_id
                                                AND wi.workflow_id      = wt.workflow_id
                    JOIN workflow_stages ws ON ws.stage_id = wt.to_stage_id
                    WHERE wi.instance_id = %s
                    AND wt.action_name   = %s
                    AND wt.active        = 1
                    LIMIT 1
                """,
                "params": [instance_id, action_name]
            })
            t_records = t_response.get("records", [])

            if not t_records:
                messagebox.showerror(
                    "Error",
                    f"No '{action_name}' transition found for current stage.\nCheck workflow_transitions table.",
                    parent=self.window
                )
                return

            from_stage_id = t_records[0]["current_stage_id"]
            to_stage_id   = t_records[0]["to_stage_id"]
            workflow_id   = t_records[0]["workflow_id"]
            next_role     = t_records[0]["role_required"]
            next_stage    = t_records[0]["next_stage"]

            # 2. Update workflow_instance stage
            call_lambda({
                "action": "raw_sql",
                "sql": "UPDATE workflow_instance SET current_stage_id = %s WHERE instance_id = %s",
                "params": [to_stage_id, instance_id]
            })

            # 3. Log workflow_history
            call_lambda({
                "action": "raw_sql",
                "sql": """INSERT INTO workflow_history
                          (instance_id, workflow_id, from_stage_id, to_stage_id,
                           action_performed, performed_by, remarks, performed_at)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
                "params": [
                    instance_id, workflow_id,
                    from_stage_id, to_stage_id,
                    action_name, self.current_user,
                    f"{action_label} performed by {self.current_user}"
                ]
            })

            # 4. Update issues.assigned_to with next role
            call_lambda({
                "action": "raw_sql",
                "sql": """UPDATE issues
                          SET assigned_to = %s, assigned_by = %s, assigned_at = NOW()
                          WHERE issue_id = %s""",
                "params": [next_role, self.current_user, issue_id]
            })

            # 5. If closing — mark workflow COMPLETED and check test plan
            if is_closing:
                call_lambda({
                    "action": "raw_sql",
                    "sql": """UPDATE workflow_instance
                              SET status = 'COMPLETED', completed_at = NOW()
                              WHERE instance_id = %s""",
                    "params": [instance_id]
                })

                # Update issue status to CLOSED
                call_lambda({
                    "action": "raw_sql",
                    "sql": "UPDATE issues SET status = 'CLOSED' WHERE issue_id = %s",
                    "params": [issue_id]
                })

                # Check if all issues in same test plan+cycle are closed
                self._check_and_rerun_plan(issue_id)

                messagebox.showinfo(
                    "Issue Closed",
                    f"✔ Issue #{issue_id} has been CLOSED.\n\nWorkflow completed.",
                    parent=self.window
                )
            else:
                messagebox.showinfo(
                    action_label,
                    f"✔ Issue #{issue_id} — '{action_label}' done.\n\nMoved to: {next_stage}\nAssigned to: {next_role}",
                    parent=self.window
                )

            if self.on_close_callback:
                self.on_close_callback()

            self._load_issues()

        except Exception as e:
            messagebox.showerror("Error", f"Action failed:\n{e}", parent=self.window)

    # ─────────────────────────────────────────────
    # CHECK & RE-RUN TEST PLAN
    # ─────────────────────────────────────────────

    def _check_and_rerun_plan(self, issue_id):
        """
        After closing an issue, check if all issues in the same
        test plan + cycle are closed. If yes, trigger plan re-execution.
        """
        try:
            # Get plan_id and cycle_id for this issue
            info_response = call_lambda({
                "action": "raw_sql",
                "sql": """
                    SELECT i.test_ plan_id, wi.cycle_id
                    FROM issues i
                    JOIN workflow_instance wi ON wi.reference_id = i.issue_id
                                             AND wi.module_name  = 'ISSUE'
                    WHERE i.issue_id = %s
                    LIMIT 1
                """,
                "params": [issue_id]
            })
            info_records = info_response.get("records", [])
            if not info_records:
                return

            plan_id  = info_records[0]["plan_id"]
            cycle_id = info_records[0]["cycle_id"]

            if not plan_id:
                return

            # Count total vs closed issues for this plan+cycle
            count_response = call_lambda({
                "action": "raw_sql",
                "sql": """
                    SELECT
                        COUNT(*)                                        AS total,
                        SUM(CASE WHEN i.issue_status = 'CLOSED' THEN 1 ELSE 0 END) AS closed
                    FROM issues i
                    WHERE i.plan_id = %s
                """,
                "params": [plan_id]
            })
            count_records = count_response.get("records", [])
            if not count_records:
                return

            total  = count_records[0]["total"]  or 0
            closed = count_records[0]["closed"] or 0

            print(f"📊 Plan {plan_id} | Total issues: {total} | Closed: {closed}")

            if total > 0 and total == closed:
                # All issues closed — trigger plan re-execution
                self._trigger_plan_reexecution(plan_id, cycle_id)

        except Exception as e:
            print(f"❌ Error in _check_and_rerun_plan: {e}")

    def _trigger_plan_reexecution(self, plan_id, cycle_id):
        """
        All issues are closed — re-execute the test plan automatically.
        """
        try:
            from runners.control_execution_runner import ControlExecutionRunner

            confirm = messagebox.askyesno(
                "Re-run Test Plan",
                f"✅ All issues for Test Plan #{plan_id} are CLOSED.\n\nDo you want to re-execute the test plan now?",
                parent=self.window
            )
            if not confirm:
                return

            print(f"🔄 Re-executing Test Plan {plan_id}...")
            runner = ControlExecutionRunner()
            report = runner.execute_test_plan(plan_id)

            messagebox.showinfo(
                "Test Plan Re-executed",
                f"✅ Test Plan #{plan_id} has been re-executed.\n\nA new cycle has been created automatically.",
                parent=self.window
            )

            print(f"✅ Re-execution complete. Report: {report}")

        except Exception as e:
            print(f"❌ Error in _trigger_plan_reexecution: {e}")
            messagebox.showerror("Error", f"Failed to re-execute test plan:\n{e}", parent=self.window)