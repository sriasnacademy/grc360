import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from runners.report_runner import ControlReportRunner
from tkinter import messagebox
from services.report_service import ReportService


class ControlReportGUI:
    svc = ReportService()

    def __init__(self, root):
        self.root = root
        self.root.title("GRC360 – Control Scheduler")
        self.root.geometry("1100x650")

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

        self.schedule_tab = tk.Frame(self.tabs)
        self.execute_tab = tk.Frame(self.tabs)

        self.tabs.add(self.schedule_tab, text="Schedule")
        self.tabs.add(self.execute_tab, text="Execute")

        self.build_schedule_tab()
        self.build_execute_tab()

    # ======================================================
    # SCHEDULE TAB
    # ======================================================
    def build_schedule_tab(self):

        frame = tk.Frame(self.schedule_tab, pady=40)
        frame.pack()

        # Start Time
        tk.Label(frame, text="🕒 Start Time", font=("Segoe UI", 11, "bold")).grid(row=0, column=0, padx=40)
        self.start_time = tk.Entry(frame, width=10, font=("Segoe UI", 11))
        self.start_time.insert(0, "10:00")
        self.start_time.grid(row=1, column=0, padx=40)

        # End Time
        tk.Label(frame, text="🕒 End Time", font=("Segoe UI", 11, "bold")).grid(row=0, column=1, padx=40)
        self.end_time = tk.Entry(frame, width=10, font=("Segoe UI", 11))
        self.end_time.insert(0, "18:00")
        self.end_time.grid(row=1, column=1, padx=40)

        # Schedule Button
        tk.Button(
            frame,
            text="Schedule",
            bg="#0D6EFD",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            width=15,
            command=self.schedule_job
        ).grid(row=3, column=0, columnspan=2, pady=40)

    def schedule_job(self):
        start = self.start_time.get()
        end = self.end_time.get()

        tk.messagebox.showinfo(
            "Scheduled",
            f"Control execution scheduled from {start} to {end}"
        )

    # ======================================================
    # EXECUTE TAB
    # ======================================================

    def build_execute_tab(self):

        # -------------------------------
        # SEARCH BAR
        # -------------------------------
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

        # -------------------------------
        # SCROLLABLE CONTAINER
        # -------------------------------
        container = tk.Frame(self.execute_tab)
        container.pack(fill="both", expand=True, padx=20, pady=10)

        canvas = tk.Canvas(container, highlightthickness=0)
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

        # -------------------------------
        # LOAD TEST PLANS
        # -------------------------------
        self.load_executable_test_plans()

    def show_test_plan_info(self):
        svc = ReportService()
        name = self.plan_combo.get()

        if not name:
            messagebox.showwarning("Select Test Plan", "Please select a test plan")
            return

        test_plan_id = self.test_plan_map[name]
        details = svc.fetch_test_plan(test_plan_id)

        info = (
            f"Process       : {details['process']}\n"
            f"Sub-Process   : {details['sub_process']}\n\n"
            f"Risks:\n"
        )

        for r in details["risks"]:
            info += f"  • {r}\n"

        info += "\nControls:\n"
        for c in details["controls"]:
            info += f"  • {c}\n"

        messagebox.showinfo("Test Plan Information", info)

    def load_executable_test_plans(self):
        svc = ReportService()
        self.all_plans = svc.fetch_executable_test_plans()
        self.render_cards(self.all_plans)

    
    def render_cards(self, plans):
        self.clear_cards()

        for plan in plans:
            self.create_test_plan_card(plan)
            
    def create_test_plan_card(self, plan):

        card = tk.Frame(
            self.cards_frame,
            bd=1,
            relief="solid",
            padx=15,
            pady=10
        )
        card.pack(fill="x", pady=6)

        card.plan_data = plan

        left = tk.Frame(card)
        left.pack(side="left", fill="x", expand=True)

        tk.Label(
            left,
            text=f"Test Plan - {plan['test_plan_name']}",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w")

        tk.Label(
            left,
            text=f"Control - {plan['control_name']}",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=2)

        tk.Label(
            left,
            text=f"Risk - {plan['risk_name']}",
            font=("Segoe UI", 10)
        ).pack(anchor="w")

        tk.Label(
            left,
            text=f"Process - {plan['process_name']}",
            font=("Segoe UI", 10)
        ).pack(anchor="w", pady=2)

        tk.Button(
            card,
            text="Test",
            width=10,
            bg="#E9D8A6",
            font=("Segoe UI", 10, "bold"),
            command=lambda p=plan: self.execute_test_plan(p)
        ).pack(side="right", padx=10)

        
    def filter_cards(self, *_):
        keyword = self.search_var.get().lower()

        for card in self.cards_frame.winfo_children():
            plan = card.plan_data

            text = (
                plan["test_plan_name"]
                + plan["control_name"]
                + plan["risk_name"]
                + plan["process_name"]
            ).lower()

            if keyword in text:
                card.pack(fill="x", pady=6)
            else:
                card.pack_forget()


    def execute_test_plan(self, plan):

        report = self.runner.generate_control_report(plan["test_plan_id"])

        if "error" in report:
            messagebox.showerror("Error", report["error"])
            return

        self.show_report_popup(report)


    
    def clear_cards(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()

    # ======================================================
    # EXECUTION LOGIC (UNCHANGED CORE)
    # ======================================================
    def generate_report(self):

        self.text.delete("1.0", tk.END)
        test_plan_id = int(self.plan_entry.get())
        report = self.runner.generate_control_report(test_plan_id)

        self.text.insert(tk.END, "CONTROL EFFECTIVENESS REPORT\n", "title")
        self.text.insert(tk.END, f"Test Plan: {report['test_plan']}\n", "header")
        self.text.insert(tk.END, "=" * 120 + "\n\n")

        for ctrl in report["controls"]:
            tag = "pass" if ctrl["result"] == "PASS" else "fail"
            icon = "🟢 PASS" if ctrl["result"] == "PASS" else "🔴 FAIL"

            self.text.insert(tk.END, f"Control : {ctrl['control_name']}\n")
            self.text.insert(tk.END, f"Result  : {icon}\n\n", tag)
            
    def show_report_popup(self, report):

        popup = tk.Toplevel(self.root)
        popup.title("Control Execution Report")
        popup.geometry("900x600")
        popup.transient(self.root)
        popup.grab_set()  # modal window

        # ---------- HEADER ----------
        header = tk.Frame(popup, pady=10)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Control Effectiveness Report",
            font=("Segoe UI", 14, "bold"),
            fg="#0B5ED7"
        ).pack(anchor="w", padx=15)

        tk.Label(
            header,
            text=f"Test Plan: {report['test_plan']}",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w", padx=15)

        tk.Label(
            header,
            text=f"Control: {report['control']}",
            font=("Segoe UI", 11)
        ).pack(anchor="w", padx=15)

        result_color = "#198754" if report["result"] == "PASS" else "#DC3545"

        tk.Label(
            header,
            text=f"Result: {report['result']}",
            font=("Segoe UI", 11, "bold"),
            fg=result_color
        ).pack(anchor="w", padx=15, pady=(0, 10))

        # ---------- REPORT BODY ----------
        body = ScrolledText(
            popup,
            font=("Consolas", 10),
            wrap="word"
        )
        body.pack(fill="both", expand=True, padx=15, pady=10)

        # ---------- CONTENT ----------
        for proc in report["procedures"]:
            body.insert(tk.END, f"STEP: {proc['step']}\n", "header")

            for task in proc["tasks"]:
                body.insert(tk.END, f"  Task: {task['task_name']}\n")

                if task["results"]:
                    for r in task["results"]:
                        body.insert(
                            tk.END,
                            f"    - {r['evidence_result']}  ({r['executed_at']})\n"
                        )
                else:
                    body.insert(tk.END, "    - No evidence\n")

            body.insert(tk.END, "\n")

        body.configure(state="disabled")

