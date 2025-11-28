# ui.py

import tkinter as tk
from brcontrollers.brsample import handle_submit

def create_ui(root):
    root.title("GRC360")
    root.geometry("500x200")

    # ----- ROW 1 -----
    label1 = tk.Label(root, text="Name:")
    label1.grid(row=0, column=0, padx=10, pady=10)

    entry1 = tk.Entry(root, width=25)
    entry1.grid(row=0, column=1, padx=10, pady=10)

    status1 = tk.Label(root, text="")
    status1.grid(row=0, column=2, padx=10, pady=10)

    btn1 = tk.Button(root, text="MySQl Submit",
                     command=lambda: handle_submit(entry1, status1))
    btn1.grid(row=0, column=3, padx=10, pady=10)


    # ----- ROW 2 -----
    label2 = tk.Label(root, text="Name:")
    label2.grid(row=1, column=0, padx=10, pady=10)

    entry2 = tk.Entry(root, width=25)
    entry2.grid(row=1, column=1, padx=10, pady=10)

    status2 = tk.Label(root, text="")
    status2.grid(row=1, column=2, padx=10, pady=10)

    btn2 = tk.Button(root, text="Submit",
                     command=lambda: handle_submit(entry2, status2))
    btn2.grid(row=1, column=3, padx=10, pady=10)
