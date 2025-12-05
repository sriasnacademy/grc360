import tkinter as tk
from agents.intent_agent import IntentAgent
from openai import OpenAI

# ✅ Initialize LLM and Agent properly
llm_client = OpenAI(api_key="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" \
"")
agent = IntentAgent(llm_client)

def prompt_Template(root):
    root.title("GRC360")
    root.geometry("500x200")
    
    # ----- ROW 1 -----
    label1 = tk.Label(root, text="Enter Text:")
    label1.grid(row=0, column=0, padx=10, pady=10)

    entry1 = tk.Entry(root, width=25)
    entry1.grid(row=0, column=1, padx=10, pady=10)

    status1 = tk.Label(root, text="")
    status1.grid(row=0, column=2, padx=10, pady=10)

    # ✅ Button event handler
    def submit_text():
        user_input = entry1.get()     # ✅ get text properly
        if not user_input.strip():
            status1.config(text="⚠ Enter input")
            return

        intent = agent.classify_intent(user_input)
        status1.config(text=f"✅ {intent}")

    # ✅ BUTTON
    btn1 = tk.Button(
        root,
        text="MySQL Submit",
        command=submit_text
    )
    btn1.grid(row=1, column=1, padx=10, pady=10)
