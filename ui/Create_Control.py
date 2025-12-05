import tkinter as tk
from brcontrollers.brsample import *
from brcontrollers.test_lambda import call_lambda

def control(root):
    root.title("GRC360")
    root.geometry("500x200")

    tk.Label(root, text="Enter your Control", font=("Arial", 12)).pack(pady=10)

    entry_name = tk.Entry(root, width=30)
    entry_name.pack()
    tk.Button(root, text="Submit", width=15).pack(pady=20)