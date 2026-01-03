import tkinter as tk
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText
import threading
import time

from runners.manual_runner import ManualRunner


class ControlExecutionGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("GRC Automated Control Execution")
        self.root.geometry("700x500")

        self.runner = ManualRunner()
        self.scheduler_thread = None
        self.stop_scheduler = False

        # ---------------- HEADER ----------------
        tk.Label(
            root,
            text="GRC Automated Control Execution",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # ---------------- INPUT SECTION ----------------
        frame = tk.Frame(root)
        frame.pack(pady=5)

        tk.Label(frame, text="Test Plan ID:").grid(row=0, column=0, padx=5)
        self.test_plan_entry = tk.Entry(frame, width=10)
        self.test_plan_entry.insert(0, "3")
        self.test_plan_entry.grid(row=0, column=1, padx=5)

        # Execute Button
        tk.Button(
            root,
            text="▶ Execute Now",
            width=25,
            bg="green",
            fg="white",
            command=self.execute_now
        ).pack(pady=10)

        # ---------------- SCHEDULER SECTION ----------------
        sched_frame = tk.LabelFrame(root, text="Scheduler", padx=10, pady=10)
        sched_frame.pack(pady=10)

        tk.Label(sched_frame, text="Interval (minutes):").grid(row=0, column=0)
        self.interval_entry = tk.Entry(sched_frame, width=10)
        self.interval_entry.insert(0, "1440")
        self.interval_entry.grid(row=0, column=1, padx=5)

        tk.Button(
            sched_frame,
            text="⏰ Start Scheduler",
            bg="blue",
            fg="white",
            width=20,
            command=self.start_scheduler
        ).grid(row=1, column=0, pady=5)

        tk.Button(
            sched_frame,
            text="⏹ Stop Scheduler",
            bg="red",
            fg="white",
            width=20,
            command=self.stop_scheduler_job
        ).grid(row=1, column=1, pady=5)

        # ---------------- RESULTS SECTION ----------------
        tk.Label(root, text="Execution Results", font=("Arial", 12, "bold")).pack(pady=5)

        self.results_box = ScrolledText(root, height=15, width=85)
        self.results_box.pack(padx=10, pady=5)

    # ---------------- ACTIONS ----------------

    def execute_now(self):
        self.results_box.delete("1.0", tk.END)

        try:
            test_plan_id = int(self.test_plan_entry.get())
            result = self.runner.run(test_plan_id)

            if not result or "error" in result:
                self.results_box.insert(tk.END, "❌ No test steps found\n")
                return

            self.display_results(result)

        except Exception as e:
            messagebox.showerror("Execution Error", str(e))

    def scheduler_loop(self, test_plan_id, interval_minutes):
        while not self.stop_scheduler:
            self.results_box.delete("1.0", tk.END)
            self.results_box.insert(tk.END, "⏰ Scheduled Execution Started\n\n")

            result = self.runner.run(test_plan_id)
            if result:
                self.display_results(result)

            time.sleep(interval_minutes * 60)

    def start_scheduler(self):
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            messagebox.showwarning("Scheduler", "Scheduler already running")
            return

        try:
            test_plan_id = int(self.test_plan_entry.get())
            interval = int(self.interval_entry.get())
        except ValueError:
            messagebox.showerror("Invalid Input", "Enter valid numeric values")
            return

        self.stop_scheduler = False
        self.scheduler_thread = threading.Thread(
            target=self.scheduler_loop,
            args=(test_plan_id, interval),
            daemon=True
        )
        self.scheduler_thread.start()

        messagebox.showinfo("Scheduler Started", "Automated execution started")

    def stop_scheduler_job(self):
        self.stop_scheduler = True
        messagebox.showinfo("Scheduler Stopped", "Scheduler stopped")

    # ---------------- RESULT DISPLAY ----------------

    def display_results(self, result):
        self.results_box.insert(
            tk.END,
            f"Test Step: {result['step_name']}\n"
            + "=" * 70 + "\n"
        )

        for task in result["tasks"]:
            status_icon = "✅" if task["status"] == "PASS" else "❌"

            self.results_box.insert(
                tk.END,
                f"{status_icon} Task       : {task['task_name']}\n"
                f"   Value      : {task['value']}\n"
                f"   AI Result  : {task['status']}\n"
                f"   Reason     : {task['reason']}\n"
                + "-" * 70 + "\n"
            )
