import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from runners.report_runner import ControlReportRunner


class ControlReportGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("GRC360 – Control Effectiveness Report")
        self.root.geometry("1100x700")

        self.runner = ControlReportRunner()

        # ---------- HEADER ----------
        tk.Label(
            root,
            text="Control Effectiveness Report",
            font=("Segoe UI", 16, "bold"),
            fg="#0B5ED7"
        ).pack(pady=10)

        form = tk.Frame(root)
        form.pack()

        tk.Label(form, text="Test Plan ID:", font=("Segoe UI", 10)).grid(row=0, column=0)
        self.plan_entry = tk.Entry(form, width=10)
        self.plan_entry.insert(0, "3")
        self.plan_entry.grid(row=0, column=1, padx=5)

        tk.Button(
            form,
            text="Generate Report",
            command=self.generate_report,
            bg="#198754",
            fg="white",
            font=("Segoe UI", 10, "bold")
        ).grid(row=0, column=2, padx=10)

        self.text = ScrolledText(
            root,
            width=130,
            height=35,
            font=("Consolas", 10)
        )
        self.text.pack(pady=15)

        # ---------- TAG STYLES ----------
        self.text.tag_config("title", foreground="#0B5ED7", font=("Segoe UI", 14, "bold"))
        self.text.tag_config("header", foreground="#212529", font=("Segoe UI", 11, "bold"))
        self.text.tag_config("pass", foreground="#198754", font=("Segoe UI", 11, "bold"))
        self.text.tag_config("fail", foreground="#DC3545", font=("Segoe UI", 11, "bold"))
        self.text.tag_config("info", foreground="#0D6EFD")
        self.text.tag_config("muted", foreground="#6C757D")

    # ------------------------------------------------

    def generate_report(self):
        self.text.delete("1.0", tk.END)

        test_plan_id = int(self.plan_entry.get())
        report = self.runner.generate_control_report(test_plan_id)

        # ---------- REPORT TITLE ----------
        self.text.insert(tk.END, "CONTROL EFFECTIVENESS REPORT\n", "title")
        self.text.insert(tk.END, f"Test Plan: {report['test_plan']}\n", "header")
        self.text.insert(tk.END, "=" * 120 + "\n\n")

        for ctrl in report["controls"]:

            status_tag = "pass" if ctrl["result"] == "PASS" else "fail"
            status_icon = "🟢 PASS" if ctrl["result"] == "PASS" else "🔴 FAIL"

            # ---------- CONTROL SUMMARY ----------
            self.text.insert(tk.END, "CONTROL SUMMARY\n", "header")
            self.text.insert(tk.END, f"Control Name      : {ctrl['control_name']}\n")
            self.text.insert(tk.END, f"Control Result    : {status_icon}\n", status_tag)
            self.text.insert(tk.END, "-" * 120 + "\n\n")

            # ---------- TESTING PROCEDURE ----------
            self.text.insert(tk.END, "HOW THE CONTROL WAS TESTED\n", "header")

            for proc in ctrl["testing_procedure"]:
                self.text.insert(tk.END, f"• {proc['task_name']}\n", "info")

                if proc["results"]:
                    latest = proc["results"][-1]   # latest execution only
                    self.text.insert(
                        tk.END,
                        f"    Evidence Result : {latest['evidence_result']}\n",
                        "muted"
                    )
                    self.text.insert(
                        tk.END,
                        f"    Executed At     : {latest['executed_at']}\n\n",
                        "muted"
                    )
                else:
                    self.text.insert(tk.END, "    No evidence found\n\n", "muted")

            # ---------- PROCESS IMPACT ----------
            self.text.insert(tk.END, "PROCESS IMPACT ASSESSMENT\n", "header")

            if ctrl["process_impact"]:
                for pid in ctrl["process_impact"]:
                    self.text.insert(tk.END, f"• Process ID Impacted: {pid}\n", "fail")
            else:
                self.text.insert(tk.END, "• No process impact identified\n", "pass")

            self.text.insert(tk.END, "\n" + "=" * 120 + "\n\n")
