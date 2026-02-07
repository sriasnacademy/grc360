import tkinter as tk
from tkinter import Menu, ttk, scrolledtext

from ui.postgresUI import create_ui
from ui.guardrails_process import open_process_screen
from ui.Create_Process import prompt_Template
from ui.View_Process import open_view_process_screen
from ui.Create_Risk import risk
from ui.Create_Control import create_control
from ui.Create_subprocess import create_subporcess
from agents.intent_agent import IntentAgent
from ui.control_report_gui import ControlReportGUI
from ui.rag_bulk_ui import MainUI

agent = IntentAgent()

# ------------------------------
# AI ASSISTANT WORKSPACE CLASS
# ------------------------------
class GRC360ChatModel:

    global status_label,intent_label
    def __init__(self, workspace):
        self.user_input = tk.Entry(width=80)
        self.intent_label = tk.Label(text="Detected Intent: -")
        self.status_label = tk.Label(text="")

        workspace.configure(bg="#F2F4F7")

        # -----------------------------------
        # LEFT SIDEBAR (AI STYLE)
        # -----------------------------------
        sidebar = tk.Frame(workspace, bg="white", bd=1, relief="solid")
        sidebar.place(x=10, y=10, width=260, height=500)

        tk.Label(
            sidebar,
            text="GRC360",
            bg="white",
            font=("Arial", 16, "bold")
        ).pack(pady=12)

        # Module
        #tk.Label(sidebar, text="Module", bg="white", fg="#555").pack(anchor="w", padx=15)
        #self.module_var = tk.StringVar(value="General")
        #ttk.Combobox(
        #   sidebar,
        #    textvariable=self.module_var,
        #   values=["General", "Guardrails", "Risk Assessment", "Processes", "Audit"],
        #   state="readonly"
        #).pack(padx=15, fill="x", pady=5)

        # Guardrail Checkbox
        #self.guardrail_var = tk.BooleanVar(value=True)
        #tk.Checkbutton(
        #   sidebar,
        #   text="Apply Guardrails",
        #    variable=self.guardrail_var,
        #    bg="white"
        #).pack(anchor="w", padx=15, pady=8)

        # -----------------------------
        # QUICK ACTIONS (AI STYLE)
        # -----------------------------
        tk.Label(
            sidebar,
            text="⚡ Quick Actions",
            bg="white",
            font=("Arial", 12, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        self.create_action_card(
            sidebar,
            "🧩 Create Process",
            "Define a new business process",
            prompt_Template_Screen
        )

        self.create_action_card(
            sidebar,
            "⚠ Create Risk",
            "Identify & assess risks",
            Create_Risk_Screen
        )

        self.create_action_card(
            sidebar,
            "🛡 Create Control",
            "Mitigate identified risks",
            Create_Control_Screen
        )

        # -----------------------------
        # SYSTEM PROMPT
        # -----------------------------
        #tk.Label(sidebar, text="System Prompt", bg="white").pack(anchor="w", padx=15, pady=(15, 2))
        #self.system_prompt = tk.Text(sidebar, height=4, width=28)
        #self.system_prompt.insert(
        #   "1.0",
        #   "You are GRC360 assistant.\nProvide concise actionable answers."
        #)
        #self.system_prompt.pack(padx=15, pady=5)

        # -----------------------------------
        # CHAT AREA (UNCHANGED)
        # -----------------------------------
        chat_frame = tk.Frame(workspace, bg="white", bd=1, relief="solid")
        chat_frame.place(x=280, y=10, width=600, height=500)

        tk.Label(
            chat_frame,
            text="AI Assistant",
            bg="white",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        self.chat_box = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=("Arial", 11)
        )

        self.chat_box.tag_configure(
           "assistant_msg",
            justify="left",
            lmargin1=10,
            lmargin2=10,
            rmargin=120
        )

        self.chat_box.tag_configure(
            "user_msg",
            justify="left",      # text alignment
            lmargin1=120,        # PUSH message to right
            lmargin2=120,
            rmargin=10
        )


        self.chat_box.pack(padx=0, pady=5, fill="both", expand=True)
        self.chat_box.insert(
            tk.END,
            "System: You are GRC360 assistant.\n",
            "left_msg"
        )
        self.chat_box.insert(
            tk.END,
            "Assistant: Hi — how can I help you today?\n\n",
            "left_msg"
        )


        self.chat_box.config(state="disabled")

        input_frame = tk.Frame(chat_frame)
        input_frame.pack(fill="x", pady=5)

        self.user_input = tk.Entry(input_frame, font=("Arial", 12))
        self.user_input.pack(side="left", fill="x", expand=True, padx=5)
        self.user_input.bind("<Return>", lambda e: self.submit_text_Meghana())

        tk.Button(
            input_frame,
            text="Send",
            bg="#2563EB",
            fg="white",
            command=self.submit_text_Meghana
        ).pack(side="right", padx=5)

    # -----------------------------------
    # ACTION CARD CREATOR
    # -----------------------------------
    def create_action_card(self, parent, title, desc, command):
        card = tk.Frame(parent, bg="#F9FAFB", bd=1, relief="solid", cursor="hand2")
        card.pack(fill="x", padx=15, pady=6)

        card.bind("<Button-1>", lambda e: command())

        tk.Label(
            card,
            text=title,
            bg="#F9FAFB",
            font=("Arial", 11, "bold"),
            anchor="w"
        ).pack(fill="x", padx=10, pady=(6, 0))

        tk.Label(
            card,
            text=desc,
            bg="#F9FAFB",
            fg="#555",
            font=("Arial", 9),
            anchor="w"
        ).pack(fill="x", padx=10, pady=(0, 6))

    # -----------------------------------
    # CHAT FUNCTIONS
    # -----------------------------------
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
    # -----------------------------------
    # Meghana
    # -----------------------------------
    def submit_text_Meghana(self):
        raw_text = self.user_input.get().strip()

        if not raw_text:
            self.status_label.config(text="⚠ Please enter text.")
            return

    # Show user message (RIGHT side)
        self.append_chat("You", raw_text)
        self.user_input.delete(0, tk.END)

        try:
        # Call intent agent
            intent, assistant_response = agent.classify_intent(raw_text)

        # Update labels
            self.intent_label.config(text=f"Detected Intent: {intent}")
            self.status_label.config(text="✅ Response generated")

        # 🔥 SHOW ASSISTANT RESPONSE (LEFT side)
            self.append_chat("Assistant", assistant_response)

        except Exception as e:
            self.status_label.config(text=f"❌ UI Error: {e}")
            self.append_chat("Assistant", f"❌ Error: {e}")

    # -----------------------------------
    # End Meghana
    # -----------------------------------
    def append_chat(self, role, message):
        self.chat_box.config(state="normal")

        if role == "You":
            self.chat_box.insert(
                tk.END,
                f"You: {message}\n\n",
                "user_msg"
            )
        else:
            self.chat_box.insert(
                tk.END,
                f"{role}: {message}\n\n",
                "assistant_msg"
            )

        self.chat_box.config(state="disabled")
        self.chat_box.yview(tk.END)


# ------------------------------
# FUNCTIONS TO OPEN SCREENS
# ------------------------------
def open_mysql_pg_screen():
    create_ui(tk.Toplevel())

def execute_rag():
    root = tk.Toplevel()
    app = MainUI(root)

def open_guardrails_screen():
    open_process_screen(tk.Toplevel())

def Create_Control_Screen():
    create_control(tk.Toplevel())    
    
def prompt_Template_Screen():
    prompt_Template(tk.Toplevel())

def View_Process_Screen():
    open_view_process_screen(tk.Toplevel())

def Create_Risk_Screen():
    risk(tk.Toplevel())

def Create_SubProcess():
    create_subporcess(tk.Toplevel())

def Test_Execution():
    root = tk.Toplevel()
    app = ControlReportGUI(root)
#    root = tk.Toplevel()
#   app = ControlExecutionGUI(root)

# ------------------------------
# MAIN FORM WITH MENU + WORKSPACE
# ------------------------------
def start_main_form():
    root = tk.Tk()
    root.title("GRC_360")
    root.geometry("900x550")

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
    swetha_menu.add_command(label="Bedrock Health Check Screen", command=execute_rag)
    menubar.add_cascade(label="Swetha", menu=swetha_menu)

    # Process menu
    grc_process_menu = Menu(menubar, tearoff=0)
    grc_process_menu.add_command(label="Create Process", command=prompt_Template_Screen)
    grc_process_menu.add_command(label="View Process", command=View_Process_Screen)
    menubar.add_cascade(label="Process", menu=grc_process_menu)

    # Risk menu
    risk_menu = Menu(menubar, tearoff=0)
    risk_menu.add_command(label="Create Risk", command=Create_Risk_Screen)
    risk_menu.add_command(label="View Risk", command=View_Process_Screen)
    menubar.add_cascade(label="Risk", menu=risk_menu)

    # Control menu
    control_menu = Menu(menubar, tearoff=0)
    control_menu.add_command(label="Create Control", command=Create_Control_Screen)
    menubar.add_cascade(label="Control", menu=control_menu)

    # Audit menu
    aduit_menu = Menu(menubar, tearoff=0)
    aduit_menu.add_command(label="Test Execution", command=Test_Execution)
    menubar.add_cascade(label="Test", menu=aduit_menu)

    # Control menu
    subprocess_menu = Menu(menubar, tearoff=0)
    subprocess_menu.add_command(label="Create Subprocess", command=Create_SubProcess)
    menubar.add_cascade(label="Sub Process", menu=subprocess_menu)

    # -----------------------------
    # Process1 Menu
    # -----------------------------
    #process1_menu = Menu(menubar, tearoff=0)
    #menubar.add_cascade(label="Process1", menu=process1_menu)

    #process1_menu.add_command(label="Create Process")

    # -----------------------------
    # Sub Process Menu (inside Process1)
    # ----------------------------- 
    #subprocess_menu = Menu(process1_menu, tearoff=0)
    #process1_menu.add_cascade(label="Sub Process", menu=subprocess_menu)

    #subprocess_menu.add_command(label="SubProcess1")
    #subprocess_menu.add_command(label="SubProcess2")
    

    root.config(menu=menubar)

    # ----------------------------
    # WORKING SPACE FRAME
    # ----------------------------
    workspace = tk.Frame(root, bg="#E8EBEF")
    workspace.pack(fill="both", expand=True)

    # Load AI Assistant inside workspace
    GRC360ChatModel(workspace)

    root.mainloop()
