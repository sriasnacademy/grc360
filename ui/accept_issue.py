# ui/accept_issue.py
import tkinter as tk
from tkinter import ttk, messagebox
from connectors.lambda_mysql import call_lambda


class AcceptIssueScreen:

    def __init__(self, parent, current_user_role, current_user, on_accept_callback=None):
        self.parent = parent
        self.current_user_role = current_user_role
        self.current_user = current_user
        self.on_accept_callback = on_accept_callback

        self.window = parent
        self.window.title("Accept Issues")
        self.window.geometry("1000x560")
        self.window.configure(bg="#F4F6F9")
        self.window.resizable(True, True)

        self._instance_map = {}
        self._build_ui()
        self._load_issues()

    def _build_ui(self):
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

        info = tk.Frame(self.window, bg="#EAF2FB", height=32)
        info.pack(fill="x")
        info.pack_propagate(False)
        tk.Label(
            info,
            text="Showing issues assigned to your role. Select an issue and click Accept to proceed.",
            font=("Segoe UI", 9), fg="#1E3A5F", bg="#EAF2FB"
        ).pack(side="left", padx=16, pady=6)

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

        table_frame = tk.Frame(self.window, bg="#F4F6F9")
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        columns = ("issue_id", "plan_id", "cycle_id", "type", "test_plan", "cycle_number", "current_stage", "assigned_to")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=14)

        self.tree.heading("issue_id",      text="Issue ID")
        self.tree.heading("plan_id",       text="Plan ID")
        self.tree.heading("cycle_id",      text="Cycle ID")
        self.tree.heading("type",          text="Issue Type")
        self.tree.heading("test_plan",     text="Test Plan")
        self.tree.heading("cycle_number",  text="Cycle #")
        self.tree.heading("current_stage", text="Current Stage")
        self.tree.heading("assigned_to",   text="Assigned To")

        self.tree.column("issue_id",      width=70,  anchor="center")
        self.tree.column("plan_id",       width=65,  anchor="center")
        self.tree.column("cycle_id",      width=65,  anchor="center")
        self.tree.column("type",          width=200, anchor="w")
        self.tree.column("test_plan",     width=160, anchor="w")
        self.tree.column("cycle_number",  width=60,  anchor="center")
        self.tree.column("current_stage", width=140, anchor="center")
        self.tree.column("assigned_to",   width=110, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure("odd",  background="#FFFFFF")
        self.tree.tag_configure("even", background="#F0F5FB")

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

        self.tree.bind("<<TreeviewSelect>>", self._on_row_select)

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
                        i.test_plan_id,
                        tp.test_plan_name  AS test_plan,
                        tc.cycle_id        AS cycle_id,
                        tc.cycle_number    AS cycle_number,
                        i.assigned_to,
                        wi.instance_id,
                        ws.stage_name      AS current_stage
                    FROM issues i
                    JOIN workflow_instance wi  ON wi.reference_id = i.issue_id
                                              AND wi.module_name  = 'ISSUE'
                                              AND wi.status       = 'ACTIVE'
                    JOIN workflow_stages ws    ON ws.stage_id = wi.current_stage_id
                    LEFT JOIN test_plan tp     ON tp.test_plan_id = i.test_plan_id
                    LEFT JOIN test_cycle tc    ON tc.cycle_id     = wi.cycle_id
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
                str(rec["issue_id"]): rec["instance_id"]
                for rec in records
            }

            for i, rec in enumerate(records):
                tag = "even" if i % 2 == 0 else "odd"
                self.tree.insert("", "end", iid=str(rec["issue_id"]), tags=(tag,), values=(
                    rec["issue_id"],
                    rec.get("test_plan_id",  "—"),
                    rec.get("cycle_id",      "—"),
                    rec["issue_type"],
                    rec.get("test_plan",     "—"),
                    rec.get("cycle_number",  "—"),
                    rec.get("current_stage", "—"),
                    rec.get("assigned_to",   "—"),
                ))

            self.status_label.config(
                text=f"{len(records)} issue(s) found. Select one to accept.",
                fg="#1E3A5F"
            )

        except Exception as e:
            self.status_label.config(text=f"❌ Error loading issues: {e}", fg="red")

    def _on_row_select(self, event):
        selected = self.tree.selection()
        if selected:
            vals = self.tree.item(selected[0], "values")
            # vals: issue_id, plan_id, cycle_id, type, test_plan, cycle_number, stage, assigned_to
            self.status_label.config(
                text=f"Selected: Issue #{vals[0]}  |  Plan ID: {vals[1]}  |  Cycle ID: {vals[2]}  |  Cycle #: {vals[5]}  |  Stage: {vals[6]}",
                fg="#1E3A5F"
            )

    def _on_accept(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an issue to accept.", parent=self.window)
            return

        issue_id    = selected[0]
        instance_id = self._instance_map.get(str(issue_id))
        vals        = self.tree.item(issue_id, "values")
        issue_type  = vals[3]
        plan_name   = vals[4]
        cycle_num   = vals[5]

        confirm = messagebox.askyesno(
            "Confirm Accept",
            f"Accept Issue #{issue_id}?\n\n"
            f"Type: {issue_type}\n"
            f"Test Plan: {plan_name}  |  Cycle #: {cycle_num}\n\n"
            f"This will move the workflow to the next stage.",
            parent=self.window
        )
        if not confirm:
            return

        self._accept_issue(issue_id, instance_id)

    def _accept_issue(self, issue_id, instance_id):
        try:
            # Get transition details
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
                    AND wt.action_name   = 'accept_and_assign_issue'
                    AND wt.active        = 1
                    LIMIT 1
                """,
                "params": [instance_id]
            })
            t_records = t_response.get("records", [])

            if not t_records:
                messagebox.showerror(
                    "Error",
                    "No 'accept_and_assign_issue' transition found for this stage.\nCheck workflow_transitions table.",
                    parent=self.window
                )
                return

            from_stage_id = t_records[0]["current_stage_id"]
            to_stage_id   = t_records[0]["to_stage_id"]
            workflow_id   = t_records[0]["workflow_id"]
            next_role     = t_records[0]["role_required"]
            next_stage    = t_records[0]["next_stage"]

            # Update workflow stage
            call_lambda({
                "action": "raw_sql",
                "sql": "UPDATE workflow_instance SET current_stage_id = %s WHERE instance_id = %s",
                "params": [to_stage_id, instance_id]
            })

            # Log history
            call_lambda({
                "action": "raw_sql",
                "sql": """INSERT INTO workflow_history
                          (instance_id, workflow_id, from_stage_id, to_stage_id,
                           action_performed, performed_by, remarks, performed_at)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
                "params": [
                    instance_id, workflow_id,
                    from_stage_id, to_stage_id,
                    "accept_and_assign_issue", self.current_user,
                    f"Issue accepted by {self.current_user}. Assigned to role: {next_role}"
                ]
            })

            # Update assigned_to
            call_lambda({
                "action": "raw_sql",
                "sql": """UPDATE issues
                          SET assigned_to = %s, assigned_by = %s, assigned_at = NOW()
                          WHERE issue_id = %s""",
                "params": [next_role, self.current_user, issue_id]
            })

            messagebox.showinfo(
                "Issue Accepted",
                f"✔ Issue #{issue_id} accepted.\n\nMoved to: {next_stage}\nAssigned to: {next_role}",
                parent=self.window
            )

            if self.on_accept_callback:
                self.on_accept_callback()

            self._load_issues()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to accept issue:\n{e}", parent=self.window)