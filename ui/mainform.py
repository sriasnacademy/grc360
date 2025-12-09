import tkinter as tk
from tkinter import Menu, ttk, scrolledtext

from ui.sampleScreen import create_ui
from ui.guardrails_process import open_process_screen
from ui.Create_Process import prompt_Template
from ui.View_Process import open_view_process_screen

# ------------------------------
# AI ASSISTANT WORKSPACE CLASS
# ------------------------------
class GRC360ChatModel:
    def __init__(self, workspace):

        # FULL WORKSPACE AREA
        workspace.configure(bg="#F2F4F7")

        # -----------------------------------
        # LEFT SIDEBAR
        # -----------------------------------
        sidebar = tk.Frame(workspace, bg="white", bd=1, relief="solid")
        sidebar.place(x=10, y=10, width=260, height=660)

        tk.Label(sidebar, text="GRC360", bg="white",
                 font=("Arial", 14, "bold")).pack(pady=10)

        # Module
        tk.Label(sidebar, text="Module", bg="white").pack(anchor="w", padx=12)
        self.module_var = tk.StringVar(value="General")
        ttk.Combobox(sidebar, textvariable=self.module_var,
                     values=["General", "Guardrails", "Risk Assessment", "Processes", "Audit"],
                     state="readonly").pack(padx=12, fill="x", pady=5)

        # Guardrail Checkbox
        self.guardrail_var = tk.BooleanVar(value=True)
        tk.Checkbutton(sidebar, text="Apply Guardrails",
                       variable=self.guardrail_var, bg="white").pack(anchor="w", padx=12, pady=5)

        # System Prompt
        tk.Label(sidebar, text="System Prompt", bg="white").pack(anchor="w", padx=12)
        self.system_prompt = tk.Text(sidebar, height=5, width=30)
        self.system_prompt.insert("1.0", "You are GRC360 assistant. Provide concise actionable answers.")
        self.system_prompt.pack(padx=12, pady=5)

        # Sample buttons
        tk.Button(sidebar, text="Insert Risk",
                  command=lambda: self.insert_sample("risk")).pack(padx=12, pady=5, fill="x")
        tk.Button(sidebar, text="Create Process",
                  command=lambda: self.insert_sample("process")).pack(padx=12, pady=5, fill="x")
        tk.Button(sidebar, text="Insert Guardrail",
                  command=lambda: self.insert_sample("guardrail")).pack(padx=12, pady=5, fill="x")

        # -----------------------------------
        # CHAT AREA
        # -----------------------------------
        chat_frame = tk.Frame(workspace, bg="white", bd=1, relief="solid")
        chat_frame.place(x=280, y=10, width=950, height=660)

        tk.Label(chat_frame, text="AI Assistant", bg="white",
                 font=("Arial", 14, "bold")).pack(pady=10)

        # Chat window
        self.chat_box = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, font=("Arial", 11))
        self.chat_box.pack(padx=10, pady=5, fill="both", expand=True)
        self.chat_box.insert(tk.END, "System: You are GRC360 assistant.\n")
        self.chat_box.insert(tk.END, "Assistant: Hi — how can I help you with GRC360 today?\n\n")
        self.chat_box.config(state="disabled")

        # Input box
        input_frame = tk.Frame(chat_frame)
        input_frame.pack(fill="x", pady=5)
        
        # TEXT ENTRY
        self.user_input = tk.Entry(input_frame, font=("Arial", 12))
        self.user_input.pack(side="left", fill="x", expand=True, padx=5)
        self.user_input.bind("<Return>", lambda e: self.send_message())

        # SEND BUTTON
        tk.Button(input_frame, text="Send",
                  command=self.send_message).pack(side="right", padx=5)

    # Sample insert functions
    def insert_sample(self, kind):
        if kind == "risk":
            self.user_input.insert(0, "Submit risk: title=Data Leak, rating=High, impact=Severe, likelihood=Likely")
        elif kind == "process":
            self.user_input.insert(0, "Create process: name=Employee Onboarding, owner=HR, steps=Document verification, IT setup")
        elif kind == "guardrail":
            self.user_input.insert(0, "Add guardrail: name=No PII export, type=output, severity=high")

    def send_message(self):
        text = self.user_input.get().strip()
        if not text:
            return

        self.append_chat("You", text)
        self.user_input.delete(0, tk.END)

        module = self.module_var.get()
        gr = "ON" if self.guardrail_var.get() else "OFF"

        response = f"[Module: {module} | Guardrails {gr}]\nProcessed: {text}"

        self.append_chat("Assistant", response)

    def append_chat(self, role, message):
        self.chat_box.config(state="normal")
        self.chat_box.insert(tk.END, f"{role}: {message}\n\n")
        self.chat_box.config(state="disabled")
        self.chat_box.yview(tk.END)

# ------------------------------
# FUNCTIONS TO OPEN SCREENS
# ------------------------------
def open_mysql_pg_screen():
    create_ui(tk.Toplevel())

def open_guardrails_screen():
    open_process_screen(tk.Toplevel())
    
    
def prompt_Template_Screen():
    prompt_Template(tk.Toplevel())

def View_Process_Screen():
    open_view_process_screen(tk.Toplevel())

# ------------------------------
# MAIN FORM WITH MENU + WORKSPACE
# ------------------------------
def start_main_form():
    root = tk.Tk()
    root.title("GRC_360")
    root.geometry("1300x700")

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
    grc_process_menu.add_command(label="View Process", command=View_Process_Screen)
    menubar.add_cascade(label="Process", menu=grc_process_menu)

    # Risk menu
    risk_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Risk", menu=risk_menu)

    # Control menu
    control_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Control", menu=control_menu)

    # Audit menu
    aduit_menu = Menu(menubar, tearoff=0)
    menubar.add_cascade(label="Audit", menu=aduit_menu)

    root.config(menu=menubar)

    # ----------------------------
    # WORKING SPACE FRAME
    # ----------------------------
    workspace = tk.Frame(root, bg="#E8EBEF")
    workspace.pack(fill="both", expand=True)

    # Load AI Assistant inside workspace
    GRC360ChatModel(workspace)

    root.mainloop()
