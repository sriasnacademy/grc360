import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox

from runners.report_runner import ControlReportRunner
from services.report_service import ReportService
from runners.control_execution_runner import ControlExecutionRunner
from ui.workflow_tracker_tab import WorkflowTrackerTab
from ui.schedule_tab import ScheduleTab          # ✅ schedule tab


class ControlReportGUI:
    svc = ReportService()

    def __init__(self, root):
        self.root = root
        self.root.title("GRC360 – Control Scheduler")
        self.root.geometry("1200x700")

        self.runner = ControlReportRunner()

        # ---------- HEADER ----------
        tk.Label(
            root,
            text="Test Plan Execution Console",
            font=("Segoe UI", 16, "bold"),
            fg="#0B5ED7"
        ).pack(pady=10)

        # ---------- TABS ----------
        self.tabs = ttk.Notebook(root)
        self.tabs.pack(fill="both", expand=True)

        # ✅ Schedule tab — self-contained, owns its own DB + UI logic
        ScheduleTab(self.tabs)

        # Execute tab
        self.execute_tab = tk.Frame(self.tabs)
        self.tabs.add(self.execute_tab, text="Execute")
        self.build_execute_tab()

        # Workflow tracker tab
        WorkflowTrackerTab(self.tabs)

    # ======================================================
    # EXECUTE TAB  (unchanged)
    # ======================================================
    def build_execute_tab(self):

        top = tk.Frame(self.execute_tab, pady=10)
        top.pack(fill="x", padx=20)

        tk.Label(top, text="🔍 Search:", font=("Segoe UI", 11)).pack(side="left")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self.filter_cards)

        tk.Entry(
            top,
            textvariable=self.search_var,
            width=40,
            font=("Segoe UI", 11)
        ).pack(side="left", padx=10)

        container = tk.Frame(self.execute_tab)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        canvas    = tk.Canvas(container, highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)

        self.cards_frame = tk.Frame(canvas)
        self.cards_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.load_executable_test_plans()

    def load_executable_test_plans(self):
        self.all_plans = self.svc.fetch_executable_test_plans()
        self.render_cards(self.all_plans)

    def render_cards(self, plans):
        self.clear_cards()
        for plan in plans:
            self.create_test_plan_card(plan)

    def create_test_plan_card(self, plan):
        card = tk.Frame(self.cards_frame, bd=1, relief="solid", padx=15, pady=10)
        card.pack(fill="x", pady=6)
        card.plan_data = plan

        left = tk.Frame(card)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(left, text=f"Test Plan - {plan['test_plan_name']}",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(left, text=f"Control - {plan['control_name']}",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=2)
        tk.Label(left, text=f"Risk - {plan['risk_name']}",
                 font=("Segoe UI", 10)).pack(anchor="w")
        tk.Label(left, text=f"Process - {plan['process_name']}",
                 font=("Segoe UI", 10)).pack(anchor="w", pady=2)

        tk.Button(
            card, text="Test", width=10,
            bg="#E9D8A6", font=("Segoe UI", 10, "bold"),
            command=lambda p=plan: self.execute_test_plan(p)
        ).pack(side="right", padx=10)

    def filter_cards(self, *_):
        keyword = self.search_var.get().lower()
        for card in self.cards_frame.winfo_children():
            plan = card.plan_data
            text = (
                plan["test_plan_name"] +
                plan["control_name"]   +
                plan["risk_name"]      +
                plan["process_name"]
            ).lower()
            if keyword in text:
                card.pack(fill="x", pady=6)
            else:
                card.pack_forget()

    def execute_test_plan(self, plan):
        runner = ControlExecutionRunner()
        report = runner.execute_test_plan(plan["test_plan_id"])
        if "error" in report:
            messagebox.showerror("Error", report["error"])
            return
        self.show_report_popup(report)

    def clear_cards(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

    # ======================================================
    # REPORT POPUP  (unchanged)
    # ======================================================
    def generate_report(self):
        self.text.delete("1.0", tk.END)
        test_plan_id = int(self.plan_entry.get())
        report = self.runner.generate_control_report(test_plan_id)

        self.text.insert(tk.END, "CONTROL EFFECTIVENESS REPORT\n", "title")
        self.text.insert(tk.END, f"Test Plan: {report['test_plan']}\n", "header")
        self.text.insert(tk.END, "=" * 120 + "\n\n")

        for ctrl in report["controls"]:
            tag  = "pass" if ctrl["result"] == "PASS" else "fail"
            icon = "🟢 PASS" if ctrl["result"] == "PASS" else "🔴 FAIL"
            self.text.insert(tk.END, f"Control : {ctrl['control_name']}\n")
            self.text.insert(tk.END, f"Result  : {icon}\n\n", tag)

    def status_badge(parent, text, bg):
        tk.Label(
            parent, text=text, bg=bg, fg="white",
            font=("Segoe UI", 11, "bold"), padx=12, pady=6
        ).pack(side="left", padx=10)

    def render_issue_section(self, parent, report):
        issue_frame = tk.Frame(parent, bg="#F8D7DA", bd=1, relief="solid")
        issue_frame.pack(fill="x", padx=25, pady=(10, 20))

        tk.Label(issue_frame, text="🚨 Issue Automatically Created",
                 font=("Segoe UI", 14, "bold"),
                 bg="#F8D7DA", fg="#842029").pack(anchor="w", padx=15, pady=(12, 4))

        issue_id = f"ISSUE-{report['test_plan']}-{report['control']}"

        tk.Label(issue_frame, text=f"Issue ID      : {issue_id}",
                 font=("Segoe UI", 11), bg="#F8D7DA").pack(anchor="w", padx=15)
        tk.Label(issue_frame, text="Severity      : HIGH",
                 font=("Segoe UI", 11, "bold"),
                 fg="#DC3545", bg="#F8D7DA").pack(anchor="w", padx=15)
        tk.Label(issue_frame,
                 text="Issue Summary : Control failed due to one or more test step failures",
                 font=("Segoe UI", 11), bg="#F8D7DA").pack(anchor="w", padx=15, pady=(4, 6))
        tk.Label(issue_frame, text="Failed Tasks:",
                 font=("Segoe UI", 11, "bold"), bg="#F8D7DA").pack(anchor="w", padx=15, pady=(6, 2))

        for task in report["tasks"]:
            if task["status"] == "FAIL":
                tk.Label(issue_frame, text=f"• {task['task_name']}",
                         font=("Segoe UI", 10), bg="#F8D7DA").pack(anchor="w", padx=30)

        tk.Label(issue_frame, text="Issue Status  : OPEN",
                 font=("Segoe UI", 11, "bold"), bg="#F8D7DA").pack(anchor="w", padx=15, pady=(6, 12))

    def show_report_popup(self, report):
        popup = tk.Toplevel(self.root)
        popup.title("Control Execution Report")
        popup.geometry("1000x700")
        popup.transient(self.root)
        popup.grab_set()

        # header
        header = tk.Frame(popup, bg="#F1F3F5", pady=18)
        header.pack(fill="x")
        tk.Label(header, text="Control Effectiveness Report",
                 font=("Segoe UI", 18, "bold"), bg="#F1F3F5").pack(anchor="w", padx=25)
        tk.Label(header,
                 text=f"Test Plan: {report['test_plan']}   |   Control: {report['control']}",
                 font=("Segoe UI", 11), bg="#F1F3F5").pack(anchor="w", padx=25, pady=(6, 0))

        # summary
        summary = tk.Frame(popup, pady=15)
        summary.pack(fill="x", padx=25)

        total_tasks  = len(report["tasks"])
        failed_tasks = sum(1 for t in report["tasks"] if t["status"] == "FAIL")
        passed_tasks = total_tasks - failed_tasks
        pass_ratio   = int((passed_tasks / total_tasks) * 100) if total_tasks else 0

        result_color = "#198754" if report["result"] == "PASS" else "#DC3545"
        result_text  = "CONTROL PASSED" if report["result"] == "PASS" else "CONTROL FAILED"

        tk.Label(summary, text=result_text,
                 font=("Segoe UI", 12, "bold"), fg="white",
                 bg=result_color, padx=24, pady=10).pack(side="left")

        metrics = tk.Frame(summary)
        metrics.pack(side="left", padx=40)
        tk.Label(metrics, text=f"Total Tasks: {total_tasks}", font=("Segoe UI", 11)).pack(anchor="w")
        tk.Label(metrics, text=f"Passed: {passed_tasks}",    font=("Segoe UI", 11), fg="#198754").pack(anchor="w")
        tk.Label(metrics, text=f"Failed: {failed_tasks}",    font=("Segoe UI", 11), fg="#DC3545").pack(anchor="w")

        # progress
        pf = tk.Frame(popup)
        pf.pack(fill="x", padx=25, pady=(5, 18))
        ttk.Progressbar(pf, orient="horizontal", length=450,
                        mode="determinate", value=pass_ratio).pack(side="left")
        tk.Label(pf, text=f"{pass_ratio}% Tasks Passed",
                 font=("Segoe UI", 10)).pack(side="left", padx=12)

        if report["result"] == "FAIL":
            self.render_issue_section(popup, report)

        # details
        body = ScrolledText(popup, font=("Consolas", 10), wrap="word")
        body.pack(fill="both", expand=True, padx=25, pady=10)

        for task in report["tasks"]:
            icon = "❌" if task["status"] == "FAIL" else "✅"
            body.insert(tk.END, f"{icon} TASK: {task['task_name']}  [{task['status']}]\n")
            body.insert(tk.END, f"      Reason: {task['evidence_result']}\n")
            if task.get("executed_at"):
                body.insert(tk.END, f"      Executed At: {task['executed_at']}\n")
            body.insert(tk.END, "\n")

        body.configure(state="disabled")