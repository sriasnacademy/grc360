import tkinter as tk
from tkinter import ttk
from services.fetch_data_from_mysql import GetDataFromMySql

class GRCUISkeleton:
    
    getdata = GetDataFromMySql()
    
    def __init__(self, root):
        self.root = root
        self.root.title("GRC360")
        self.root.geometry("1100x650")
        self.root.minsize(1000, 600)

        self.setup_styles()
        self.build_layout()

    # ---------------- STYLES ----------------
    def setup_styles(self):
        style = ttk.Style()
        style.configure("Sidebar.TButton", anchor="w", padding=10)
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"))
        style.configure("SubHeader.TLabel", font=("Segoe UI", 10))

    # ---------------- LAYOUT ----------------
    def build_layout(self):
        self.root.configure(bg="#FFFFFF")

        self.main = tk.Frame(self.root, bg="#FFFFFF")
        self.main.pack(fill=tk.BOTH, expand=True)

        # Header
        self.header_bar = tk.Frame(
        self.main,
        bg="#FFFFFF",
        height=50
    )
        self.header_bar.pack(fill=tk.X)

        tk.Label(
            self.header_bar,
            text="GRC360 – Governance Risk Compliance",
            font=("Segoe UI", 14, "bold"),
            bg="#FFFFFF"
        ).pack(side=tk.LEFT, padx=15, pady=10)

        ttk.Separator(self.main, orient="horizontal").pack(fill="x")

        # Body
        self.body_frame = ttk.Frame(self.main)
        self.body_frame.pack(fill=tk.BOTH, expand=True)

        self.build_sidebar()
        self.build_content()


    # ---------------- SIDEBAR ----------------
    def build_sidebar(self):
        self.sidebar = tk.Frame(
        self.body_frame,
        width=220,
        bg="#FFFFFF"
    )
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        ttk.Label(
            self.sidebar,
            text="MENU",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 5))

        ttk.Separator(self.sidebar, orient="horizontal").pack(fill="x", padx=10, pady=5)

        menu_items = [
            ("Processes", self.show_process),
            ("Sub Processes", self.show_subprocess),
            ("Risks", self.show_risks),
            ("Controls", self.show_controls),
            ("Test Plans", self.show_testplans),
            ("Test Steps", self.show_teststeps),
            ("Test Tasks", self.show_testtasks),
        ]

        for text, command in menu_items:
            ttk.Button(
                self.sidebar,
                text=text,
                style="Sidebar.TButton",
                command=command
            ).pack(fill=tk.X, padx=10, pady=4)

        ttk.Separator(self.body_frame, orient="vertical").pack(
            side=tk.LEFT, fill=tk.Y
        )


    # ---------------- CONTENT ----------------
    def build_content(self):
        self.content = tk.Frame(
        self.body_frame,
        bg="#FFFFFF"
    )
        self.content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Page Title
        self.page_title = ttk.Label(
            self.content,
            text="Dashboard",
            font=("Segoe UI", 13, "bold")
        )
        self.page_title.pack(anchor="w", padx=15, pady=(15, 5))

        ttk.Separator(self.content, orient="horizontal").pack(fill="x", padx=15)
        self.body = ttk.Frame(self.content)
        self.body.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)


    # ---------------- HEADER ----------------
    def build_header(self):
        self.header = ttk.Frame(self.content)
        self.header.pack(fill=tk.X, padx=15, pady=10)

        self.page_title = ttk.Label(
            self.header,
            text="Dashboard",
            style="Header.TLabel"
        )
        self.page_title.pack(side=tk.LEFT)

    # ---------------- BODY (EMPTY CONTAINER) ----------------
    def build_body(self):
        self.body = tk.Frame(
        self.content,
        bg="#FFFFFF"
    )
        self.body.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)


        self.show_placeholder("Select an option from the left")

    # ---------------- UTILITIES ----------------
    def clear_body(self):
        for widget in self.body.winfo_children():
            widget.destroy()

    def show_placeholder(self, text):
        self.clear_body()
        ttk.Label(
            self.body,
            text=text,
            font=("Segoe UI", 11),
            foreground="#666"
        ).pack(expand=True)
    
    def calculate_column_widths(self, headers, data):
        widths = {}

        for header in headers:
            max_len = len(header)

            for row in data[:50]:  # limit for performance
                value = str(row.get(header, ""))
                max_len = max(max_len, len(value))

            # Convert character count to pixels (rough but effective)
            widths[header] = min(max(max_len * 7, 140), 350)

        return widths


    def render_grid(self, data):
        self.clear_body()

        if not data:
            ttk.Label(self.body, text="No data available").pack()
            return

        headers = list(data[0].keys())
        col_widths = self.calculate_column_widths(headers, data)

        # ===== Scroll container =====
        container = ttk.Frame(self.body)
        container.pack(fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(container, highlightthickness=0)
        v_scroll = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        h_scroll = ttk.Scrollbar(container, orient="horizontal", command=canvas.xview)

        canvas.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)

        grid_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=grid_frame, anchor="nw")

        grid_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        # ===== Configure columns =====
        for col, header in enumerate(headers):
            grid_frame.columnconfigure(col, minsize=col_widths[header])

        # ===== Header =====
        for col, header in enumerate(headers):
            ttk.Label(
                grid_frame,
                text=header,
                font=("Segoe UI", 10, "bold"),
                anchor="w",
                wraplength=col_widths[header] - 20
            ).grid(
                row=0, column=col,
                sticky="nsew",
                padx=10, pady=8
            )

        ttk.Separator(grid_frame, orient="horizontal").grid(
            row=1, column=0, columnspan=len(headers), sticky="ew"
        )

        # ===== Data =====
        row_num = 2
        for row in data:
            for col, header in enumerate(headers):
                ttk.Label(
                    grid_frame,
                    text=str(row.get(header, "")),
                    anchor="w",
                    justify="left",
                    wraplength=col_widths[header] - 20
                ).grid(
                    row=row_num,
                    column=col,
                    sticky="nsew",
                    padx=10,
                    pady=6
                )

            ttk.Separator(grid_frame, orient="horizontal").grid(
                row=row_num + 1,
                column=0,
                columnspan=len(headers),
                sticky="ew"
            )

            row_num += 2

    # ---------------- SIDEBAR ACTIONS ----------------
    def show_process(self):
        self.page_title.config(text="Processes")
        self.clear_body()
        processes = self.getdata.get_processes()
        self.render_grid(processes)
        
        # DB-driven widgets will be added here later
    def show_subprocess(self):
        self.page_title.config(text="Processes")
        self.clear_body()
        subprocesses = self.getdata.get_subprocesses()
        self.render_grid(subprocesses)
        
    def show_risks(self):
        self.page_title.config(text="Risks")
        self.clear_body()
        risks = self.getdata.get_risks()
        self.render_grid(risks)

    def show_controls(self):
        self.page_title.config(text="Controls")
        self.clear_body()
        controls = self.getdata.get_controls()
        self.render_grid(controls)

    def show_testplans(self):
        self.page_title.config(text="Test Plans")
        self.clear_body()
        testplans = self.getdata.get_testplan()
        self.render_grid(testplans)

    def show_teststeps(self):
        self.page_title.config(text="Test Steps")
        self.clear_body()
        teststeps = self.getdata.get_teststeps()
        self.render_grid(teststeps)
        
    def show_testtasks(self):
        self.page_title.config(text="Test Tasks")
        self.clear_body()
        testtasks = self.getdata.get_testtasks()
        self.render_grid(testtasks)

