import tkinter as tk
from tkinter import messagebox
import threading

from utils.bulk_data_rag_builder import ragbuild


class MainUI:

    def __init__(self, root):
        self.root = root
        self.root.title("GRC RAG Builder")
        self.root.geometry("400x200")

        # Title
        title = tk.Label(
            root,
            text="Process → RAG Builder",
            font=("Arial", 14, "bold")
        )
        title.pack(pady=20)

        # Button
        self.rag_button = tk.Button(
            root,
            text="Build Process RAG",
            width=25,
            height=2,
            command=self.on_rag_click
        )
        self.rag_button.pack(pady=10)

        # Status label
        self.status = tk.Label(root, text="", fg="green")
        self.status.pack(pady=10)

    def on_rag_click(self):
        """
        Runs RAG build in a background thread
        (UI will NOT freeze)
        """
        self.status.config(text="Running RAG build...")
        self.rag_button.config(state="disabled")

        thread = threading.Thread(target=self.run_rag)
        thread.start()

    def run_rag(self):
        try:
            service = ragbuild()
            service.ragbuild()

            self.status.config(text="RAG build completed successfully ✅")
            messagebox.showinfo("Success", "Process RAG build completed")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.status.config(text="RAG build failed ❌")

        finally:
            self.rag_button.config(state="normal")
