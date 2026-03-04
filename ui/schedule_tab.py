import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime, timedelta

# ── only import, no DB code here ──────────────────────────────────
from services.schedule_service import ScheduleRepository


class ScheduleTab:
    """
    Self-contained Schedule tab with a right-side Schedule Report panel.
    Usage in ControlReportGUI:
        from ui.schedule_tab import ScheduleTab
        ScheduleTab(self.tabs)
    """

    def __init__(self, notebook):
        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="Schedule")
        self.repo = ScheduleRepository()   # ← single instance, no DB code in UI
        self._build()

    # ======================================================
    # BUILD UI  — zero DB calls
    # ======================================================
    def _build(self):
        # ── Top-level horizontal split: LEFT form | RIGHT report ──
        self.paned = tk.PanedWindow(
            self.frame, orient="horizontal",
            sashrelief="raised", sashwidth=6,
            bg="#D1D5DB"
        )
        self.paned.pack(fill="both", expand=True)

        # ── LEFT pane (original scheduling form) ──────────────────
        left_frame = tk.Frame(self.paned, bg="#FFFFFF")
        self.paned.add(left_frame, minsize=360)

        # scrollable wrapper inside left pane
        canvas  = tk.Canvas(left_frame, highlightthickness=0, bg="#FFFFFF")
        vscroll = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        outer = tk.Frame(canvas, bg="#FFFFFF")
        canvas.create_window((0, 0), window=outer, anchor="nw")
        outer.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        # ── Mouse wheel scroll (Windows + Linux) ──────────────────
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        def _on_mousewheel_linux(event):
            canvas.yview_scroll(-1 if event.num == 4 else 1, "units")

        canvas.bind("<Enter>",  lambda _: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>",  lambda _: canvas.unbind_all("<MouseWheel>"))
        canvas.bind("<Enter>",  lambda _: (canvas.bind_all("<Button-4>", _on_mousewheel_linux),
                                           canvas.bind_all("<Button-5>", _on_mousewheel_linux)))


        P = dict(padx=16, pady=3)

        # ── SECTION 1 · Test Plan ─────────────────────────────────
        self._section(outer, "①  Select Test Plan")

        row1 = tk.Frame(outer, bg="#FFFFFF"); row1.pack(fill="x", **P)

        tk.Label(row1, text="Test Plan",
                 font=("Segoe UI", 10), width=16, anchor="w",
                 bg="#FFFFFF").pack(side="left")

        self.plan_var   = tk.StringVar()
        self.plan_combo = ttk.Combobox(
            row1, textvariable=self.plan_var,
            state="readonly", width=28, font=("Segoe UI", 10))
        self.plan_combo.pack(side="left", padx=6)
        self.plan_combo.bind("<<ComboboxSelected>>", lambda _: self._refresh_preview())

        tk.Button(
            row1, text="⟳ Refresh",
            font=("Segoe UI", 9),
            command=self._load_plans
        ).pack(side="left", padx=4)

        # ── SECTION 2 · Date & Time (IST) ────────────────────────
        self._section(outer, "②  Schedule Date & Time  (IST)")

        dt = tk.Frame(outer, bg="#FFFFFF"); dt.pack(fill="x", **P)

        tk.Label(dt, text="Date (DD / MM / YYYY)",
                 font=("Segoe UI", 10), width=22, anchor="w",
                 bg="#FFFFFF").grid(row=0, column=0, sticky="w", pady=4)

        drow = tk.Frame(dt, bg="#FFFFFF"); drow.grid(row=0, column=1, sticky="w")
        now = datetime.now()
        self.sd_day   = self._spin(drow, 1,    31,   now.day,   4)
        tk.Label(drow, text=" / ", font=("Segoe UI", 11), bg="#FFFFFF").pack(side="left")
        self.sd_month = self._spin(drow, 1,    12,   now.month, 4)
        tk.Label(drow, text=" / ", font=("Segoe UI", 11), bg="#FFFFFF").pack(side="left")
        self.sd_year  = self._spin(drow, 2024, 2035, now.year,  6)

        tk.Label(dt, text="Time (HH : MM)",
                 font=("Segoe UI", 10), width=22, anchor="w",
                 bg="#FFFFFF").grid(row=1, column=0, sticky="w", pady=4)

        trow = tk.Frame(dt, bg="#FFFFFF"); trow.grid(row=1, column=1, sticky="w")
        self.sd_hour = self._spin(trow, 0, 23, now.hour,   4)
        tk.Label(trow, text=" : ", font=("Segoe UI", 12, "bold"), bg="#FFFFFF").pack(side="left")
        self.sd_min  = self._spin(trow, 0, 59, now.minute, 4)
        tk.Label(trow, text="  IST", font=("Segoe UI", 9),
                 fg="#888", bg="#FFFFFF").pack(side="left")

        # quick-set buttons
        qrow = tk.Frame(dt, bg="#FFFFFF"); qrow.grid(row=2, column=1, sticky="w", pady=6)
        tk.Label(qrow, text="Quick set:",
                 font=("Segoe UI", 9), fg="#666", bg="#FFFFFF").pack(side="left", padx=(0, 6))
        for lbl, mins in [("+15 min", 15), ("+30 min", 30),
                          ("+1 hr",   60), ("+2 hr",  120)]:
            tk.Button(
                qrow, text=lbl, font=("Segoe UI", 9),
                bg="#EEF2FF", fg="#3730A3", relief="flat", padx=8,
                command=lambda m=mins: self._quick_set(m)
            ).pack(side="left", padx=3)

        # ── SECTION 3 · UTC Preview ───────────────────────────────
        self._section(outer, "③  UTC Preview  (stored in MySQL)")

        pf = tk.Frame(outer, bg="#F0FDF4", bd=1, relief="solid")
        pf.pack(fill="x", padx=16, pady=4)
        pi = tk.Frame(pf, bg="#F0FDF4"); pi.pack(fill="x", padx=12, pady=8)

        def _row(text, row, color):
            tk.Label(pi, text=text, font=("Segoe UI", 10), bg="#F0FDF4",
                     fg=color, width=18, anchor="w").grid(row=row, column=0, sticky="w")
            lbl = tk.Label(pi, text="—", font=("Courier New", 10, "bold"),
                           bg="#F0FDF4", fg=color)
            lbl.grid(row=row, column=1, sticky="w")
            return lbl

        self.lbl_ist = _row("IST entered :",  0, "#166534")
        self.lbl_utc = _row("UTC to store :", 1, "#1E40AF")

        tk.Label(pi, text="SQL preview :", font=("Segoe UI", 10), bg="#F0FDF4",
                 fg="#6B21A8", width=18, anchor="w").grid(row=2, column=0, sticky="nw", pady=(6,0))
        self.lbl_sql = tk.Label(pi, text="—", font=("Courier New", 9),
                                bg="#F0FDF4", fg="#6B21A8",
                                wraplength=280, justify="left")
        self.lbl_sql.grid(row=2, column=1, sticky="w", pady=(6, 0))

        tk.Button(
            pi, text="⟳  Refresh Preview",
            font=("Segoe UI", 9), bg="#DBEAFE",
            command=self._refresh_preview
        ).grid(row=3, column=1, sticky="w", pady=(10, 0))

        # ── SECTION 4 · Recurrence ────────────────────────────────
        self._section(outer, "④  Recurrence")

        rrow = tk.Frame(outer, bg="#FFFFFF"); rrow.pack(fill="x", **P)
        self.recurrence_var = tk.StringVar(value="ONCE")
        for val, lbl in [("ONCE",    "One-time"),
                         ("DAILY",   "Daily"),
                         ("WEEKLY",  "Weekly"),
                         ("MONTHLY", "Monthly")]:
            tk.Radiobutton(
                rrow, text=f"  {lbl}  ",
                variable=self.recurrence_var, value=val,
                font=("Segoe UI", 10), bg="#FFFFFF"
            ).pack(side="left", padx=10)

        # ── SECTION 5 · Action Buttons ────────────────────────────
        self._section(outer, "")

        brow = tk.Frame(outer, bg="#FFFFFF"); brow.pack(pady=10, padx=16, anchor="w")

        tk.Button(
            brow,
            text="  ⚡  Schedule Test Plan  ",
            bg="#0D6EFD", fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat", padx=10, pady=8,
            command=self._submit
        ).pack(side="left", padx=(0, 10))

        tk.Button(
            brow,
            text="  ↺  Reset  ",
            bg="#6C757D", fg="white",
            font=("Segoe UI", 11),
            relief="flat", padx=10, pady=8,
            command=self._reset
        ).pack(side="left")

        # ── RIGHT pane (Schedule Report) ──────────────────────────
        self._build_report_panel()

        # ── load plans once on startup ────────────────────────────
        self._load_plans()

        # ── Set initial sash: left panel 400px, right gets the rest ──
        self.frame.update_idletasks()
        self.paned.sash_place(0, 400, 0)

    # ======================================================
    # RIGHT PANEL  — Schedule Report
    # ======================================================
    def _build_report_panel(self):
        right_frame = tk.Frame(self.paned, bg="#F8FAFC")
        self.paned.add(right_frame, minsize=420)

        # ── Header bar ────────────────────────────────────────────
        header = tk.Frame(right_frame, bg="#0B5ED7", pady=0)
        header.pack(fill="x")

        tk.Label(
            header,
            text="📋  Schedule Report",
            font=("Segoe UI", 12, "bold"),
            bg="#0B5ED7", fg="white",
            padx=16, pady=10
        ).pack(side="left")

        # Status filter
        filter_frame = tk.Frame(header, bg="#0B5ED7")
        filter_frame.pack(side="right", padx=10, pady=6)

        tk.Label(filter_frame, text="Filter:",
                 font=("Segoe UI", 9), bg="#0B5ED7",
                 fg="#BFDBFE").pack(side="left", padx=(0, 4))

        self.filter_var = tk.StringVar(value="ALL")
        self.filter_combo = ttk.Combobox(
            filter_frame, textvariable=self.filter_var,
            values=["ALL", "PENDING", "RUNNING", "COMPLETED", "FAILED"],
            state="readonly", width=12, font=("Segoe UI", 9)
        )
        self.filter_combo.pack(side="left", padx=(0, 6))
        self.filter_combo.bind("<<ComboboxSelected>>", lambda _: self._load_report())

        tk.Button(
            filter_frame,
            text="⟳ Refresh",
            font=("Segoe UI", 9),
            bg="#1D4ED8", fg="white",
            relief="flat", padx=8, pady=2,
            command=self._load_report
        ).pack(side="left")

        # ── Summary stats bar ─────────────────────────────────────
        stats_frame = tk.Frame(right_frame, bg="#EFF6FF", bd=0)
        stats_frame.pack(fill="x", padx=0, pady=0)

        self.stat_labels = {}
        stats_config = [
            ("TOTAL",     "#1E40AF", "#DBEAFE"),
            ("PENDING",   "#92400E", "#FEF3C7"),
            ("RUNNING",   "#065F46", "#D1FAE5"),
            ("COMPLETED", "#1E3A5F", "#BFDBFE"),
            ("FAILED",    "#7F1D1D", "#FEE2E2"),
        ]
        for key, fg, bg in stats_config:
            box = tk.Frame(stats_frame, bg=bg, padx=12, pady=6)
            box.pack(side="left", expand=True, fill="x", padx=1, pady=4)
            tk.Label(box, text=key, font=("Segoe UI", 7, "bold"),
                     bg=bg, fg=fg).pack()
            lbl = tk.Label(box, text="—", font=("Segoe UI", 14, "bold"),
                           bg=bg, fg=fg)
            lbl.pack()
            self.stat_labels[key] = lbl

        # ── Treeview table ────────────────────────────────────────
        table_frame = tk.Frame(right_frame, bg="#F8FAFC")
        table_frame.pack(fill="both", expand=True, padx=8, pady=(4, 0))

        # Style
        style = ttk.Style()
        style.configure(
            "Report.Treeview",
            font=("Segoe UI", 9),
            rowheight=28,
            background="#FFFFFF",
            fieldbackground="#FFFFFF",
            foreground="#1F2937",
        )
        style.configure(
            "Report.Treeview.Heading",
            font=("Segoe UI", 9, "bold"),
            background="#E2E8F0",
            foreground="#374151",
            relief="flat",
        )
        style.map("Report.Treeview",
                  background=[("selected", "#BFDBFE")],
                  foreground=[("selected", "#1E3A8A")])

        columns = ("id", "plan", "scheduled_ist", "scheduled_utc", "recurrence", "status", "created")
        self.report_tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            style="Report.Treeview",
            selectmode="browse"
        )

        col_config = [
            ("id",            "ID",             50,  "center"),
            ("plan",          "Test Plan",      160, "w"),
            ("scheduled_ist", "Scheduled (IST)",140, "center"),
            ("scheduled_utc", "Scheduled (UTC)",140, "center"),
            ("recurrence",    "Recurrence",      80, "center"),
            ("status",        "Status",          80, "center"),
            ("created",       "Created",        120, "center"),
        ]
        for col, heading, width, anchor in col_config:
            self.report_tree.heading(col, text=heading,
                                     command=lambda c=col: self._sort_tree(c))
            self.report_tree.column(col, width=width, anchor=anchor, minwidth=40)

        # Scrollbars
        vsb = ttk.Scrollbar(table_frame, orient="vertical",
                            command=self.report_tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal",
                            command=self.report_tree.xview)
        self.report_tree.configure(yscrollcommand=vsb.set,
                                   xscrollcommand=hsb.set)

        self.report_tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Tag colours for status
        self.report_tree.tag_configure("PENDING",   background="#FFFBEB", foreground="#92400E")
        self.report_tree.tag_configure("RUNNING",   background="#ECFDF5", foreground="#065F46")
        self.report_tree.tag_configure("COMPLETED", background="#EFF6FF", foreground="#1E3A8A")
        self.report_tree.tag_configure("FAILED",    background="#FEF2F2", foreground="#991B1B")
        self.report_tree.tag_configure("odd",       background="#F9FAFB")

        # Right-click context menu
        self.ctx_menu = tk.Menu(self.report_tree, tearoff=0)
        self.ctx_menu.add_command(label="🗑  Delete Schedule",   command=self._delete_selected)
        self.ctx_menu.add_command(label="🔄  Mark as CANCELLED", command=self._cancel_selected)
        self.ctx_menu.add_separator()
        self.ctx_menu.add_command(label="⟳  Refresh Table",     command=self._load_report)
        self.report_tree.bind("<Button-3>", self._show_ctx_menu)
        self.report_tree.bind("<Double-1>",  lambda _: self._show_detail())

        # ── Footer bar ────────────────────────────────────────────
        footer = tk.Frame(right_frame, bg="#E2E8F0", pady=4)
        footer.pack(fill="x", side="bottom")

        self.lbl_report_status = tk.Label(
            footer,
            text="Last refreshed: —",
            font=("Segoe UI", 8), fg="#6B7280", bg="#E2E8F0"
        )
        self.lbl_report_status.pack(side="left", padx=10)

        tk.Button(
            footer,
            text="🗑  Delete Selected",
            font=("Segoe UI", 8),
            bg="#FEE2E2", fg="#991B1B",
            relief="flat", padx=8, pady=2,
            command=self._delete_selected
        ).pack(side="right", padx=6)

        tk.Button(
            footer,
            text="⟳  Refresh",
            font=("Segoe UI", 8),
            bg="#DBEAFE", fg="#1E3A8A",
            relief="flat", padx=8, pady=2,
            command=self._load_report
        ).pack(side="right", padx=2)

        # Sort state tracker
        self._sort_col   = "id"
        self._sort_asc   = False

        # Load report data on startup
        self._load_report()

    # ======================================================
    # REPORT HELPERS
    # ======================================================
    @staticmethod
    def _utc_to_ist_str(utc_str: str) -> str:
        """Convert a UTC datetime string to IST string for display."""
        try:
            utc_dt = datetime.strptime(utc_str, "%Y-%m-%d %H:%M:%S")
            ist_dt = utc_dt + timedelta(hours=5, minutes=30)
            return ist_dt.strftime("%d %b %Y  %H:%M")
        except Exception:
            return utc_str

    def _load_report(self):
        """Fetch scheduled rows from DB and populate the treeview."""
        try:
            status_filter = self.filter_var.get()
            rows = self.repo.fetch_schedules(
                status=None if status_filter == "ALL" else status_filter
            )
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not load schedule report:\n{e}")
            return

        # Clear existing rows
        for item in self.report_tree.get_children():
            self.report_tree.delete(item)

        # Update stat counters
        counts = {"TOTAL": len(rows), "PENDING": 0, "RUNNING": 0, "COMPLETED": 0, "FAILED": 0}
        for r in rows:
            s = r.get("status", "").upper()
            if s in counts:
                counts[s] += 1
        for key, lbl in self.stat_labels.items():
            lbl.config(text=str(counts.get(key, "—")))

        # Populate rows
        for idx, r in enumerate(rows):
            utc_str  = r.get("scheduled_datetime", "")
            ist_str  = self._utc_to_ist_str(utc_str)
            utc_disp = utc_str[:16] if len(utc_str) >= 16 else utc_str
            status   = r.get("status", "").upper()

            tag = status if status in ("PENDING", "RUNNING", "COMPLETED", "FAILED") \
                  else ("odd" if idx % 2 else "")

            created_raw = r.get("created_at", "")
            try:
                created_disp = datetime.strptime(
                    str(created_raw), "%Y-%m-%d %H:%M:%S"
                ).strftime("%d %b %Y  %H:%M")
            except Exception:
                created_disp = str(created_raw)

            self.report_tree.insert(
                "", "end",
                iid=str(r.get("id", idx)),
                values=(
                    r.get("id", ""),
                    r.get("test_plan_name", r.get("test_plan_id", "")),
                    ist_str,
                    utc_disp,
                    r.get("recurrence", ""),
                    status,
                    created_disp,
                ),
                tags=(tag,)
            )

        self.lbl_report_status.config(
            text=f"Last refreshed: {datetime.now().strftime('%H:%M:%S')}  |  "
                 f"{len(rows)} record(s)"
        )

    def _sort_tree(self, col: str):
        """Toggle sort on column header click."""
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_col = col
            self._sort_asc = True

        rows = [(self.report_tree.set(k, col), k)
                for k in self.report_tree.get_children("")]
        rows.sort(reverse=not self._sort_asc,
                  key=lambda x: (x[0].lower() if isinstance(x[0], str) else x[0]))
        for idx, (_, k) in enumerate(rows):
            self.report_tree.move(k, "", idx)

    def _show_ctx_menu(self, event):
        row = self.report_tree.identify_row(event.y)
        if row:
            self.report_tree.selection_set(row)
            self.ctx_menu.tk_popup(event.x_root, event.y_root)

    def _get_selected_id(self):
        sel = self.report_tree.selection()
        if not sel:
            messagebox.showwarning("No Selection", "Please select a schedule row first.")
            return None
        return int(sel[0])

    def _delete_selected(self):
        row_id = self._get_selected_id()
        if row_id is None:
            return
        vals = self.report_tree.item(str(row_id), "values")
        plan_name = vals[1] if vals else str(row_id)
        if not messagebox.askyesno(
            "Confirm Delete",
            f"Delete schedule #{row_id}  ({plan_name})?\nThis cannot be undone."
        ):
            return
        try:
            self.repo.delete_schedule(row_id)
            self._load_report()
            messagebox.showinfo("Deleted", f"Schedule #{row_id} deleted.")
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not delete schedule:\n{e}")

    def _cancel_selected(self):
        row_id = self._get_selected_id()
        if row_id is None:
            return
        try:
            self.repo.update_schedule_status(row_id, "CANCELLED")
            self._load_report()
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not update status:\n{e}")

    def _show_detail(self):
        """Show a detail popup for the double-clicked row."""
        sel = self.report_tree.selection()
        if not sel:
            return
        vals = self.report_tree.item(sel[0], "values")
        if not vals:
            return
        labels = ["ID", "Test Plan", "Scheduled (IST)", "Scheduled (UTC)",
                  "Recurrence", "Status", "Created"]
        detail = "\n".join(f"  {l:<18}: {v}" for l, v in zip(labels, vals))
        messagebox.showinfo(f"Schedule Detail — #{vals[0]}", detail)

    # ======================================================
    # INTERNAL HELPERS  — pure UI logic, no SQL
    # ======================================================
    def _section(self, parent, title):
        f = tk.Frame(parent, bg="#FFFFFF"); f.pack(fill="x", padx=16, pady=(10, 2))
        if title:
            tk.Label(f, text=title,
                     font=("Segoe UI", 10, "bold"), fg="#0B5ED7",
                     bg="#FFFFFF").pack(side="left")
        ttk.Separator(f, orient="horizontal").pack(
            side="left", fill="x", expand=True, padx=8)

    def _spin(self, parent, from_, to, init, width):
        s = tk.Spinbox(parent, from_=from_, to=to,
                       width=width, font=("Segoe UI", 10), justify="center")
        s.delete(0, "end"); s.insert(0, str(init).zfill(2))
        s.pack(side="left", padx=2)
        return s

    def _read_ist(self) -> datetime:
        return datetime(
            int(self.sd_year.get()),  int(self.sd_month.get()),
            int(self.sd_day.get()),   int(self.sd_hour.get()),
            int(self.sd_min.get()),   0)

    @staticmethod
    def _to_utc(ist: datetime) -> datetime:
        return ist - timedelta(hours=5, minutes=30)

    def _quick_set(self, mins: int):
        try:   base = self._read_ist()
        except: base = datetime.now()
        t = base + timedelta(minutes=mins)
        for spin, val in [(self.sd_day,   t.day),
                          (self.sd_month, t.month),
                          (self.sd_year,  t.year),
                          (self.sd_hour,  t.hour),
                          (self.sd_min,   t.minute)]:
            spin.delete(0, "end"); spin.insert(0, str(val).zfill(2))
        self._refresh_preview()

    def _refresh_preview(self):
        try:
            ist = self._read_ist()
            utc = self._to_utc(ist)
            pid = self.plan_map.get(self.plan_var.get(), "?")

            self.lbl_ist.config(text=ist.strftime("%d %b %Y   %H:%M  IST"))
            self.lbl_utc.config(text=utc.strftime("%Y-%m-%d %H:%M:%S  UTC"))
            self.lbl_sql.config(
                text=f"INSERT INTO test_plan_scheduling\n"
                     f"  (test_plan_id, status, scheduled_datetime)\n"
                     f"VALUES ({pid}, 'PENDING', '{utc.strftime('%Y-%m-%d %H:%M:%S')}');")
        except Exception:
            pass

    def _reset(self):
        n = datetime.now()
        for spin, val in [(self.sd_day,   n.day),
                          (self.sd_month, n.month),
                          (self.sd_year,  n.year),
                          (self.sd_hour,  n.hour),
                          (self.sd_min,   n.minute)]:
            spin.delete(0, "end"); spin.insert(0, str(val).zfill(2))
        self.recurrence_var.set("ONCE")
        self._refresh_preview()

    # ======================================================
    # DB CALLS  — only delegated to repository
    # ======================================================
    def _load_plans(self):
        """Fetch plan names from DB → populate combobox."""
        try:
            plans = self.repo.fetch_test_plans()
            self.plan_map = {p["test_plan_name"]: p["test_plan_id"] for p in plans}
            self.plan_combo["values"] = list(self.plan_map.keys())
            if self.plan_map:
                self.plan_combo.current(0)
                self._refresh_preview()
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not load test plans:\n{e}")

    def _submit(self):
        """Validate → confirm → INSERT via repository → refresh report."""

        if not self.plan_var.get():
            messagebox.showwarning("Missing", "Please select a test plan.")
            return

        try:
            ist = self._read_ist()
        except ValueError as e:
            messagebox.showerror("Invalid Date", str(e))
            return

        if ist <= datetime.now():
            messagebox.showwarning(
                "Past Time",
                f"{ist.strftime('%d %b %Y  %H:%M  IST')} is in the past.\n"
                "Please choose a future time.")
            return

        utc = self._to_utc(ist)
        pid = self.plan_map[self.plan_var.get()]
        rec = self.recurrence_var.get()

        if not messagebox.askyesno(
            "Confirm Schedule",
            f"Test Plan  :  {self.plan_var.get()}\n"
            f"IST time   :  {ist.strftime('%d %b %Y  %H:%M')}\n"
            f"UTC stored :  {utc.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"Recurrence :  {rec}\n\n"
            f"Proceed?"
        ):
            return

        try:
            row_id = self.repo.insert_schedule(
                test_plan_id=pid,
                utc_datetime=utc.strftime("%Y-%m-%d %H:%M:%S"),
                recurrence=rec
            )
            messagebox.showinfo(
                "Scheduled ✅",
                f"'{self.plan_var.get()}' scheduled successfully!\n\n"
                f"Row ID     :  {row_id}\n"
                f"IST time   :  {ist.strftime('%d %b %Y  %H:%M')}\n"
                f"UTC stored :  {utc.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Status     :  PENDING\n"
                f"Recurrence :  {rec}"
            )
            # ← auto-refresh report panel after a new schedule is saved
            self._load_report()

        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to save schedule:\n{e}")