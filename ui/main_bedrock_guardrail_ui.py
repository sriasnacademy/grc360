import tkinter as tk
from tkinter import messagebox, scrolledtext
from services.main_bedrock_service import validate_with_guardrail
import re

# ===============================
# 🔐 CUSTOM MASKING FUNCTIONS
# ===============================

def mask_mobile(text):
    return re.sub(
        r'\b([6-9]\d{6})(\d{3})\b',
        lambda m: '*' * len(m.group(1)) + m.group(2),
        text
    )

def mask_email(text):
    def replace_email(match):
        email = match.group(0)
        local, domain = email.split('@')

        masked_local = '*' * len(local)

        if '.' in domain:
            name, ext = domain.split('.', 1)
            masked_domain = '**.' + ext.upper()
        else:
            masked_domain = '**'

        return f"{masked_local}@{masked_domain}"

    return re.sub(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
        replace_email,
        text
    )

def mask_aadhaar(text):
    return re.sub(
        r'\b(\d{8})(\d{4})\b',
        lambda m: '*' * len(m.group(1)) + m.group(2),
        text
    )
def mask_name(text):
    """
    Masks names only when preceded by keywords like:
    'name is', 'Name:', 'Employee Name:'
    """
    return re.sub(
        r'(?i)(name\s*(is|:)\s*)([A-Za-z ]+)',
        lambda m: m.group(1) + ' '.join('*' * len(word) for word in m.group(3).split()),
        text
    )
def apply_custom_masking(text):
    text = mask_mobile(text)
    text = mask_email(text)
    text = mask_aadhaar(text)
    text = mask_name(text)
    return text


# ===============================
# GUARDRAIL TEST WINDOW
# ===============================
def open_guardrail_window(root):

    root.title("Guardrail Testing")
    root.geometry("750x750")

    tk.Label(root, text="Enter Text to Validate:", font=("Arial", 12)).pack(pady=10)

    text_area = scrolledtext.ScrolledText(root, width=85, height=8)
    text_area.pack(pady=10)

    output_area = scrolledtext.ScrolledText(root, width=85, height=25)
    output_area.pack(pady=10)

    # --------------------------
    # Validate Function
    # --------------------------
    def validate_text():
        user_input = text_area.get("1.0", tk.END).strip()

        if not user_input:
            messagebox.showwarning("Warning", "Please enter some text.")
            return

        try:
            result = validate_with_guardrail(user_input, source="OUTPUT")
            details = result["details"]

            # output_area.delete("1.0", tk.END)

            # --------------------
            # Basic Info
            # --------------------
            action = details.get("action")
            reason = details.get("actionReason")
            
            # output_area.insert(tk.END, f"Action: {action}\n")
            # output_area.insert(tk.END, f"Action Reason: {reason}\n\n")

            # --------------------
            # AWS Masked Output (Original functionality kept)
            # --------------------
            # if "outputs" in details and len(details["outputs"]) > 0:
            #     output_area.insert(tk.END, "AWS Output:\n")
            #     output_area.insert(tk.END, "-" * 60 + "\n")
            #     output_area.insert(tk.END, details["outputs"][0]["text"] + "\n\n")

            # --------------------
            # 🔥 YOUR CUSTOM MASKING ADDED (NEW SECTION)
            # --------------------
            custom_masked = apply_custom_masking(user_input)
            return custom_masked,action, reason
            # output_area.insert(tk.END, "Custom Masked Output:\n")
            # output_area.insert(tk.END, "-" * 60 + "\n")
            # output_area.insert(tk.END, custom_masked + "\n\n")

            # --------------------
            # Assessments (All Policies)
            # --------------------
            #assessments = details.get("assessments", [])

            #for assessment in assessments:

            #   output_area.insert(tk.END, "Policy Assessment:\n")
            #   output_area.insert(tk.END, "-" * 60 + "\n")

            #   pii_entities = assessment.get("sensitiveInformationPolicy", {}).get("piiEntities", [])

            #   for entity in pii_entities:
            #       output_area.insert(tk.END, f"Type: {entity.get('type')}\n")
            #       output_area.insert(tk.END, f"Match: {entity.get('match')}\n")
            #       output_area.insert(tk.END, f"Action Taken: {entity.get('action')}\n")
            #       output_area.insert(tk.END, "-" * 40 + "\n")

            # --------------------
            # Coverage
            # --------------------
            coverage = details.get("guardrailCoverage", {})
            text_coverage = coverage.get("textCharacters", {})

            output_area.insert(tk.END, "\nCoverage Info:\n")
            output_area.insert(tk.END, f"Guarded Characters: {text_coverage.get('guarded')}\n")
            output_area.insert(tk.END, f"Total Characters: {text_coverage.get('total')}\n")

        except Exception as e:
            output_area.delete("1.0", tk.END)
            output_area.insert(tk.END, f"❌ Error: {e}")
    tk.Button(
        root,
        text="Validate",
        command=validate_text,
        bg="blue",
        fg="white",
        width=20
    ).pack(pady=30)