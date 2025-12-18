import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from brcontrollers.br_Guardrails_PII import PIIService


def launch_ui(root):
    # -------- INIT SERVICE --------
    pii_service = PIIService()

    # -------- MAIN WINDOW --------
    root.title("PDF Sensitive Data Anonymizer")
    root.geometry("1200x600")
    root.configure(bg="#F5F6FA")

    # -------- FUNCTIONS (INNER) --------
    def load_pdf():
        file_path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[
        ("All Files", "*.*"),
        ("Text Files", "*.txt"),
        ("PDF Files", "*.pdf"),
        ("Word Files", "*.docx")]
        )

        if not file_path:
            return

        try:
            text = pii_service.read_file(file_path)
            txt_original.delete("1.0", tk.END)
            txt_original.insert(tk.END, text)
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def anonymize_text():
        original_text = txt_original.get("1.0", tk.END).strip()

        if not original_text:
            messagebox.showwarning("Warning", "Please load a PDF first")
            return

        anonymized = pii_service.anonymize_text(original_text)
        txt_anonymized.delete("1.0", tk.END)
        txt_anonymized.insert(tk.END, anonymized)

    # -------- BUTTONS --------
    btn_frame = tk.Frame(root, bg="#F5F6FA")
    btn_frame.pack(pady=10)

    tk.Button(
        btn_frame,
        text="Load PDF",
        width=15,
        bg="#2F80ED",
        fg="white",
        command=load_pdf
    ).pack(side=tk.LEFT, padx=10)

    tk.Button(
        btn_frame,
        text="Anonymize",
        width=15,
        bg="#27AE60",
        fg="white",
        command=anonymize_text
    ).pack(side=tk.LEFT, padx=10)

    # -------- TEXT AREAS --------
    text_frame = tk.Frame(root)
    text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    tk.Label(
        text_frame,
        text="Original PDF Text",
        font=("Arial", 11, "bold")
    ).grid(row=0, column=0)

    tk.Label(
        text_frame,
        text="Anonymized Text",
        font=("Arial", 11, "bold")
    ).grid(row=0, column=1)

    txt_original = scrolledtext.ScrolledText(
        text_frame,
        wrap=tk.WORD
    )
    txt_original.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

    txt_anonymized = scrolledtext.ScrolledText(
        text_frame,
        wrap=tk.WORD
    )
    txt_anonymized.grid(row=1, column=1, padx=5, pady=5, sticky="nsew")

    text_frame.columnconfigure(0, weight=1)
    text_frame.columnconfigure(1, weight=1)
    text_frame.rowconfigure(1, weight=1)

