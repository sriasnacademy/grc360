import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from datetime import datetime, timedelta

# ── only import, no DB code here ──────────────────────────────────
from services.schedule_service import ScheduleRepository


class ScheduleTab:
    """
    Self-contained Schedule tab.
    Usage in ControlReportGUI:
        from ui.schedule_tab import ScheduleTab
        ScheduleTab(self.tabs)
    """

    def __init__(self, notebook):
        self.frame = tk.Frame(notebook)
        notebook.add(self.frame, text="Schedule")
        self.repo  = ScheduleRepository()   # ← single instance, no DB code in UI
        self._build()

    # ======================================================
    # BUILD UI  — zero DB calls
    # ======================================================
    def _build(self):

        # scrollable wrapper
        canvas  = tk.Canvas(self.frame, highlightthickness=0)
        vscroll = ttk.Scrollbar(self.frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        vscroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        outer = tk.Frame(canvas)
        canvas.create_window((0, 0), window=outer, anchor="nw")
        outer.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        P = dict(padx=30, pady=6)

        # ── SECTION 1 · Test Plan ─────────────────────────────────
        self._section(outer, "①  Select Test Plan")

        row1 = tk.Frame(outer); row1.pack(fill="x", **P)

        tk.Label(row1, text="Test Plan",
                 font=("Segoe UI", 10), width=16, anchor="w").pack(side="left")

        self.plan_var   = tk.StringVar()
        self.plan_combo = ttk.Combobox(
            row1, textvariable=self.plan_var,
            state="readonly", width=50, font=("Segoe UI", 10))
        self.plan_combo.pack(side="left", padx=6)
        self.plan_combo.bind("<<ComboboxSelected>>", lambda _: self._refresh_preview())

        tk.Button(
            row1, text="⟳ Refresh",
            font=("Segoe UI", 9),
            command=self._load_plans
        ).pack(side="left", padx=4)

        # ── SECTION 2 · Date & Time (IST) ────────────────────────
        self._section(outer, "②  Schedule Date & Time  (IST)")

        dt = tk.Frame(outer); dt.pack(fill="x", **P)

        tk.Label(dt, text="Date (DD / MM / YYYY)",
                 font=("Segoe UI", 10), width=22, anchor="w").grid(
            row=0, column=0, sticky="w", pady=4)

        drow = tk.Frame(dt); drow.grid(row=0, column=1, sticky="w")
        now = datetime.now()
        self.sd_day   = self._spin(drow, 1,    31,   now.day,   4)
        tk.Label(drow, text=" / ", font=("Segoe UI", 11)).pack(side="left")
        self.sd_month = self._spin(drow, 1,    12,   now.month, 4)
        tk.Label(drow, text=" / ", font=("Segoe UI", 11)).pack(side="left")
        self.sd_year  = self._spin(drow, 2024, 2035, now.year,  6)

        tk.Label(dt, text="Time (HH : MM)",
                 font=("Segoe UI", 10), width=22, anchor="w").grid(
            row=1, column=0, sticky="w", pady=4)

        trow = tk.Frame(dt); trow.grid(row=1, column=1, sticky="w")
        self.sd_hour = self._spin(trow, 0, 23, now.hour,   4)
        tk.Label(trow, text=" : ", font=("Segoe UI", 12, "bold")).pack(side="left")
        self.sd_min  = self._spin(trow, 0, 59, now.minute, 4)
        tk.Label(trow, text="  IST", font=("Segoe UI", 9), fg="#888").pack(side="left")

        # quick-set buttons
        qrow = tk.Frame(dt); qrow.grid(row=2, column=1, sticky="w", pady=6)
        tk.Label(qrow, text="Quick set:",
                 font=("Segoe UI", 9), fg="#666").pack(side="left", padx=(0, 6))
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
        pf.pack(fill="x", padx=30, pady=6)
        pi = tk.Frame(pf, bg="#F0FDF4"); pi.pack(fill="x", padx=18, pady=12)

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
                                wraplength=520, justify="left")
        self.lbl_sql.grid(row=2, column=1, sticky="w", pady=(6, 0))

        tk.Button(
            pi, text="⟳  Refresh Preview",
            font=("Segoe UI", 9), bg="#DBEAFE",
            command=self._refresh_preview
        ).grid(row=3, column=1, sticky="w", pady=(10, 0))

        # ── SECTION 4 · Recurrence ────────────────────────────────
        self._section(outer, "④  Recurrence")

        rrow = tk.Frame(outer); rrow.pack(fill="x", **P)
        self.recurrence_var = tk.StringVar(value="ONCE")
        for val, lbl in [("ONCE",    "One-time"),
                         ("DAILY",   "Daily"),
                         ("WEEKLY",  "Weekly"),
                         ("MONTHLY", "Monthly")]:
            tk.Radiobutton(
                rrow, text=f"  {lbl}  ",
                variable=self.recurrence_var, value=val,
                font=("Segoe UI", 10)
            ).pack(side="left", padx=10)

        # ── SECTION 5 · Action Buttons ────────────────────────────
        self._section(outer, "")

        brow = tk.Frame(outer); brow.pack(pady=20, padx=30, anchor="w")

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

        # ── load plans once on startup ────────────────────────────
        self._load_plans()

    # ======================================================
    # INTERNAL HELPERS  — pure UI logic, no SQL
    # ======================================================
    def _section(self, parent, title):
        f = tk.Frame(parent); f.pack(fill="x", padx=30, pady=(18, 2))
        if title:
            tk.Label(f, text=title,
                     font=("Segoe UI", 10, "bold"), fg="#0B5ED7").pack(side="left")
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
    # DB CALLS  — only two, both delegated to repository
    # ======================================================
    def _load_plans(self):
        """Fetch plan names from DB → populate combobox. Called once on startup."""
        try:
            plans = self.repo.fetch_test_plans()                # ← repository call
            self.plan_map = {p["test_plan_name"]: p["test_plan_id"] for p in plans}
            self.plan_combo["values"] = list(self.plan_map.keys())
            if self.plan_map:
                self.plan_combo.current(0)
                self._refresh_preview()
        except Exception as e:
            messagebox.showerror("DB Error", f"Could not load test plans:\n{e}")

    def _submit(self):
        """Validate → confirm → INSERT via repository. Only DB write in this file."""

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
            row_id = self.repo.insert_schedule(                 # ← repository call
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
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to save schedule:\n{e}")