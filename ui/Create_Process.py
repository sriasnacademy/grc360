import tkinter as tk
from agents.intent_agent import IntentAgent

agent = IntentAgent()

def submit_text():
    raw_text = entry.get()

    if not raw_text.strip():
        status_label.config(text="⚠ Please enter text.")
        return

    try:
        intent, status = agent.classify_intent(raw_text)

        intent_label.config(text=f"Detected Intent: {intent}")
        status_label.config(text=status)

    except Exception as e:
        status_label.config(text=f"❌ UI Error: {e}")


def prompt_Template(root):
    root.geometry("500x250")
    root.title("GRC360")

    tk.Label(root, text="Enter Process / Control Text").pack(pady=5)

    global entry
    entry = tk.Entry(root, width=60)
    entry.pack(pady=5)

    tk.Button(root, text="Submit", command=submit_text).pack(pady=10)

    # ✅ Labels for output
    global intent_label, status_label

    intent_label = tk.Label(root, text="", fg="blue", font=("Arial", 10, "bold"))
    intent_label.pack()

    status_label = tk.Label(root, text="", fg="green", font=("Arial", 10))
    status_label.pack()

