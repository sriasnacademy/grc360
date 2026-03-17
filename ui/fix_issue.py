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

        info = tk.Frame(self.window, bg="#EAF2FB", height=32)
        info.pack(fill="x")
        info.pack_propagate(False)
        tk.Label(
            info,
            text="Mark all issues as Fixed first. Close Issue only after test plan re-runs clean.",
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
            btn_frame, text="Issues assigned to you:",
            font=("Segoe UI", 10, "bold"), fg="#1E3A5F", bg="#F4F6F9"
        ).pack(side="left")

        table_frame = tk.Frame(self.window, bg="#F4F6F9")
        table_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))

        columns = ("chk", "issue_id", "plan_id", "cycle_id", "type", "test_plan", "test_cycle", "current_stage", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=13)

        self.tree.heading("chk",           text="✔")
        self.tree.heading("issue_id",      text="Issue ID")
        self.tree.heading("plan_id",       text="Plan ID")
        self.tree.heading("cycle_id",      text="Cycle ID")
        self.tree.heading("type",          text="Issue Type")
        self.tree.heading("test_plan",     text="Test Plan")
        self.tree.heading("test_cycle",    text="Cycle #")
        self.tree.heading("current_stage", text="Workflow Stage")
        self.tree.heading("status",        text="Status")

        self.tree.column("chk",           width=35,  anchor="center")
        self.tree.column("issue_id",      width=70,  anchor="center")
        self.tree.column("plan_id",       width=65,  anchor="center")
        self.tree.column("cycle_id",      width=65,  anchor="center")
        self.tree.column("type",          width=175, anchor="w")
        self.tree.column("test_plan",     width=130, anchor="w")
        self.tree.column("test_cycle",    width=55,  anchor="center")
        self.tree.column("current_stage", width=130, anchor="center")
        self.tree.column("status",        width=110, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self.tree.tag_configure("odd",    background="#FFFFFF")
        self.tree.tag_configure("even",   background="#F0F5FB")
        self.tree.tag_configure("fixed",  background="#FFF3CD", foreground="#856404")
        self.tree.tag_configure("closed", background="#D4EDDA", foreground="#155724")

        action_bar = tk.Frame(self.window, bg="#E8EDF2", height=56)
        action_bar.pack(fill="x", side="bottom")
        action_bar.pack_propagate(False)

        self.status_label = tk.Label(
            action_bar, text="Select an issue to take action.",
            font=("Segoe UI", 9), fg="#555", bg="#E8EDF2"
        )
        self.status_label.pack(side="left", padx=16, pady=16)

        tk.Button(
            action_bar, text="✖  Exit",
            font=("Segoe UI", 10), bg="#E8EDF2", fg="#555",
            relief="flat", cursor="hand2", padx=14,
            command=self.window.destroy
        ).pack(side="right", padx=10, pady=10)

        self.close_btn = tk.Button(
            action_bar, text="🔒  Close Issue",
            font=("Segoe UI", 10, "bold"),
            bg="#DC3545", fg="white",
            relief="flat", cursor="hand2", padx=14,
            command=self._on_close_issue
        )
        self.close_btn.pack(side="right", padx=4, pady=10)

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
                        tp.test_plan_name  AS test_plan,
                        tc.cycle_number    AS test_cycle,
                        ws.stage_name      AS current_stage,
                        i.assigned_to,
                        i.status           AS issue_status,
                        wi.instance_id,
                        wi.status          AS workflow_status,
                        wi.cycle_id        AS wf_cycle_id,
                        i.test_plan_id
                    FROM issues i
                    JOIN workflow_instance wi  ON wi.reference_id = i.issue_id
                                              AND wi.module_name  = 'ISSUE'
                    JOIN workflow_stages ws    ON ws.stage_id = wi.current_stage_id
                    LEFT JOIN test_plan tp     ON tp.test_plan_id = i.test_plan_id
                    LEFT JOIN test_cycle tc    ON tc.cycle_id     = wi.cycle_id
                    WHERE i.assigned_to = %s
                    AND i.status != 'ISSUE CLOSED'
                    ORDER BY i.issue_id DESC
                """,
                "params": [self.current_user_role]
            }
            response = call_lambda(payload)
            records  = response.get("records", [])

            if not records:
                self.status_label.config(text="No open issues assigned to your role.", fg="#888")
                return

            self._instance_map = {
                str(rec["issue_id"]): {
                    "instance_id":     rec["instance_id"],
                    "workflow_status": rec["workflow_status"],
                    "current_stage":   rec["current_stage"],
                    "issue_status":    rec["issue_status"] or "OPEN",
                    "cycle_id":        rec["wf_cycle_id"],
                    "test_plan_id":    rec["test_plan_id"]
                }
                for rec in records
            }

            for i, rec in enumerate(records):
                status = rec.get("issue_status") or "OPEN"
                chk    = "☑" if status == "fix_issue" else "☐"
                if status == "fix_issue":
                    tag = "fixed"
                else:
                    tag = "even" if i % 2 == 0 else "odd"

                self.tree.insert("", "end", iid=str(rec["issue_id"]), tags=(tag,), values=(
                    chk,
                    rec["issue_id"],
                    rec.get("test_plan_id", "—"),
                    rec.get("wf_cycle_id",  "—"),
                    rec["issue_type"],
                    rec.get("test_plan",    "—"),
                    rec.get("test_cycle",   "—"),
                    rec.get("current_stage","—"),
                    status,
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
        if not selected:
            return

        vals     = self.tree.item(selected[0], "values")
        issue_id = str(vals[1])
        info     = self._instance_map.get(issue_id, {})

        self.status_label.config(
            text=(
                f"Selected: Issue #{issue_id} — {vals[4]}"
                f"  |  Plan ID: {vals[2]}  |  Cycle ID: {vals[3]}"
                f"  |  Stage: {info.get('current_stage', '—')}"
                f"  |  Status: {info.get('issue_status', '—')}"
            ),
            fg="#1E3A5F"
        )

    def _check_cycle_status_for_close(self, cycle_id):
        """
        Check only rows matching cycle_id (string-safe comparison).
        Highlights matching rows. Returns True only if ALL are fix_issue.
        """
        cycle_id_str = str(cycle_id).strip()
        matched   = []
        not_fixed = []

        for iid in self.tree.get_children():
            row_vals  = self.tree.item(iid, "values")
            row_cycle = str(row_vals[3]).strip()
            row_issue = str(row_vals[1]).strip()

            if row_cycle != cycle_id_str:
                continue

            self.tree.selection_add(iid)
            matched.append(row_issue)

            info       = self._instance_map.get(row_issue, {})
            row_status = info.get("current_stage", "")
            print(f"  CHECK issue={row_issue} cycle={row_cycle} status='{row_status}'")

            if row_status != "Fix Issue":
                not_fixed.append(row_issue)

        print(f"  SUMMARY cycle={cycle_id_str} matched={matched} not_fixed={not_fixed}")

        if not matched:
            self.status_label.config(
                text=f"⚠ No rows found for Cycle #{cycle_id_str}. Try refreshing.",
                fg="#DC3545"
            )
            return False

        if not_fixed:
            self.status_label.config(
                text=f"⚠ Issues {', '.join(not_fixed)} in Cycle #{cycle_id_str} are NOT fixed. Fix them before closing.",
                fg="#DC3545"
            )
            return False

        self.status_label.config(
            text=f"✔ All {len(matched)} issue(s) in Cycle #{cycle_id_str} are Fixed. Proceeding to close...",
            fg="#1E7E34"
        )
        return True

    def _get_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No Selection", "Please select an issue first.", parent=self.window)
            return None, None, None
        vals        = self.tree.item(selected[0], "values")
        issue_id    = str(vals[1])
        info        = self._instance_map.get(issue_id, {})
        instance_id = info.get("instance_id")
        return issue_id, instance_id, vals[4]

    # ─────────────────────────────────────────────
    # ACTIONS
    # ─────────────────────────────────────────────

    def _on_action(self, action_name, action_label):
        issue_id, instance_id, issue_type = self._get_selected()
        if not issue_id:
            return

        confirm = messagebox.askyesno(
            f"Confirm: {action_label}",
            f"Mark Issue #{issue_id} as Fixed?\n\n\"{issue_type}\"",
            parent=self.window
        )
        if not confirm:
            return

        self._perform_fix(issue_id, instance_id, action_name, action_label)

    def _on_close_issue(self):
        issue_id, instance_id, issue_type = self._get_selected()
        if not issue_id:
            return

        info     = self._instance_map.get(str(issue_id), {})
        plan_id  = info.get("test_plan_id")
        cycle_id = info.get("cycle_id")

        print(f"DEBUG _on_close_issue | issue_id={issue_id} | plan_id={plan_id} | cycle_id={cycle_id}")

        if not plan_id or not cycle_id:
            messagebox.showerror("Error", "Could not determine plan or cycle for this issue.", parent=self.window)
            return

        # Check all issues in cycle are fixed (uses _instance_map, not tree display)
        all_fixed = self._check_cycle_status_for_close(str(cycle_id))
        if not all_fixed:
            messagebox.showwarning(
                "Cannot Close",
                "Some issues in this cycle are not Fixed yet.\n\nPlease mark ALL issues as Fixed before closing.",
                parent=self.window
            )
            return

        self._check_all_fixed_then_rerun(issue_id, instance_id, int(plan_id), int(cycle_id), issue_type)

    # ─────────────────────────────────────────────
    # MARK AS FIXED
    # ─────────────────────────────────────────────

    def _perform_fix(self, issue_id, instance_id, action_name, action_label):
        try:
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
                    "Transition Error",
                    f"No '{action_name}' transition found for current stage.\n"
                    f"Check workflow_transitions table.",
                    parent=self.window
                )
                return

            from_stage_id = t_records[0]["current_stage_id"]
            to_stage_id   = t_records[0]["to_stage_id"]
            workflow_id   = t_records[0]["workflow_id"]
            next_role     = t_records[0]["role_required"]
            next_stage    = t_records[0]["next_stage"]

            # Transition workflow stage
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
                    action_name, self.current_user,
                    f"Issue fixed by {self.current_user}"
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

            # Set issues.status = 'fix_issue'
            call_lambda({
                "action": "raw_sql",
                "sql": "UPDATE issues SET status = 'fix_issue' WHERE issue_id = %s",
                "params": [issue_id]
            })

            messagebox.showinfo(
                "Marked as Fixed",
                f"✔ Issue #{issue_id} marked as Fixed.\n\nMoved to: {next_stage}\nAssigned to: {next_role}",
                parent=self.window
            )

            if self.on_close_callback:
                self.on_close_callback()

            self._load_issues()

        except Exception as e:
            messagebox.showerror("Error", f"Fix action failed:\n{e}", parent=self.window)

    # ─────────────────────────────────────────────
    # CLOSE ISSUE FLOW
    # ─────────────────────────────────────────────

    def _check_all_fixed_then_rerun(self, issue_id, instance_id, plan_id, cycle_id, issue_type):
        """
        Double-check via DB that all issues in cycle have fix_issue in workflow_history.
        Then confirm and re-run test plan.
        """
        try:
            count_response = call_lambda({
                "action": "raw_sql",
                "sql": """
                    SELECT
                        COUNT(DISTINCT wi.instance_id) AS total,
                        SUM(CASE WHEN wh.action_performed = 'fix_issue' THEN 1 ELSE 0 END) AS fixed
                    FROM issues i
                    JOIN workflow_instance wi ON wi.reference_id = i.issue_id
                                             AND wi.module_name  = 'ISSUE'
                    LEFT JOIN workflow_history wh ON wh.instance_id      = wi.instance_id
                                                 AND wh.action_performed = 'fix_issue'
                    WHERE i.test_plan_id = %s
                    AND wi.cycle_id      = %s
                    AND i.assigned_to    = %s
                """,
                "params": [plan_id, cycle_id, self.current_user_role]
            })
            count_records = count_response.get("records", [])
            if not count_records:
                return

            total = int(count_records[0]["total"] or 0)
            fixed = int(count_records[0]["fixed"] or 0)

            print(f"📊 DB check — Cycle {cycle_id} | Plan {plan_id} | Total: {total} | Fixed: {fixed}")

            if total == 0 or total != fixed:
                remaining = total - fixed
                messagebox.showwarning(
                    "Issues Not Fixed Yet",
                    f"⚠ DB check: {remaining} issue(s) in Cycle #{cycle_id} are not yet Fixed in workflow history.\n\n"
                    f"Please mark all issues as Fixed before closing.",
                    parent=self.window
                )
                return

            confirm = messagebox.askyesno(
                "All Issues Fixed — Re-run Test Plan?",
                f"✅ All {total} issue(s) in Cycle #{cycle_id} are Fixed.\n\n"
                f"Re-run Test Plan #{plan_id} now?\n\n"
                f"• New cycle CLEAN  →  all issues COMPLETED + ISSUE CLOSED ✅\n"
                f"• New issues found →  nothing changes, new workflows start",
                parent=self.window
            )
            if not confirm:
                return

            self._rerun_and_close(plan_id, cycle_id)

        except Exception as e:
            print(f"❌ Error in _check_all_fixed_then_rerun: {e}")
            messagebox.showerror("Error", f"Check failed:\n{e}", parent=self.window)

    def _rerun_and_close(self, plan_id, cycle_id):
        """
        1. Re-run test plan.
        2. If new cycle is CLEAN → look up close_issue terminal stage from workflow
           definition (not current stage) and force-close ALL instances in old cycle.
        3. If new issues found → do nothing.
        """
        try:
            from runners.control_execution_runner import ControlExecutionRunner

            print(f"🔄 Re-running Test Plan {plan_id}...")
            self.status_label.config(text="⏳ Re-running test plan...", fg="#FF8C00")
            self.window.update()

            runner = ControlExecutionRunner()
            runner.execute_test_plan(int(plan_id))

            # ── Get new cycle ──────────────────────────────────────────────
            new_cycle_response = call_lambda({
                "action": "raw_sql",
                "sql": """
                    SELECT MAX(cycle_number) AS new_cycle_num,
                           MAX(cycle_id)     AS new_cycle_id
                    FROM test_cycle
                    WHERE test_plan_id = %s
                """,
                "params": [plan_id]
            })
            new_cycle_records = new_cycle_response.get("records", [])
            new_cycle_num = new_cycle_records[0]["new_cycle_num"] if new_cycle_records else None
            new_cycle_id  = new_cycle_records[0]["new_cycle_id"]  if new_cycle_records else None

            print(f"Old cycle_id={cycle_id} | New cycle_id={new_cycle_id}")

            if not new_cycle_id or int(new_cycle_id) == int(cycle_id):
                messagebox.showwarning(
                    "Warning",
                    "Could not detect a new cycle after re-run.\nPlease check manually.",
                    parent=self.window
                )
                return

            # ── Count issues in new cycle ──────────────────────────────────
            issue_check = call_lambda({
                "action": "raw_sql",
                "sql": """
                    SELECT COUNT(*) AS issue_count
                    FROM issues i
                    JOIN workflow_instance wi ON wi.reference_id = i.issue_id
                                             AND wi.module_name  = 'ISSUE'
                    WHERE i.test_plan_id = %s
                    AND wi.cycle_id      = %s
                """,
                "params": [plan_id, new_cycle_id]
            })
            issue_count = int(
                (issue_check.get("records") or [{}])[0].get("issue_count", 0)
            )
            print(f"New cycle {new_cycle_id} issue_count={issue_count}")

            if issue_count > 0:
                # New issues found — do nothing, new workflows already started
                messagebox.showwarning(
                    "New Issues Found ⚠",
                    f"⚠ Test Plan #{plan_id} re-executed.\n\n"
                    f"Cycle #{new_cycle_num} has {issue_count} new issue(s).\n\n"
                    f"No transitions made. Fix the new issues and try closing again.",
                    parent=self.window
                )
                print(f"⚠ New cycle {new_cycle_id} has {issue_count} issues — nothing closed.")
                self._load_issues()
                return

            # ── CLEAN — close all instances in OLD cycle ───────────────────

            # Get all instances in old cycle
            all_instances_response = call_lambda({
                "action": "raw_sql",
                "sql": """
                    SELECT wi.instance_id, wi.current_stage_id, wi.workflow_id
                    FROM issues i
                    JOIN workflow_instance wi ON wi.reference_id = i.issue_id
                                             AND wi.module_name  = 'ISSUE'
                    WHERE i.test_plan_id = %s
                    AND wi.cycle_id      = %s
                """,
                "params": [plan_id, cycle_id]
            })
            all_instances = all_instances_response.get("records", [])

            if not all_instances:
                messagebox.showwarning("Warning", "No instances found in old cycle to close.", parent=self.window)
                return

            # ── Look up close_issue terminal stage from workflow definition ─
            # We use ANY instance's workflow_id — all in same plan share the same workflow.
            # We do NOT use from_stage_id because instances are at stage 4 (Fix Issue),
            # and close_issue transition is defined from stage 6 → 7.
            # Instead we find the to_stage_id for action_name = 'close_issue' anywhere
            # in the workflow, which gives us stage 7 (Close Issue) unconditionally.
            workflow_id_for_lookup = all_instances[0]["workflow_id"]
            close_def_response = call_lambda({
                "action": "raw_sql",
                "sql": """
                    SELECT wt.to_stage_id, wt.role_required, ws.stage_name
                    FROM workflow_transitions wt
                    JOIN workflow_stages ws ON ws.stage_id = wt.to_stage_id
                    WHERE wt.workflow_id  = %s
                    AND wt.action_name    = 'close_issue'
                    AND wt.active         = 1
                    LIMIT 1
                """,
                "params": [workflow_id_for_lookup]
            })
            close_def_records = close_def_response.get("records", [])

            if not close_def_records:
                messagebox.showerror(
                    "Workflow Error",
                    f"No 'close_issue' transition found in workflow {workflow_id_for_lookup}.\n"
                    f"Please check the workflow_transitions table.",
                    parent=self.window
                )
                return

            close_to_stage_id = close_def_records[0]["to_stage_id"]
            close_next_role   = close_def_records[0]["role_required"]
            close_stage_name  = close_def_records[0]["stage_name"]

            print(f"Closing to stage {close_to_stage_id} ({close_stage_name}) role={close_next_role}")

            # ── Per-instance: transition + history + issue status ──────────
            for inst in all_instances:
                inst_id       = inst["instance_id"]
                workflow_id   = inst["workflow_id"]
                from_stage_id = inst["current_stage_id"]

                print(f"  Closing instance {inst_id} from stage {from_stage_id} → {close_to_stage_id}")

                # Transition to Close Issue stage
                call_lambda({
                    "action": "raw_sql",
                    "sql": "UPDATE workflow_instance SET current_stage_id = %s WHERE instance_id = %s",
                    "params": [close_to_stage_id, inst_id]
                })

                # Log history
                call_lambda({
                    "action": "raw_sql",
                    "sql": """INSERT INTO workflow_history
                              (instance_id, workflow_id, from_stage_id, to_stage_id,
                               action_performed, performed_by, remarks, performed_at)
                              VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())""",
                    "params": [
                        inst_id, workflow_id,
                        from_stage_id, close_to_stage_id,
                        "close_issue", self.current_user,
                        f"Force-closed after test plan re-run — Cycle #{new_cycle_id} is clean"
                    ]
                })

                # Update issue: assigned_to + ISSUE CLOSED
                call_lambda({
                    "action": "raw_sql",
                    "sql": """UPDATE issues
                              SET assigned_to = %s,
                                  assigned_by = %s,
                                  assigned_at = NOW(),
                                  status      = 'CLOSED'
                              WHERE issue_id = (
                                  SELECT reference_id FROM workflow_instance WHERE instance_id = %s
                              )""",
                    "params": [close_next_role, self.current_user, inst_id]
                })
                print(f"  ✔ Instance {inst_id} → ISSUE CLOSED")

            # Mark ALL old-cycle instances COMPLETED
            call_lambda({
                "action": "raw_sql",
                "sql": """
                    UPDATE workflow_instance wi
                    JOIN issues i ON wi.reference_id = i.issue_id
                                 AND wi.module_name  = 'ISSUE'
                    SET wi.status = 'COMPLETED', wi.completed_at = NOW()
                    WHERE i.test_plan_id = %s
                    AND wi.cycle_id      = %s
                """,
                "params": [plan_id, cycle_id]
            })

            # Mark test_results ISSUE CLOSED
            call_lambda({
                "action": "raw_sql",
                "sql": """
                    UPDATE test_results
                    SET status = 'ISSUE CLOSED'
                    WHERE test_plan_id = %s
                    AND cycle_number   = (
                        SELECT cycle_number FROM test_cycle
                        WHERE cycle_id = %s LIMIT 1
                    )
                """,
                "params": [plan_id, cycle_id]
            })

            print(f"✅ Plan {plan_id} — all instances in cycle {cycle_id} closed.")

            messagebox.showinfo(
                "Test Plan PASSED ✅",
                f"✅ Test Plan #{plan_id} re-executed — Cycle #{new_cycle_num} is CLEAN!\n\n"
                f"No new issues found.\n\n"
                f"✔ All instances transitioned to '{close_stage_name}'\n"
                f"✔ All instances marked COMPLETED\n"
                f"✔ All issues + test results marked 'ISSUE CLOSED'",
                parent=self.window
            )

            self.status_label.config(text="✅ Issues closed. Refreshing...", fg="#1E7E34")
            self._load_issues()

        except Exception as e:
            print(f"❌ Error in _rerun_and_close: {e}")
            messagebox.showerror("Error", f"Failed:\n{e}", parent=self.window)