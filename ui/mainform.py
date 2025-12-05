import tkinter as tk
from tkinter import Menu

from ui.sampleScreen import create_ui
from ui.guardrails_process import open_process_screen
from ui.Create_Process import prompt_Template
from ui.Create_Risk import risk
from ui.Create_Control import control

# ------------------------------
# FUNCTIONS TO OPEN SCREENS
# ------------------------------
def open_mysql_pg_screen():
    create_ui(tk.Toplevel())

def open_guardrails_screen():
    open_process_screen(tk.Toplevel())

def prompt_Template_Screen():
    prompt_Template(tk.Toplevel())

def risk_Screen():
    risk(tk.Toplevel())

def control_Screen():
    control(tk.Toplevel())

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
    grc_process_menu = Menu(menubar, tearoff=0)
    grc_process_menu.add_command(label="Create Process", command=prompt_Template_Screen)
    grc_process_menu.add_command(label="View Process")
    menubar.add_cascade(label="Process", menu=grc_process_menu)

    # Risk menu
    grc_risk_menu = Menu(menubar, tearoff=0)
    grc_risk_menu.add_command(label="Create Risk", command=risk_Screen)
    grc_risk_menu.add_command(label="View Risk")
    menubar.add_cascade(label="Risk", menu=grc_risk_menu)

    # Control menu
    grc_control_menu = Menu(menubar, tearoff=0)
    grc_control_menu.add_command(label="Create Control", command=control_Screen)
    grc_control_menu.add_command(label="View Control")
    menubar.add_cascade(label="Control", menu=grc_control_menu)

    # Audit menu
    grc_audit_menu = Menu(menubar, tearoff=0)
    grc_audit_menu.add_command(label="Create Audit")
    menubar.add_cascade(label="Audit", menu=grc_audit_menu)

    root.config(menu=menubar)
    root.mainloop()
