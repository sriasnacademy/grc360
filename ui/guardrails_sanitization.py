import tkinter as tk
from tkinter import messagebox
import mysql.connector
from brcontrollers.br_guardrails_sanitization import GuardrailEngine

def submit_process():

    raw_name = entry_name.get()

    payload = {
        "process_name": raw_name
    }

    engine = GuardrailEngine()
    result = engine.evaluate(payload)

    # ❌ BLOCKED BY GUARDRAIL
    if not result["allowed"]:
        messagebox.showerror("Guardrail Blocked", result["message"])
        return

    # ✅ USE SANITIZED VALUE
    process_name = result["sanitized_payload"]["process_name"]

    # INSERT INTO DB
    conn = mysql.connector.connect(
        host="grc360.cmhggsagqy8d.us-east-1.rds.amazonaws.com",
        user="admin",
        password="GoodLuck25",
        database="DB_GRC360"
    )
    cur = conn.cursor()

    sql = """
    INSERT INTO processes
    (process_name, description, department, process_owner, frequency, triggers, outcomes)
    VALUES (%s,%s,%s,%s,%s,%s,%s)
    """

    cur.execute(sql, (process_name, "", "", "", "", "", ""))
    conn.commit()

    messagebox.showinfo("Success", "Process saved successfully!")

# ---------------- UI ----------------

root = tk.Tk()
root.title("Process Input Guardrails")
root.geometry("400x200")

tk.Label(root, text="Enter Process Name", font=("Arial", 12)).pack(pady=10)

entry_name = tk.Entry(root, width=35)
entry_name.pack()

tk.Button(root, text="Submit", command=submit_process, width=15).pack(pady=20)

root.mainloop()
