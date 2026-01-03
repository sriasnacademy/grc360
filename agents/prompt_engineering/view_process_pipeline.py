from connectors.lambda_mysql import call_lambda


def run_view_process_pipeline(intent: str, raw_text: str):
    """
    Handles:
    - show processes
    - view all processes
    - view process <process name>
    """

    try:
        process_name = extract_process_name(raw_text)

        payload = {
            "action": "select",
            "table": "processes"
        }

        # ✅ If user asked for a specific process
        if process_name:
            payload["where"] = {
                "process_name": process_name
            }

        data = call_lambda(payload)
        records = data.get("records", [])

        if not records:
            return "No matching process found."

        return format_process_response(records)

    except Exception as e:
        return f"❌ Error fetching process data: {e}"


# -------------------------------------------------
# Extract process name from user input
# -------------------------------------------------
def extract_process_name(text: str):
    """
    Examples:
    - view process Employee Onboarding
    - show process Vendor Management
    """

    text = text.lower().strip()

    keywords = [
        "view process",
        "show process",
        "display process"
    ]

    for key in keywords:
        if key in text:
            name = text.split(key)[-1].strip()
            return name.title() if name else None

    return None


# -------------------------------------------------
# Format response for AI assistant UI
# -------------------------------------------------
def format_process_response(processes):
    response = "📋 Process Details\n\n"

    for idx, p in enumerate(processes, start=1):
        response += f"{idx}. 📌 {p.get('process_name', 'N/A')}\n"

        if p.get("department"):
            response += f"   • Department: {p['department']}\n"
        if p.get("process_owner"):
            response += f"   • Owner: {p['process_owner']}\n"
        if p.get("frequency"):
            response += f"   • Frequency: {p['frequency']}\n"
        if p.get("triggers"):
            response += f"   • Triggers: {p['triggers']}\n"
        if p.get("outcomes"):
            response += f"   • Outcomes: {p['outcomes']}\n"
        if p.get("description"):
            response += f"   • Description: {p['description']}\n"

        response += "\n"

    return response.strip()
