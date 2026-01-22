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

        top = tk.Frame(self.execute_tab, pady=10)
        top.pack()

        # -------------------------------
        # TEST PLAN DROPDOWN
        # -------------------------------
        tk.Label(top, text="Test Plan:", font=("Segoe UI", 11)).grid(row=0, column=0, padx=5)

        self.test_plan_map = {}   # name → id

        self.plan_combo = ttk.Combobox(
            top,
            width=30,
            state="readonly",
            font=("Segoe UI", 11)
        )
        self.plan_combo.grid(row=0, column=1, padx=5)

        self.load_test_plans()

        # -------------------------------
        # INFO ICON
        # -------------------------------
        info_btn = tk.Button(
            top,
            text="ℹ",
            font=("Segoe UI", 12, "bold"),
            fg="#0D6EFD",
            bd=0,
            command=self.show_test_plan_info
        )
        info_btn.grid(row=0, column=2, padx=5)

        # -------------------------------
        # EXECUTE BUTTON
        # -------------------------------
        tk.Button(
            top,
            text="Execute",
            bg="#198754",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            command=self.generate_report
        ).grid(row=0, column=3, padx=15)

        # -------------------------------
        # RESULTS BOX
        # -------------------------------
        self.text = ScrolledText(
            self.execute_tab,
            width=130,
            height=28,
            font=("Consolas", 10)
        )
        self.text.pack(pady=15)

        self.text.tag_config("title", foreground="#0B5ED7", font=("Segoe UI", 14, "bold"))
        self.text.tag_config("header", font=("Segoe UI", 11, "bold"))
        self.text.tag_config("pass", foreground="#198754", font=("Segoe UI", 11, "bold"))
        self.text.tag_config("fail", foreground="#DC3545", font=("Segoe UI", 11, "bold"))
        self.text.tag_config("muted", foreground="#6C757D")


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

    def load_test_plans(self):
        svc = ReportService()
        plans = svc.fetch_all_test_plans()

        names = []
        for p in plans:
            names.append(p["test_plan_name"])
            self.test_plan_map[p["test_plan_name"]] = p["test_plan_id"]

        self.plan_combo["values"] = names

        if names:
            self.plan_combo.current(0)
            
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
