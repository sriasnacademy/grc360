import tkinter as tk
from tkinter import Menu

from ui.sampleScreen import create_ui
from ui.guardrails_process import open_process_screen

# ------------------------------
# FUNCTIONS TO OPEN SCREENS
# ------------------------------
def open_mysql_pg_screen():
    create_ui(tk.Toplevel())

def open_guardrails_screen():
    open_process_screen(tk.Toplevel())

# ------------------------------
# MAIN FORM START FUNCTION
# ------------------------------
def start_main_form():
    root = tk.Tk()
    root.title("GRC_360")
    root.geometry("700x600")

    label = tk.Label(root, text="GRC 360", font=("Arial", 20))
    label.pack(pady=50)

    # Menu bar
    menubar = Menu(root)

    # Sirisha menu
    sirisha_menu = Menu(menubar, tearoff=0)
    sirisha_menu.add_command(label="MySQL & PostgreSQL", command=open_mysql_pg_screen)
    menubar.add_cascade(label="Sirisha", menu=sirisha_menu)

    # Meghana menu
    meghana_menu = Menu(menubar, tearoff=0)
    meghana_menu.add_command(label="Guardrails Screen", command=open_guardrails_screen)
    menubar.add_cascade(label="Meghana", menu=meghana_menu)

    # Swetha menu
    swetha_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Swetha", menu=swetha_menu)

    # Process menu
    swetha_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Process", menu=swetha_menu)

    # Risk menu
    swetha_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Risk", menu=swetha_menu)

    # Control menu
    swetha_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Control", menu=swetha_menu)

    # Audit menu
    swetha_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Audit", menu=swetha_menu)

    root.config(menu=menubar)
    root.mainloop()
