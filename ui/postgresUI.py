import tkinter as tk
from tkinter import ttk, messagebox
from connectors.lambda_pgvector import PGVectorDB

# Initialize Lambda client
db = PGVectorDB(function_name="grc-vectordb")

# ---------- QUERY EXECUTION ----------
def execute_query():
    query = query_text.get("1.0", tk.END).strip()

    if not query:
        messagebox.showwarning("Warning", "Please enter a SQL query")
        return

    try:
        rows = db.execute(query)

        if not rows:
            messagebox.showinfo("Info", "Query executed successfully. No rows returned.")
            clear_table()
            return

        populate_table(rows)

    except Exception as e:
        messagebox.showerror("Error", str(e))


# ---------- TABLE HELPERS ----------
def clear_table():
    table.delete(*table.get_children())

def populate_table(rows):
    clear_table()

    # Dynamically create columns based on row length
    col_count = len(rows[0])
    table["columns"] = [f"col{i}" for i in range(col_count)]
    table["show"] = "headings"

    for i in range(col_count):
        table.heading(f"col{i}", text=f"Column {i+1}")
        table.column(f"col{i}", width=120)

    for row in rows:
        table.insert("", tk.END, values=row)



def create_ui(root):
# ---------- TKINTER UI ----------
    root.title("PgVector Lambda Query Tool")
    root.geometry("900x500")

# ----- ROW 1 : Query Label -----
    label = tk.Label(root, text="SQL Query:")
    label.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

# ----- ROW 1 : Query Textbox -----
    global query_text
    query_text = tk.Text(root, height=4, width=70)
    query_text.grid(row=0, column=1, columnspan=3, padx=10, pady=10)

# ----- ROW 1 : Button -----
    btn = tk.Button(root, text="Execute Query", command=execute_query)
    btn.grid(row=0, column=4, padx=10, pady=10)

# ----- ROW 2 : Table -----
    global table
    table = ttk.Treeview(root)
    table.grid(row=1, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")

# Scrollbars
    scroll_y = ttk.Scrollbar(root, orient="vertical", command=table.yview)
    scroll_y.grid(row=1, column=5, sticky="ns")
    table.configure(yscrollcommand=scroll_y.set)

    scroll_x = ttk.Scrollbar(root, orient="horizontal", command=table.xview)
    scroll_x.grid(row=2, column=0, columnspan=5, sticky="ew")
    table.configure(xscrollcommand=scroll_x.set)

# Grid resize config
    root.grid_rowconfigure(1, weight=1)
    root.grid_columnconfigure(1, weight=1)
