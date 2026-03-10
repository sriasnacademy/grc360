import tkinter as tk
from tkinter import Menu
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
from ui.overalldata import GRCUISkeleton
from ui.main_bedrock_guardrail_ui import open_guardrail_window
from services.email_service import send_stage_notification
from ui.accept_issue import AcceptIssueScreen
agent = IntentAgent()

# ─────────────────────────────────────────────
#  DESIGN TOKENS  — full light theme
# ─────────────────────────────────────────────
CLR = {
    "app_bg":         "#F0F4F8",
    # sidebar (dark navy)
    "sidebar_bg":     "#1E2A3A",
    "sidebar_accent": "#2563EB",
    "card_bg":        "#253447",
    "card_hover":     "#2E3F56",
    "card_border":    "#344A63",
    "tag_bg":         "#1A3254",
    "tag_fg":         "#60A5FA",
    "sb_text_main":   "#F0F4FF",
    "sb_text_dim":    "#94A3B8",
    "sb_text_tiny":   "#64748B",
    # chat panel (light)
    "header_bg":      "#FFFFFF",
    "header_border":  "#E2E8F0",
    "msg_bg":         "#FFFFFF",
    "msg_text":       "#1E293B",
    "user_lbl":       "#2563EB",
    "asst_lbl":       "#059669",
    "sys_text":       "#94A3B8",
    "divider":        "#E2E8F0",
    # input
    "input_bar_bg":   "#F8FAFC",
    "input_bg":       "#FFFFFF",
    "input_fg":       "#1E293B",
    "input_border":   "#CBD5E1",
    "input_focus":    "#2563EB",
    "placeholder":    "#94A3B8",
    # status
    "accent":         "#2563EB",
    "accent_hover":   "#1D4ED8",
    "success":        "#10B981",
    "warning":        "#F59E0B",
    "error":          "#EF4444",
    "scroll":         "#CBD5E1",
}

FT = {
    "title":   ("Segoe UI", 14, "bold"),
    "sub":     ("Segoe UI", 7,  "bold"),
    "section": ("Segoe UI", 8,  "bold"),
    "card":    ("Segoe UI", 10, "bold"),
    "card_d":  ("Segoe UI", 8),
    "header":  ("Segoe UI", 12, "bold"),
    "hdr_s":   ("Segoe UI", 8),
    "chat":    ("Segoe UI", 10),
    "lbl":     ("Segoe UI", 8,  "bold"),
    "input":   ("Segoe UI", 11),
    "send":    ("Segoe UI", 10, "bold"),
    "status":  ("Segoe UI", 9),
    "small":   ("Segoe UI", 8),
    "sys":     ("Segoe UI", 8),
}

SIDEBAR_W = 240   # sidebar fixed width in pixels


# ─────────────────────────────────────────────
#  SLIM SCROLLBAR
# ─────────────────────────────────────────────
class SlimScrollbar(tk.Canvas):
    def __init__(self, parent, textwidget, **kwargs):
        kwargs.pop("bg", None)
        super().__init__(parent, width=6, bg=CLR["msg_bg"],
                         highlightthickness=0, bd=0, **kwargs)
        self._tw = textwidget
        self._thumb = self.create_rectangle(
            1, 0, 5, 40, fill=CLR["scroll"], outline="", width=0)
        self._tw.configure(yscrollcommand=self._update)
        self.bind("<ButtonPress-1>", self._jump)
        self.bind("<B1-Motion>",     self._drag)
        self._lo = 0.0; self._hi = 1.0

    def _update(self, lo, hi):
        self._lo, self._hi = float(lo), float(hi)
        h = self.winfo_height() or 1
        self.coords(self._thumb, 1, int(self._lo * h),
                    5, max(int(self._lo * h) + 20, int(self._hi * h)))

    def _jump(self, e): self._drag(e)
    def _drag(self, e):
        h = self.winfo_height() or 1
        self._tw.yview_moveto(e.y / h - (self._hi - self._lo) / 2)


# ─────────────────────────────────────────────
#  SIDEBAR ACTION CARD
# ─────────────────────────────────────────────
class ActionCard(tk.Frame):
    def __init__(self, parent, icon, title, desc, command, **kwargs):
        super().__init__(parent, bg=CLR["card_bg"],
                         highlightbackground=CLR["card_border"],
                         highlightthickness=1, cursor="hand2", **kwargs)
        self._cmd = command

        badge = tk.Frame(self, bg=CLR["tag_bg"], padx=5, pady=4)
        badge.pack(side="left", padx=(10, 8), pady=8)
        tk.Label(badge, text=icon, bg=CLR["tag_bg"],
                 fg=CLR["tag_fg"], font=("Segoe UI", 13)).pack()

        txt = tk.Frame(self, bg=CLR["card_bg"])
        txt.pack(side="left", fill="both", expand=True, pady=8)
        tk.Label(txt, text=title, bg=CLR["card_bg"],
                 fg=CLR["sb_text_main"], font=FT["card"], anchor="w").pack(fill="x")
        tk.Label(txt, text=desc, bg=CLR["card_bg"],
                 fg=CLR["sb_text_dim"], font=FT["card_d"], anchor="w").pack(fill="x")

        tk.Label(self, text="›", bg=CLR["card_bg"],
                 fg=CLR["sb_text_dim"], font=("Segoe UI", 15)).pack(side="right", padx=8)

        for w in self._descendants():
            w.bind("<Button-1>", self._fire)
            w.bind("<Enter>",    self._on)
            w.bind("<Leave>",    self._off)
        self.bind("<Button-1>", self._fire)
        self.bind("<Enter>",    self._on)
        self.bind("<Leave>",    self._off)

    def _descendants(self):
        out = []
        def walk(w):
            for c in w.winfo_children(): out.append(c); walk(c)
        walk(self); return out

    def _fire(self, _=None): self._cmd()
    def _on(self,  _=None):  self.config(bg=CLR["card_hover"])
    def _off(self, _=None):  self.config(bg=CLR["card_bg"])


# ─────────────────────────────────────────────
#  MAIN CHAT CLASS
# ─────────────────────────────────────────────
class GRC360ChatModel:

    def __init__(self, workspace):
        workspace.configure(bg=CLR["app_bg"])

        # ══════════════════════════════════════
        #  SIDEBAR — fixed width, full height via pack
        # ══════════════════════════════════════
        sidebar = tk.Frame(workspace, bg=CLR["sidebar_bg"], width=SIDEBAR_W)
        sidebar.pack(side="left", fill="y")          # ← fill="y" stretches full height
        sidebar.pack_propagate(False)                # ← respect fixed width

        # accent stripe
        tk.Frame(sidebar, bg=CLR["sidebar_accent"], width=4).pack(side="left", fill="y")

        body = tk.Frame(sidebar, bg=CLR["sidebar_bg"])
        body.pack(side="left", fill="both", expand=True)

        # logo
        logo_row = tk.Frame(body, bg=CLR["sidebar_bg"])
        logo_row.pack(fill="x", padx=14, pady=(18, 2))
        dot = tk.Canvas(logo_row, width=10, height=10,
                        bg=CLR["sidebar_bg"], highlightthickness=0)
        dot.create_oval(0, 0, 10, 10, fill=CLR["sidebar_accent"], outline="")
        dot.pack(side="left", pady=3)
        tk.Label(logo_row, text="  GRC360", bg=CLR["sidebar_bg"],
                 fg=CLR["sb_text_main"], font=FT["title"]).pack(side="left")

        tk.Label(body, text="GOVERNANCE · RISK · COMPLIANCE",
                 bg=CLR["sidebar_bg"], fg=CLR["sb_text_tiny"],
                 font=FT["sub"]).pack(anchor="w", padx=14, pady=(0, 10))

        tk.Frame(body, bg=CLR["card_border"], height=1).pack(fill="x", padx=14, pady=(0, 10))

        tk.Label(body, text="⚡  QUICK ACTIONS",
                 bg=CLR["sidebar_bg"], fg=CLR["sb_text_dim"],
                 font=FT["section"]).pack(anchor="w", padx=14, pady=(0, 6))

        ActionCard(body, "🧩", "Create Process",
                   "Define a new business process",
                   prompt_Template_Screen).pack(fill="x", padx=10, pady=3)
        ActionCard(body, "⚠", "Create Risk",
                   "Identify & assess risks",
                   Create_Risk_Screen).pack(fill="x", padx=10, pady=3)
        ActionCard(body, "🛡", "Create Control",
                   "Mitigate identified risks",
                   Create_Control_Screen).pack(fill="x", padx=10, pady=3)

        # status at bottom
        self.intent_label = tk.Label(
            body, text="Intent: —",
            bg=CLR["sidebar_bg"], fg=CLR["sb_text_dim"], font=FT["status"])
        self.intent_label.pack(side="bottom", anchor="w", padx=14, pady=(0, 8))

        self.status_label = tk.Label(
            body, text="● System Ready",
            bg=CLR["sidebar_bg"], fg=CLR["success"], font=FT["status"])
        self.status_label.pack(side="bottom", anchor="w", padx=14, pady=(0, 2))

        # ══════════════════════════════════════
        #  CHAT PANEL — fills remaining space
        # ══════════════════════════════════════
        chat_panel = tk.Frame(workspace, bg=CLR["msg_bg"])
        chat_panel.pack(side="left", fill="both", expand=True)  # ← expand fills width & height

        # ── Header ────────────────────────────
        header = tk.Frame(chat_panel, bg=CLR["header_bg"], height=52)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        av = tk.Canvas(header, width=34, height=34,
                       bg=CLR["header_bg"], highlightthickness=0)
        av.create_oval(0, 0, 34, 34, fill=CLR["accent"], outline="")
        av.create_text(17, 17, text="AI", fill="white",
                       font=("Segoe UI", 10, "bold"))
        av.pack(side="left", padx=(14, 10), pady=9)

        htxt = tk.Frame(header, bg=CLR["header_bg"])
        htxt.pack(side="left", pady=9)
        tk.Label(htxt, text="AI Assistant", bg=CLR["header_bg"],
                 fg="#1E293B", font=FT["header"]).pack(anchor="w")
        tk.Label(htxt, text="GRC360 Intelligence Layer",
                 bg=CLR["header_bg"], fg="#94A3B8",
                 font=FT["hdr_s"]).pack(anchor="w")

        pill = tk.Frame(header, bg="#ECFDF5",
                        highlightbackground="#6EE7B7", highlightthickness=1)
        pill.pack(side="right", padx=14, pady=16)
        tk.Label(pill, text="● Online", bg="#ECFDF5", fg="#059669",
                 font=("Segoe UI", 8, "bold"), padx=8, pady=2).pack()

        tk.Frame(chat_panel, bg=CLR["header_border"], height=1).pack(fill="x")

        # ── Input bar (pack BEFORE message area so it anchors to bottom) ──
        tk.Frame(chat_panel, bg=CLR["divider"], height=1).pack(fill="x", side="bottom")

        input_bar = tk.Frame(chat_panel, bg=CLR["input_bar_bg"], height=58)
        input_bar.pack(fill="x", side="bottom")      # ← anchored to bottom
        input_bar.pack_propagate(False)

        self.user_input = tk.Entry(
            input_bar,
            font=FT["input"],
            bg=CLR["input_bg"],
            fg=CLR["input_fg"],
            insertbackground=CLR["input_fg"],
            relief="solid",
            bd=1,
            highlightthickness=2,
            highlightbackground=CLR["input_border"],
            highlightcolor=CLR["input_focus"],
        )
        self.user_input.pack(side="left", fill="both", expand=True,
                             padx=(14, 8), pady=10, ipady=3)
        self.user_input.bind("<Return>", lambda e: self._send())

        # placeholder
        self._ph = "Type your message here…"
        self.user_input.insert(0, self._ph)
        self.user_input.config(fg=CLR["placeholder"])

        def _fi(_):
            if self.user_input.get() == self._ph:
                self.user_input.delete(0, tk.END)
                self.user_input.config(fg=CLR["input_fg"])

        def _fo(_):
            if not self.user_input.get():
                self.user_input.insert(0, self._ph)
                self.user_input.config(fg=CLR["placeholder"])

        self.user_input.bind("<FocusIn>",  _fi)
        self.user_input.bind("<FocusOut>", _fo)

        tk.Button(
            input_bar,
            text="Send  ›",
            font=FT["send"],
            bg=CLR["accent"],
            fg="#FFFFFF",
            activebackground=CLR["accent_hover"],
            activeforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=16,
            pady=6,
            cursor="hand2",
            command=self._send,
        ).pack(side="right", padx=(0, 14), pady=10)

        # ── Message area (fills the remaining middle space) ───
        msg_wrap = tk.Frame(chat_panel, bg=CLR["msg_bg"])
        msg_wrap.pack(fill="both", expand=True)      # ← takes all remaining height

        self.chat_box = tk.Text(
            msg_wrap,
            wrap=tk.WORD,
            font=FT["chat"],
            bg=CLR["msg_bg"],
            fg=CLR["msg_text"],
            insertbackground=CLR["msg_text"],
            selectbackground=CLR["accent"],
            selectforeground="#FFFFFF",
            relief="flat",
            bd=0,
            padx=20,
            pady=14,
            cursor="arrow",
            spacing1=2,
            spacing3=6,
        )
        self.chat_box.pack(side="left", fill="both", expand=True)

        SlimScrollbar(msg_wrap, self.chat_box).pack(
            side="right", fill="y", pady=4, padx=(0, 2))

        # text tags
        self.chat_box.tag_configure("sys",
            justify="center", foreground=CLR["sys_text"], font=FT["sys"])
        self.chat_box.tag_configure("you_lbl",
            lmargin1=180, lmargin2=180, rmargin=8,
            foreground=CLR["user_lbl"], font=FT["lbl"])
        self.chat_box.tag_configure("you_msg",
            lmargin1=180, lmargin2=180, rmargin=8,
            foreground=CLR["msg_text"], font=FT["chat"])
        self.chat_box.tag_configure("bot_lbl",
            lmargin1=8, lmargin2=8, rmargin=180,
            foreground=CLR["asst_lbl"], font=FT["lbl"])
        self.chat_box.tag_configure("bot_msg",
            lmargin1=8, lmargin2=8, rmargin=180,
            foreground=CLR["msg_text"], font=FT["chat"])

        # seed greeting
        self.chat_box.config(state="normal")
        self.chat_box.insert(tk.END, "── Session started ──\n\n", "sys")
        self.chat_box.insert(tk.END, "Assistant\n", "bot_lbl")
        self.chat_box.insert(tk.END, "Hi — how can I help you today?\n\n", "bot_msg")
        self.chat_box.config(state="disabled")

    # ─────────────────────────────────────────
    #  CHAT LOGIC  (functionality unchanged)
    # ─────────────────────────────────────────
    def _send(self):
        self.submit_text_Meghana()

    def submit_text_Meghana(self):
        raw_text = self.user_input.get().strip()
        if not raw_text or raw_text == self._ph:
            self.status_label.config(text="⚠ Please enter text.", fg=CLR["warning"])
            return

        self.append_chat("You", raw_text)
        self.user_input.delete(0, tk.END)

        try:
            intent, assistant_response = agent.classify_intent(raw_text)
            self.intent_label.config(text=f"Intent: {intent}")
            self.status_label.config(text="● Response generated", fg=CLR["success"])
            self.append_chat("Assistant", assistant_response)
        except Exception as e:
            self.status_label.config(text="❌ Error", fg=CLR["error"])
            self.append_chat("Assistant", f"❌ Error: {e}")

    def append_chat(self, role, message):
        self.chat_box.config(state="normal")
        if role == "You":
            self.chat_box.insert(tk.END, "You\n",          "you_lbl")
            self.chat_box.insert(tk.END, f"{message}\n\n", "you_msg")
        else:
            self.chat_box.insert(tk.END, "Assistant\n",    "bot_lbl")
            self.chat_box.insert(tk.END, f"{message}\n\n", "bot_msg")
        self.chat_box.config(state="disabled")
        self.chat_box.yview(tk.END)


# ─────────────────────────────────────────────
#  SCREEN LAUNCHERS  (unchanged)
# ─────────────────────────────────────────────
def open_mysql_pg_screen():        create_ui(tk.Toplevel())
def open_overalldata_screen():
    root = tk.Toplevel(); GRCUISkeleton(root)
def execute_rag():
    root = tk.Toplevel(); MainUI(root)
def open_guardrails_screen():      open_process_screen(tk.Toplevel())
def Create_Control_Screen():       create_control(tk.Toplevel())
def prompt_Template_Screen():      prompt_Template(tk.Toplevel())
def View_Process_Screen():         open_view_process_screen(tk.Toplevel())
def Create_Risk_Screen():          risk(tk.Toplevel())
def Create_SubProcess():           create_subporcess(tk.Toplevel())
def open_main_bedrock_guardrail(): open_guardrail_window(tk.Toplevel())
def Test_Execution():
    root = tk.Toplevel(); ControlReportGUI(root)
    
def Accpet_Issue():
    root = tk.Toplevel(); AcceptIssueScreen(root,"MANAGER","siri123")

def send_email():
    send_stage_notification("ssmiley120@gmail.com","Something",1,"First","NONE")


# ─────────────────────────────────────────────
#  MAIN FORM
# ─────────────────────────────────────────────
def start_main_form():
    root = tk.Tk()
    root.title("GRC_360")
    root.geometry("900x560")        # slightly taller to give menu bar room
    root.minsize(800, 500)          # prevent squashing
    root.configure(bg=CLR["app_bg"])

    # light menu bar
    menubar = Menu(root, bg="#FFFFFF", fg="#1E293B",
                   activebackground=CLR["accent"], activeforeground="#FFFFFF",
                   relief="flat", bd=0)

    def make_menu(label, items):
        m = Menu(menubar, tearoff=0, bg="#FFFFFF", fg="#1E293B",
                 activebackground=CLR["accent"], activeforeground="#FFFFFF",
                 relief="flat", bd=1)
        for lbl, cmd in items:
            m.add_command(label=lbl, command=cmd)
        menubar.add_cascade(label=label, menu=m)

    make_menu("Sirisha",     [("MySQL & PostgreSQL",             open_mysql_pg_screen)])
    make_menu("Data",        [("View Overall Data",              open_overalldata_screen)])
    make_menu("Swetha",      [("Bedrock Health Check Screen",    execute_rag),
                               ("Main Bedrock Guardrail Testing", open_main_bedrock_guardrail),
                               ("Mail Service", send_email)])
    make_menu("Process",     [("Create Process",                 prompt_Template_Screen),
                               ("View Process",                   View_Process_Screen)])
    make_menu("Risk",        [("Create Risk",                    Create_Risk_Screen),
                               ("View Risk",                      View_Process_Screen)])
    make_menu("Control",     [("Create Control",                 Create_Control_Screen)])
    make_menu("Test",        [("Test Execution",                 Test_Execution)])
    make_menu("Sub Process", [("Create Subprocess",              Create_SubProcess)])
    make_menu("Workflow", [("Accept Issue",              Accpet_Issue),
                           ("Fix Issue", Create_SubProcess)])
    root.config(menu=menubar)

    # workspace fills everything below the menu bar automatically
    workspace = tk.Frame(root, bg=CLR["app_bg"])
    workspace.pack(fill="both", expand=True)

    GRC360ChatModel(workspace)
    root.mainloop()