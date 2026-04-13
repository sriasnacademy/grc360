"""
ui/attribution_dashboard.py
Attribution Dashboard — DB Powered (Fixed + Styled)
"""

import tkinter as tk
from tkinter import ttk
import json, os
from datetime import datetime
from connectors.lambda_mysql import call_lambda


# ── DB Fetch Functions ──────────────────────
def fetch_from_db(action_type=None, tag=None, actor=None):
    conditions = []
    params = []

    if action_type:
        conditions.append("action_type = %s")
        params.append(action_type)

    if tag:
        conditions.append("JSON_CONTAINS(tags, %s)")
        params.append(json.dumps(tag))

    if actor:
        conditions.append("LOWER(actor_name) LIKE %s")
        params.append(f"%{actor.lower()}%")

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    payload = {
        "action": "raw_sql",
        "sql": f"""
            SELECT 
                record_id,
                action_type,
                actor_name,
                confidence,
                decision_summary,
                timestamp,
                checksum
            FROM attribution_records
            {where_clause}
            ORDER BY timestamp DESC
            LIMIT 500
        """,
        "params": params
    }

    res = call_lambda(payload)

    # ✅ Handle API Gateway response
    # Handle multiple response formats
    if isinstance(res, dict):

        # Case 1: Your current Lambda format
        if "records" in res:
            return res.get("records", [])

        # Case 2: Standard format
        if "data" in res:
            return res.get("data", [])

        # Case 3: API Gateway wrapped
        if "body" in res:
            try:
                body = json.loads(res["body"])
                return body.get("records", []) or body.get("data", [])
            except:
                return []

    return []


def fetch_record_by_id(record_id):
    payload = {
        "action": "raw_sql",
        "sql": "SELECT * FROM attribution_records WHERE record_id = %s",
        "params": [record_id]
    }

    res = call_lambda(payload)

    if "body" in res:
        res = json.loads(res["body"])

    data = res.get("records", [])
    return data[0] if data else {}


def fetch_summary():
    payload = {
        "action": "raw_sql",
        "sql": "SELECT action_type, COUNT(*) as count FROM attribution_records GROUP BY action_type",
        "params": []
    }

    res = call_lambda(payload)
    if "body" in res:
        res = json.loads(res["body"])
    by_action = res.get("data", [])

    payload2 = {
        "action": "raw_sql",
        "sql": "SELECT actor_name, COUNT(*) as count FROM attribution_records GROUP BY actor_name",
        "params": []
    }

    res2 = call_lambda(payload2)
    if "body" in res2:
        res2 = json.loads(res2["body"])
    by_actor = res2.get("data", [])

    return {
        "by_action": {r["action_type"]: r["count"] for r in by_action},
        "by_actor": {r["actor_name"]: r["count"] for r in by_actor},
        "total_records": sum(r["count"] for r in by_action)
    }


# ── UI Colors (Restored) ───────────────────
CLR = {
    "app_bg": "#F0F4F8",
    "sidebar_bg": "#1E2A3A",
    "accent": "#2563EB",
    "card_bg": "#253447",
    "sb_text_main": "#F0F4FF",
    "sb_text_dim": "#94A3B8",
    "header_bg": "#FFFFFF",
    "msg_bg": "#FFFFFF",
    "msg_text": "#1E293B",
}

ACTION_COLORS = {
    "intent_classification": "#2563EB",
    "control_pipeline": "#10B981",
    "risk_pipeline": "#F97316",
    "process_pipeline": "#0EA5E9",
    "subprocess_pipeline": "#8B5CF6",
}


# ───────────────────────────────────────────
def open_attribution_dashboard(parent=None):
    win = tk.Toplevel(parent) if parent else tk.Tk()
    win.title("Attribution Dashboard")
    win.geometry("1250x720")
    win.configure(bg=CLR["app_bg"])

    # HEADER
    header = tk.Frame(win, bg=CLR["sidebar_bg"], height=52)
    header.pack(fill="x")

    tk.Label(header, text="🔍 Attribution Dashboard",
             bg=CLR["sidebar_bg"], fg="white",
             font=("Segoe UI", 12, "bold")).pack(side="left", padx=16)

    count_var = tk.StringVar(value="0 records")
    tk.Label(header, textvariable=count_var,
             bg=CLR["accent"], fg="white",
             font=("Segoe UI", 9, "bold"),
             padx=10, pady=4).pack(side="right", padx=16)

    # FILTER BAR
    fbar = tk.Frame(win, bg=CLR["header_bg"])
    fbar.pack(fill="x")

    action_var = tk.StringVar(value="ALL")
    ttk.Combobox(fbar, textvariable=action_var,
                 values=["ALL","risk_pipeline","control_pipeline","process_pipeline"],
                 width=25, state="readonly").pack(side="left", padx=8, pady=8)

    tag_var = tk.StringVar()
    tk.Entry(fbar, textvariable=tag_var, width=15).pack(side="left", padx=5)

    actor_var = tk.StringVar()
    tk.Entry(fbar, textvariable=actor_var, width=15).pack(side="left", padx=5)

    # BODY
    body = tk.Frame(win, bg=CLR["app_bg"])
    body.pack(fill="both", expand=True, padx=8, pady=8)

    # TABLE STYLE
    style = ttk.Style()
    style.theme_use("clam")

    style.configure("Custom.Treeview",
        background=CLR["msg_bg"],
        foreground=CLR["msg_text"],
        fieldbackground=CLR["msg_bg"],
        rowheight=28,
        font=("Segoe UI", 9)
    )

    style.configure("Custom.Treeview.Heading",
        background=CLR["card_bg"],
        foreground=CLR["sb_text_main"],
        font=("Segoe UI", 9, "bold")
    )

    style.map("Custom.Treeview",
        background=[("selected", CLR["accent"])]
    )

    # TABLE
    cols = ("Time","Action","Actor","Conf","Summary","✓")
    tree = ttk.Treeview(body, columns=cols, show="headings", style="Custom.Treeview")

    for c in cols:
        tree.heading(c, text=c)

    tree.column("Time", width=150)
    tree.column("Action", width=160)
    tree.column("Actor", width=140)
    tree.column("Conf", width=70)
    tree.column("Summary", width=400)
    tree.column("✓", width=40)

    tree.pack(side="left", fill="both", expand=True)

    # ── Right: Detail pane ───────────────────
    right = tk.Frame(body, bg=CLR["card_bg"], width=360)
    right.pack(side="right", fill="y", padx=(8, 0))
    right.pack_propagate(False)

    tk.Label(right, text="Record Detail",
             bg=CLR["card_bg"], fg=CLR["sb_text_main"],
             font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 4))

    detail = tk.Text(right, wrap="word", font=("Courier", 9),
                     bg="#1A2535", fg="#C8D6E5",
                     insertbackground="white", relief="flat",
                     padx=8, pady=8, state="disabled")
    detail.pack(fill="both", expand=True, padx=6, pady=(0, 6))

    dsb = ttk.Scrollbar(right, orient="vertical", command=detail.yview)
    detail.configure(yscrollcommand=dsb.set)
    dsb.pack(side="right", fill="y")

    # ── Status bar ───────────────────────────
    sbar = tk.Frame(win, bg=CLR["sidebar_bg"], height=26)
    sbar.pack(fill="x", side="bottom")
    sbar.pack_propagate(False)
    status_var = tk.StringVar(value="Ready")
    tk.Label(sbar, textvariable=status_var,
             bg=CLR["sidebar_bg"], fg=CLR["sb_text_dim"],
             font=("Segoe UI", 8), anchor="w").pack(side="left", padx=10, pady=4)
    # ══════════════════════════════════════════
    # DATA FUNCTIONS
    # ══════════════════════════════════════════
    record_map = {}
    # ── Populate ────────────────────────────
    def populate():
        tree.delete(*tree.get_children())
        record_map.clear()

        records = fetch_from_db(
            None if action_var.get()=="ALL" else action_var.get(),
            tag_var.get(),
            actor_var.get()
        )

        for rec in records:
            valid = "✅" if rec.get("checksum") else "❌"

            iid = tree.insert("", "end", values=(
                rec.get("timestamp"),
                rec.get("action_type"),
                rec.get("actor_name"),
                rec.get("confidence"),
                rec.get("decision_summary")[:60],
                valid
            ))

            color = ACTION_COLORS.get(rec.get("action_type"), "#94A3B8")
            tree.tag_configure(rec.get("action_type"), foreground=color)
            tree.item(iid, tags=(rec.get("action_type"),))

            record_map[iid] = rec

        count_var.set(f"{len(records)} records")
    
    def format_attribution_report(rec):
        if not rec:
            return "No record found"

        # Safe extraction (DB → UI format)
        record_id = rec.get("record_id", "")
        timestamp = rec.get("timestamp", "")
        action = rec.get("action_type", "")
        actor = rec.get("actor_name", "")
        confidence = rec.get("confidence", "").upper()
        decision = rec.get("decision_summary", "")
        reasoning = rec.get("reasoning", "N/A")
        checksum = rec.get("checksum", "")

        # Optional fields (if stored as JSON in DB)
        try:
            tags = rec.get("tags", [])
            if isinstance(tags, str):
                tags = json.loads(tags)
        except:
            tags = []

        try:
            frameworks = rec.get("framework_refs", [])
            if isinstance(frameworks, str):
                frameworks = json.loads(frameworks)
        except:
            frameworks = []

        try:
            sources = rec.get("sources", [])
            if isinstance(sources, str):
                sources = json.loads(sources)
        except:
            sources = []

        # Format sections
        fw = ", ".join(frameworks) if frameworks else "none"
        tag_str = ", ".join(tags) if tags else "none"

        src_lines = ""
        for i, s in enumerate(sources, 1):
            src_lines += f"{i}. {s}\n"

        integrity = "✅ valid" if checksum else "❌ TAMPERED"

        # Final formatted string
        return (
            f"\nAttribution Report\n{'='*60}\n"
            f"Record ID   : {record_id}\n"
            f"Timestamp   : {timestamp}\n"
            f"Action      : {action}\n"
            f"Actor       : {actor}\n"
            f"Confidence  : {confidence}\n"
            f"Frameworks  : {fw}\n"
            f"Tags        : {tag_str}\n"
            f"\nDecision\n{'-'*40}\n{decision}\n"
            f"\nReasoning\n{'-'*40}\n{reasoning}\n"
            f"\nSources ({len(sources)})\n{'-'*40}\n{src_lines or '  (none)'}\n"
            f"\nIntegrity   : {integrity}\n"
            f"Checksum    : {checksum}\n"
            f"{'='*60}\n"
        )

    # ── Detail View ─────────────────────────
    def on_select(event):
        sel = tree.selection()
        if not sel:
            return

        rec = record_map.get(sel[0])
        full_rec = fetch_record_by_id(rec["record_id"])
        text = format_attribution_report(full_rec)
        detail.config(state="normal")
        detail.delete("1.0", "end")
        detail.insert("end", text)
        detail.config(state="disabled")
        #status_var.set(f"Viewing: {rec.record_id[:16]}…")

    tree.bind("<<TreeviewSelect>>", on_select)

    # BUTTONS
    tk.Button(fbar, text="↺ Refresh", bg=CLR["accent"], fg="white",
              command=populate).pack(side="left", padx=10)

    def export_json():
        data = fetch_from_db()
        top = tk.Toplevel(win)
        txt = tk.Text(top)
        txt.pack(fill="both", expand=True)
        txt.insert("end", json.dumps(data, indent=2))

    tk.Button(fbar, text="Export JSON",command=export_json).pack(side="left")

    def save_report():
        os.makedirs("reports", exist_ok=True)
        path = f"reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        data = fetch_from_db()
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
        print("Saved:", path)

    tk.Button(fbar, text="Save Report", command=save_report).pack(side="left")

    def open_summary():
        s = fetch_summary()
        top = tk.Toplevel(win)
        txt = tk.Text(top)
        txt.pack(fill="both", expand=True)
        txt.insert("end", json.dumps(s, indent=2))

    tk.Button(fbar, text="Summary", command=open_summary).pack(side="left")

    populate()

    if not parent:
        win.mainloop()

    return win


if __name__ == "__main__":
    open_attribution_dashboard()