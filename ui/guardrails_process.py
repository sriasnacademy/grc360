import tkinter as tk
from tkinter import messagebox
from brcontrollers.guardrail_engine import GuardrailEngine


def open_process_screen(root):

    root.title("GRC360")
    root.geometry("500x200")

    tk.Label(root, text="Enter Process Name:", font=("Arial", 12)).pack(pady=10)

    entry_name = tk.Entry(root, width=30)
    entry_name.pack()

    def submit_process():
        pname = entry_name.get().strip()

        engine = GuardrailEngine()
        result = engine.submit(pname)

        if not result["success"]:
            messagebox.showerror("Error", result["message"])
        else:
            messagebox.shorootfo("Success", result["message"])

    tk.Button(root, text="Submit", command=submit_process, width=15).pack(pady=20)
