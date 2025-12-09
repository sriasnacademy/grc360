# view_process_ui.py

import tkinter as tk
from tkinter import ttk, messagebox

from brcontrollers.brprocess import GetProcess   # <- Correct class import


def open_view_process_screen(root):
    root.title("View Processes")
    root.geometry("1000x500")
    root.configure(bg="white")

    tk.Label(root, text="Processes List", font=("Arial", 16, "bold"), bg="white").pack(pady=10)

    # ------------ TABLE COLUMNS -------------
    columns = (
        "process_id", "process_name", "description", "department",
        "process_owner", "frequency", "triggers", "outcomes"
    )

    tree = ttk.Treeview(root, columns=columns, show="headings", height=18)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=140, anchor="center")

    tree.pack(fill="both", expand=True, padx=10, pady=10)

    # ------------ LOAD DATA -------------
    try:
        gp = GetProcess()               # <- Correct object creation
        rows = gp.fetch_all_processes() # <- Correct method call

        if rows:
            for row in rows:
                tree.insert("", tk.END, values=row)
        else:
            messagebox.showinfo("Info", "No processes found.")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to load data\n{e}")


